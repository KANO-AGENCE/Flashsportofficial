import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Card, Detection, Event, Photo
from app.schemas.schemas import CardOut, EventCreate, EventOut, EventStats
from config import settings

router = APIRouter(prefix="/api/events", tags=["events"])


class EventConfig(BaseModel):
    blur_threshold: float | None = None
    yolo_confidence: float | None = None
    bib_min_digits: int | None = None
    bib_max_digits: int | None = None


def _compute_stats(event_id: int, db: Session) -> EventStats:
    """Compute classification stats using SQL aggregation."""
    effective_class = func.coalesce(Detection.validated_class, Detection.classification)
    effective_bib = func.coalesce(Detection.validated_bib, Detection.bib_number)

    row = db.query(
        func.count(case((effective_class == "bon", 1))).label("bon"),
        func.count(case((effective_class == "mauvais", 1))).label("mauvais"),
        func.count(case((effective_class == "flou", 1))).label("flou"),
        func.count(case((effective_class == "coupe", 1))).label("coupe"),
        func.count(case((effective_class == "incertain", 1))).label("incertain"),
        func.count(func.distinct(effective_bib)).label("unique_bibs"),
        func.count(case((Detection.validated == True, 1))).label("validated"),
    ).join(Photo).filter(Photo.event_id == event_id).first()

    if not row:
        return EventStats()

    return EventStats(
        bon=row.bon,
        mauvais=row.mauvais,
        flou=row.flou,
        coupe=row.coupe,
        incertain=row.incertain,
        unique_bibs=row.unique_bibs,
        validated=row.validated,
    )


def _event_out(event: Event, db: Session) -> EventOut:
    total = db.query(Photo).filter(Photo.event_id == event.id).count()
    processed = db.query(Photo).filter(
        Photo.event_id == event.id, Photo.processed == True
    ).count()
    pending = total - processed

    stats = _compute_stats(event.id, db) if processed > 0 else None

    # Load cards with live photo counts
    cards_db = db.query(Card).filter(Card.event_id == event.id).order_by(Card.created_at).all()
    cards = []
    for c in cards_db:
        count = db.query(Photo).filter(Photo.card_id == c.id).count()
        c.photo_count = count
        cards.append(CardOut.model_validate(c))

    return EventOut(
        id=event.id,
        name=event.name,
        date=event.date,
        created_at=event.created_at,
        photo_count=total,
        processed_count=processed,
        pending_count=pending,
        stats=stats,
        cards=cards,
        sample_bib_path=event.sample_bib_path,
        blur_threshold=event.blur_threshold,
        yolo_confidence=event.yolo_confidence,
        bib_min_digits=event.bib_min_digits,
        bib_max_digits=event.bib_max_digits,
    )


@router.post("", response_model=EventOut)
def create_event(data: EventCreate, db: Session = Depends(get_db)):
    event = Event(name=data.name, date=data.date)
    db.add(event)
    db.commit()
    db.refresh(event)
    return _event_out(event, db)


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.created_at.desc()).all()
    return [_event_out(ev, db) for ev in events]


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_out(event, db)


@router.put("/{event_id}/config", response_model=EventOut)
def update_config(event_id: int, data: EventConfig, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if data.blur_threshold is not None:
        event.blur_threshold = data.blur_threshold
    if data.yolo_confidence is not None:
        event.yolo_confidence = data.yolo_confidence
    if data.bib_min_digits is not None:
        event.bib_min_digits = data.bib_min_digits
    if data.bib_max_digits is not None:
        event.bib_max_digits = data.bib_max_digits
    db.commit()
    db.refresh(event)
    return _event_out(event, db)


@router.post("/{event_id}/sample-bib", response_model=EventOut)
async def upload_sample_bib(
    event_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    upload_dir = Path(settings.upload_dir) / str(event_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "sample.jpg").suffix or ".jpg"
    dest = upload_dir / f"sample_bib{ext}"

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    event.sample_bib_path = str(dest)
    db.commit()
    db.refresh(event)
    return _event_out(event, db)


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Stop any running processing/import before deleting
    from app.services.stop import request_stop
    request_stop(event_id)

    upload_dir = Path(settings.upload_dir) / str(event_id)
    if upload_dir.exists():
        shutil.rmtree(upload_dir)

    db.delete(event)
    db.commit()
    return {"message": "Event deleted"}
