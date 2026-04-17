import logging
import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.models.models import BibGroup, Detection, Event, Photo
from app.schemas.schemas import ProcessResponse, ProcessStatus
from app.services.pipeline import process_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["processing"])

# Track running processing threads to avoid double-launch
_running: set[int] = set()
_running_lock = threading.Lock()


def _run_processing(event_id: int):
    """Runs in a dedicated thread — never blocks FastAPI."""
    db = SessionLocal()
    try:
        result = process_event(event_id, db)
        logger.info(f"Event {event_id} processing complete: {result}")
    except Exception as e:
        logger.error(f"Event {event_id} processing error: {e}")
    finally:
        db.close()
        with _running_lock:
            _running.discard(event_id)


@router.post("/{event_id}/process", response_model=ProcessResponse)
def trigger_processing(
    event_id: int,
    db: Session = Depends(get_db),
):
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
        if event_id in _running:
            return ProcessResponse(
                message="Processing already running",
                total=total,
                already_processed=already,
            )
        _running.add(event_id)

    t = threading.Thread(target=_run_processing, args=(event_id,), daemon=True)
    t.start()

    return ProcessResponse(
        message=f"Processing started for {pending} photos",
        total=total,
        already_processed=already,
    )


@router.post("/{event_id}/stop")
def stop_event(event_id: int, db: Session = Depends(get_db)):
    """Emergency stop: halts import AND processing for this event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    from app.services.stop import request_stop
    request_stop(event_id)
    logger.info(f"STOP requested for event {event_id}")
    return {"message": f"Stop signal sent for event {event_id}"}


@router.post("/{event_id}/reset")
def reset_processing(event_id: int, db: Session = Depends(get_db)):
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
def get_processing_status(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    total = db.query(Photo).filter(Photo.event_id == event_id).count()
    processed = db.query(Photo).filter(
        Photo.event_id == event_id, Photo.processed == True
    ).count()

    return ProcessStatus(total=total, processed=processed, pending=total - processed)
