import logging
import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_module
from app.db.database import get_db, SessionLocal
from app.models.models import BibGroup, Card, Detection, Event, Photo
from app.schemas.schemas import ProcessResponse, ProcessStatus
from app.services.pipeline import process_event, process_card

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["processing"])

_tri_user = require_module("TRI")

# Track running tasks: stores tuples like ("event", event_id) or ("card", card_id)
_running: set[tuple] = set()
_running_lock = threading.Lock()


def _is_event_busy(event_id: int) -> bool:
    """Check if any processing is running for this event (global or any card)."""
    for key in _running:
        if key == ("event", event_id):
            return True
    return False


def _is_card_busy(card_id: int) -> bool:
    """Check if this specific card is being processed."""
    return ("card", card_id) in _running


def _run_processing(event_id: int):
    """Runs full event processing in a dedicated thread."""
    db = SessionLocal()
    try:
        result = process_event(event_id, db)
        logger.info(f"Event {event_id} processing complete: {result}")
    except Exception as e:
        logger.error(f"Event {event_id} processing error: {e}")
    finally:
        db.close()
        with _running_lock:
            _running.discard(("event", event_id))


def _run_card_processing(event_id: int, card_id: int):
    """Runs card-level processing in a dedicated thread."""
    db = SessionLocal()
    try:
        result = process_card(event_id, card_id, db)
        logger.info(f"Card {card_id} processing complete: {result}")
    except Exception as e:
        logger.error(f"Card {card_id} processing error: {e}")
    finally:
        db.close()
        with _running_lock:
            _running.discard(("card", card_id))


def _start_event_processing(event_id: int, db: Session) -> ProcessResponse:
    """Core logic for starting event processing (called by route and tri_overview)."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    total = db.query(Photo).filter(Photo.event_id == event_id).count()
    already = db.query(Photo).filter(
        Photo.event_id == event_id, Photo.processed == True
    ).count()
    pending = total - already

    if pending == 0:
        return ProcessResponse(
            message="All photos already processed",
            total=total,
            already_processed=already,
        )

    with _running_lock:
        if _is_event_busy(event_id):
            return ProcessResponse(
                message="Processing already running for this event",
                total=total,
                already_processed=already,
            )
        _running.add(("event", event_id))

    t = threading.Thread(target=_run_processing, args=(event_id,), daemon=True)
    t.start()

    return ProcessResponse(
        message=f"Processing started for {pending} photos",
        total=total,
        already_processed=already,
    )


@router.post("/{event_id}/process", response_model=ProcessResponse)
def trigger_processing(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    return _start_event_processing(event_id, db)


@router.post("/{event_id}/process-card/{card_id}", response_model=ProcessResponse)
def trigger_card_processing(
    event_id: int,
    card_id: int,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """Process only photos from a specific card."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    card = db.query(Card).filter(Card.id == card_id, Card.event_id == event_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    total = db.query(Photo).filter(Photo.card_id == card_id).count()
    already = db.query(Photo).filter(Photo.card_id == card_id, Photo.processed == True).count()
    pending = total - already

    if pending == 0:
        return ProcessResponse(message="All photos already processed", total=total, already_processed=already)

    with _running_lock:
        # Block if full-event processing is running
        if _is_event_busy(event_id):
            return ProcessResponse(message="Full event processing is running, wait for it to finish", total=total, already_processed=already)
        # Block if this specific card is already being processed
        if _is_card_busy(card_id):
            return ProcessResponse(message="This card is already being processed", total=total, already_processed=already)
        _running.add(("card", card_id))

    t = threading.Thread(target=_run_card_processing, args=(event_id, card_id), daemon=True)
    t.start()

    return ProcessResponse(message=f"Processing started for {pending} photos on card {card.name}", total=total, already_processed=already)


@router.post("/{event_id}/stop")
def stop_event(event_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    """Emergency stop: halts import AND processing for this event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    from app.services.stop import request_stop
    request_stop(event_id)

    # Also clear all running keys for this event
    with _running_lock:
        to_remove = [k for k in _running if k == ("event", event_id)]
        # Also clear cards belonging to this event
        card_ids = [c.id for c in db.query(Card.id).filter(Card.event_id == event_id).all()]
        to_remove += [k for k in _running if k[0] == "card" and k[1] in card_ids]
        for k in to_remove:
            _running.discard(k)

    logger.info(f"STOP requested for event {event_id}")
    return {"message": f"Stop signal sent for event {event_id}"}


@router.post("/{event_id}/reset")
def reset_processing(event_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    """Reset: delete all detections/bib groups, mark all photos as unprocessed."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Stop any running task first
    from app.services.stop import request_stop
    request_stop(event_id)

    photo_ids = [p.id for p in db.query(Photo.id).filter(Photo.event_id == event_id).all()]
    if photo_ids:
        db.query(Detection).filter(Detection.photo_id.in_(photo_ids)).delete(synchronize_session=False)
    db.query(BibGroup).filter(BibGroup.event_id == event_id).delete()
    db.query(Photo).filter(Photo.event_id == event_id).update({Photo.processed: False})
    db.commit()

    total = len(photo_ids)
    logger.info(f"RESET event {event_id}: {total} photos reset")
    return {"message": f"Reset done: {total} photos ready for reprocessing"}


@router.get("/{event_id}/process/status", response_model=ProcessStatus)
def get_processing_status(event_id: int, card_id: int | None = None, db: Session = Depends(get_db), _=Depends(_tri_user)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    q = db.query(Photo).filter(Photo.event_id == event_id)
    if card_id is not None:
        q = q.filter(Photo.card_id == card_id)

    total = q.count()
    processed = q.filter(Photo.processed == True).count()

    return ProcessStatus(total=total, processed=processed, pending=total - processed)
