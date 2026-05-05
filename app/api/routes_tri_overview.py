"""Routes for TRI overview: centralized view of all events being sorted."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.dependencies import require_module
from app.db.database import get_db
from app.models.models import Card, Detection, Event, Photo

router = APIRouter(prefix="/api/tri", tags=["tri-overview"])

_tri_user = require_module("TRI")


class CardLockUpdate(BaseModel):
    locked: bool


@router.get("/overview")
def tri_overview(db: Session = Depends(get_db), _=Depends(_tri_user)):
    """Get a centralized view of all events with detailed card/photo/detection stats."""
    events = db.query(Event).order_by(Event.date.desc()).all()
    event_ids = [ev.id for ev in events]

    if not event_ids:
        return {"global_stats": {"total_events": 0, "active_events": 0, "total_photos": 0, "total_processed": 0, "total_validated": 0, "total_bibs": 0}, "events": []}

    # Batch: photo counts per event
    photo_counts = dict(db.query(
        Photo.event_id,
        func.count(Photo.id).label("total"),
    ).filter(Photo.event_id.in_(event_ids)).group_by(Photo.event_id).all())

    processed_counts = dict(db.query(
        Photo.event_id,
        func.count(Photo.id).label("processed"),
    ).filter(Photo.event_id.in_(event_ids), Photo.processed == True).group_by(Photo.event_id).all())

    # Batch: detection stats per event
    effective_class = func.coalesce(Detection.validated_class, Detection.classification)
    effective_bib = func.coalesce(Detection.validated_bib, Detection.bib_number)

    det_stats_rows = db.query(
        Photo.event_id,
        func.count(Detection.id).label("total_detections"),
        func.count(case((effective_class == "bon", 1))).label("bon"),
        func.count(case((effective_class == "mauvais", 1))).label("mauvais"),
        func.count(case((effective_class == "flou", 1))).label("flou"),
        func.count(case((effective_class == "coupe", 1))).label("coupe"),
        func.count(case((effective_class == "incertain", 1))).label("incertain"),
        func.count(func.distinct(effective_bib)).label("unique_bibs"),
        func.count(case((Detection.validated == True, 1))).label("validated"),
    ).join(Photo).filter(Photo.event_id.in_(event_ids)).group_by(Photo.event_id).all()

    det_stats_map = {row.event_id: row for row in det_stats_rows}

    # Batch: card stats
    card_photo_stats = db.query(
        Card.id, Card.event_id, Card.name, Card.status, Card.total_expected,
        Card.source_path, Card.created_at,
        func.count(Photo.id).label("photo_count"),
        func.count(case((Photo.processed == True, 1))).label("processed"),
    ).outerjoin(Photo, Photo.card_id == Card.id).filter(
        Card.event_id.in_(event_ids)
    ).group_by(Card.id).order_by(Card.created_at).all()

    card_det_stats = db.query(
        Photo.card_id,
        func.count(case((Detection.validated == True, 1))).label("validated"),
        func.count(func.distinct(
            case((effective_bib.isnot(None), effective_bib))
        )).label("indexed_bibs"),
    ).join(Detection).filter(
        Photo.event_id.in_(event_ids), Photo.card_id.isnot(None)
    ).group_by(Photo.card_id).all()

    card_det_map = {row.card_id: row for row in card_det_stats}

    # Group cards by event
    cards_by_event = {}
    for c in card_photo_stats:
        cd = card_det_map.get(c.id)
        cards_by_event.setdefault(c.event_id, []).append({
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "locked": c.status == "locked",
            "photo_count": c.photo_count,
            "total_expected": c.total_expected,
            "processed": c.processed,
            "validated": cd.validated if cd else 0,
            "indexed_bibs": cd.indexed_bibs if cd else 0,
            "source_path": c.source_path,
            "created_at": str(c.created_at) if c.created_at else None,
        })

    result = []
    for ev in events:
        total_photos = photo_counts.get(ev.id, 0)
        processed = processed_counts.get(ev.id, 0)
        ds = det_stats_map.get(ev.id)
        total_validated = ds.validated if ds else 0
        total_detections = ds.total_detections if ds else 0

        result.append({
            "id": ev.id,
            "name": ev.name,
            "date": str(ev.date),
            "total_photos": total_photos,
            "processed": processed,
            "pending": total_photos - processed,
            "stats": {
                "bon": ds.bon if ds else 0,
                "mauvais": ds.mauvais if ds else 0,
                "flou": ds.flou if ds else 0,
                "coupe": ds.coupe if ds else 0,
                "incertain": ds.incertain if ds else 0,
                "unique_bibs": ds.unique_bibs if ds else 0,
                "validated": total_validated,
                "total_detections": total_detections,
                "validation_pct": round(total_validated / total_detections * 100, 1) if total_detections else 0,
            },
            "cards": cards_by_event.get(ev.id, []),
        })

    # Global stats
    total_events = len(result)
    total_photos_all = sum(e["total_photos"] for e in result)
    total_processed_all = sum(e["processed"] for e in result)
    total_validated_all = sum(e["stats"]["validated"] for e in result)
    total_bibs_all = sum(e["stats"]["unique_bibs"] for e in result)
    active_events = sum(1 for e in result if e["pending"] > 0 or any(c["status"] in ("importing", "pending") for c in e["cards"]))

    return {
        "global_stats": {
            "total_events": total_events,
            "active_events": active_events,
            "total_photos": total_photos_all,
            "total_processed": total_processed_all,
            "total_validated": total_validated_all,
            "total_bibs": total_bibs_all,
        },
        "events": result,
    }


@router.post("/cards/{card_id}/lock")
def lock_card(card_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    """Lock a card: mark it as not to be sorted."""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.status = "locked"
    db.commit()
    return {"message": f"Carte {card.name} verrouilee", "status": "locked"}


@router.post("/cards/{card_id}/unlock")
def unlock_card(card_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    """Unlock a card: make it available for sorting again."""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.status = "done"
    db.commit()
    return {"message": f"Carte {card.name} deverrouillee", "status": "done"}


@router.post("/events/{event_id}/process-all")
def process_all_cards(event_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    """Trigger processing for all unprocessed photos in the event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    from app.api.routes_process import _start_event_processing
    return _start_event_processing(event_id, db)


@router.post("/events/{event_id}/stop")
def stop_event_processing(event_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    """Stop processing for an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    from app.services.stop import request_stop
    request_stop(event_id)
    return {"message": f"Arret demande pour {event.name}"}
