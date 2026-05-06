import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_module
from app.db.database import get_db
from app.models.models import Card, Detection, Event, Photo
from app.models.web import WebEvent
from app.schemas.schemas import CardOut, EventCreate, EventOut, EventStats, RaceConfig
from config import settings

router = APIRouter(prefix="/api/events", tags=["events"])

# All event routes require TRI module access
_tri_user = require_module("TRI")

# Fields that can be updated via RaceConfig
_RACE_CONFIG_FIELDS = [
    "blur_threshold", "yolo_confidence", "bib_min_digits", "bib_max_digits",
    "precision_mode", "sport_type", "bib_color", "bib_position", "known_bibs",
    "condition_lighting", "condition_environment", "condition_weather",
    "photos_fast_motion", "avg_runners_per_photo",
]


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
    # Single query for event-level photo counts
    photo_stats = db.query(
        func.count(Photo.id).label("total"),
        func.count(case((Photo.processed == True, 1))).label("processed"),
    ).filter(Photo.event_id == event.id).first()

    total = photo_stats.total or 0
    processed = photo_stats.processed or 0
    pending = total - processed

    stats = _compute_stats(event.id, db) if processed > 0 else None

    # Single query for ALL card stats at once
    effective_bib = func.coalesce(Detection.validated_bib, Detection.bib_number)

    card_stats_q = db.query(
        Card.id,
        func.count(Photo.id).label("photo_count"),
        func.count(case((Photo.processed == True, 1))).label("processed_count"),
    ).outerjoin(Photo, Photo.card_id == Card.id).filter(
        Card.event_id == event.id
    ).group_by(Card.id).all()

    card_stats_map = {row.id: row for row in card_stats_q}

    # Validated + bibs per card (separate query since it needs Detection join)
    card_det_stats = db.query(
        Photo.card_id,
        func.count(case((Detection.validated == True, 1))).label("validated_count"),
        func.count(func.distinct(
            case((effective_bib.isnot(None), effective_bib))
        )).label("unique_bibs"),
    ).join(Detection, Detection.photo_id == Photo.id).filter(
        Photo.event_id == event.id, Photo.card_id.isnot(None)
    ).group_by(Photo.card_id).all()

    card_det_map = {row.card_id: row for row in card_det_stats}

    cards_db = db.query(Card).filter(Card.event_id == event.id).order_by(Card.created_at).all()
    cards = []
    for c in cards_db:
        cs = card_stats_map.get(c.id)
        cd = card_det_map.get(c.id)
        count = cs.photo_count if cs else 0
        c.photo_count = count
        card_out = CardOut.model_validate(c)
        card_out.processed_count = cs.processed_count if cs else 0
        card_out.pending_count = count - card_out.processed_count
        card_out.validated_count = cd.validated_count if cd else 0
        card_out.unique_bibs = cd.unique_bibs if cd else 0
        cards.append(card_out)

    # Web event info
    web_event = db.query(WebEvent).filter(WebEvent.event_id == event.id).first()

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
        blur_threshold=event.blur_threshold or 100.0,
        yolo_confidence=event.yolo_confidence or 0.35,
        bib_min_digits=event.bib_min_digits or 1,
        bib_max_digits=event.bib_max_digits or 5,
        precision_mode=event.precision_mode if event.precision_mode is not None else True,
        sport_type=event.sport_type or "running",
        bib_color=event.bib_color or "white",
        bib_position=event.bib_position or "chest",
        known_bibs=event.known_bibs,
        condition_lighting=event.condition_lighting or "day",
        condition_environment=event.condition_environment or "outdoor",
        condition_weather=event.condition_weather or "clear",
        photos_fast_motion=event.photos_fast_motion or False,
        avg_runners_per_photo=event.avg_runners_per_photo or 2,
        web_event_id=web_event.id if web_event else None,
        slug=web_event.slug if web_event else None,
        is_published=web_event.is_published if web_event else False,
    )


def _generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name."""
    import re
    import unicodedata
    slug = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = slug.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "course"


@router.post("", response_model=EventOut)
def create_event(data: EventCreate, db: Session = Depends(get_db), _=Depends(_tri_user)):
    event = Event(name=data.name, date=data.date)
    db.add(event)
    db.flush()

    # Auto-create linked WebEvent
    slug = data.slug or _generate_slug(data.name)
    # Ensure slug is unique
    base_slug = slug
    counter = 1
    while db.query(WebEvent).filter(WebEvent.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    web_event = WebEvent(
        event_id=event.id,
        slug=slug,
        description=data.description or "",
        photo_price=data.photo_price,
        pack_price=data.pack_price,
        all_photos_price=data.all_photos_price,
    )
    db.add(web_event)
    db.commit()
    db.refresh(event)
    return _event_out(event, db)


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db), _=Depends(_tri_user)):
    events = db.query(Event).order_by(Event.created_at.desc()).all()
    return [_event_out(ev, db) for ev in events]


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_out(event, db)


@router.put("/{event_id}/config", response_model=EventOut)
def update_config(event_id: int, data: RaceConfig, db: Session = Depends(get_db), _=Depends(_tri_user)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for field in _RACE_CONFIG_FIELDS:
        value = getattr(data, field, None)
        if value is not None:
            setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return _event_out(event, db)


@router.post("/{event_id}/known-bibs")
async def import_known_bibs(
    event_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """Import a list of known bib numbers from a text/CSV file."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    # Parse: one bib per line, or comma-separated
    import re
    bibs = re.findall(r"\d+", text)
    unique_bibs = sorted(set(bibs), key=lambda x: int(x))

    event.known_bibs = "\n".join(unique_bibs)
    db.commit()

    return {"message": f"{len(unique_bibs)} dossards importes", "count": len(unique_bibs)}


@router.post("/{event_id}/sample-bib", response_model=EventOut)
async def upload_sample_bib(
    event_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
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
def delete_event(event_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Stop any running processing/import before deleting
    from app.services.stop import request_stop
    request_stop(event_id)

    upload_dir = Path(settings.upload_dir) / str(event_id)
    if upload_dir.exists():
        shutil.rmtree(upload_dir)

    thumb_dir = Path(settings.upload_dir) / "thumbnails" / str(event_id)
    if thumb_dir.exists():
        shutil.rmtree(thumb_dir)

    db.delete(event)
    db.commit()
    return {"message": "Event deleted"}
