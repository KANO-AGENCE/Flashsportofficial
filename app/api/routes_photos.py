import logging
import shutil
import uuid
from pathlib import Path

import cv2
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import require_module
from app.db.database import get_db, SessionLocal
from app.models.models import BibGroup, Card, Detection, Event, Photo
from app.schemas.schemas import (
    BibGroupOut,
    CardOut,
    DetectionOut,
    PhotoOut,
    ValidationUpdate,
)
from config import settings

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp", ".cr2", ".nef", ".arw"}

router = APIRouter(prefix="/api", tags=["photos"])

_tri_user = require_module("TRI")


class FolderImport(BaseModel):
    folder_path: str
    card_name: str | None = None


class CardCreate(BaseModel):
    name: str


def _next_card_number(event_id: int, db: Session) -> int:
    """Get next sequential card number for an event."""
    max_num = db.query(func.max(Card.card_number)).filter(Card.event_id == event_id).scalar()
    return (max_num or 0) + 1


def _format_filename(event_id: int, card_number: int, photo_index: int, ext: str) -> str:
    """Generate professional filename: EVENT-CARD-PHOTO.ext"""
    return f"{event_id}-{card_number:03d}-{photo_index:06d}{ext}"


def _get_next_photo_index(event_id: int, card_id: int, db: Session) -> int:
    """Get next photo index for a card."""
    count = db.query(func.count(Photo.id)).filter(
        Photo.card_id == card_id
    ).scalar()
    return (count or 0) + 1


# --- Cards ---

@router.post("/events/{event_id}/cards", response_model=CardOut)
def create_card(event_id: int, data: CardCreate, db: Session = Depends(get_db), _=Depends(_tri_user)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    card_number = _next_card_number(event_id, db)
    card = Card(event_id=event_id, name=data.name, card_number=card_number)
    db.add(card)
    db.commit()
    db.refresh(card)
    return CardOut.model_validate(card)


@router.delete("/cards/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    event_id = card.event_id

    # Stop this card's processing and event-level too (in case it's running)
    import time as _time
    from app.services.stop import request_stop_card, clear_stop
    request_stop_card(card_id)
    _time.sleep(0.5)  # Let processing thread see the stop flag

    # Collect file paths first (lightweight query)
    filepaths = [row[0] for row in db.query(Photo.filepath).filter(Photo.card_id == card_id).all()]

    # Delete detections via subquery (no in_ limit issues)
    db.query(Detection).filter(
        Detection.photo_id.in_(
            db.query(Photo.id).filter(Photo.card_id == card_id)
        )
    ).delete(synchronize_session=False)

    # Delete photos and card
    db.query(Photo).filter(Photo.card_id == card_id).delete(synchronize_session=False)
    db.query(Card).filter(Card.id == card_id).delete(synchronize_session=False)
    db.commit()

    # Clear any stale stop flags
    clear_stop(event_id)

    # Delete files on disk AFTER db commit
    for fp in filepaths:
        try:
            Path(fp).unlink(missing_ok=True)
        except Exception:
            pass

    logger.info(f"Card {card_id} deleted: {len(filepaths)} files removed")
    return {"message": "Card deleted"}


# --- Photos upload ---

@router.post("/events/{event_id}/photos")
def upload_photos(
    event_id: int,
    files: list[UploadFile],
    card_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    """Upload photos — sync route to avoid blocking the async event loop with cv2/IO."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    upload_dir = Path(settings.upload_dir) / str(event_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Get card info for naming
    card_number = 0
    if card_id:
        card = db.query(Card).filter(Card.id == card_id).first()
        card_number = card.card_number if card else 0

    uploaded = []
    photo_index = _get_next_photo_index(event_id, card_id, db) if card_id else 1

    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            continue

        original_name = file.filename or "photo.jpg"
        ext = Path(original_name).suffix.lower() or ".jpg"

        # Professional naming
        if card_id and card_number:
            new_name = _format_filename(event_id, card_number, photo_index, ext)
            photo_index += 1
        else:
            new_name = f"{uuid.uuid4().hex}{ext}"

        dest = upload_dir / new_name

        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Read dimensions — lightweight, just header decode
        img = cv2.imread(str(dest))
        width, height = (img.shape[1], img.shape[0]) if img is not None else (None, None)

        photo = Photo(
            event_id=event_id,
            card_id=card_id,
            filename=new_name,
            original_filename=original_name,
            filepath=str(dest),
            width=width,
            height=height,
        )
        db.add(photo)
        db.flush()
        uploaded.append({"id": photo.id, "filename": photo.filename, "original": original_name})

    db.commit()

    # Update card photo count
    if card_id:
        card = db.query(Card).filter(Card.id == card_id).first()
        if card:
            card.photo_count = db.query(func.count(Photo.id)).filter(Photo.card_id == card_id).scalar()
            db.commit()

    return {"uploaded": len(uploaded), "photos": uploaded}


# --- Folder import ---

def _import_folder_task(event_id: int, card_id: int, card_number: int, folder_path: str):
    """Background task: scan folder and import all images with professional naming."""
    db = SessionLocal()
    try:
        card = db.query(Card).filter(Card.id == card_id).first()
        if card:
            card.status = "importing"
            db.commit()

        source = Path(folder_path)
        upload_dir = Path(settings.upload_dir) / str(event_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        image_files = sorted([
            f for f in source.rglob("*")
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ])

        total = len(image_files)
        logger.info(f"Importing {total} images from {folder_path} for event {event_id} card {card_id}")

        from app.services.stop import should_stop, clear_stop
        clear_stop(event_id)

        imported = 0
        for i, src_file in enumerate(image_files):
            if should_stop(event_id):
                logger.info(f"Import STOPPED for event {event_id} card {card_id} at {imported}/{total}")
                if card:
                    card = db.query(Card).filter(Card.id == card_id).first()
                    card.status = "stopped"
                    card.photo_count = imported
                    db.commit()
                return
            try:
                ext = src_file.suffix.lower()
                # Professional naming: EVENT-CARD-PHOTO.ext
                photo_index = imported + 1
                new_name = _format_filename(event_id, card_number, photo_index, ext)
                dest = upload_dir / new_name

                shutil.copy2(str(src_file), str(dest))

                img = cv2.imread(str(dest))
                width, height = (img.shape[1], img.shape[0]) if img is not None else (None, None)

                photo = Photo(
                    event_id=event_id,
                    card_id=card_id,
                    filename=new_name,
                    original_filename=src_file.name,
                    filepath=str(dest),
                    width=width,
                    height=height,
                )
                db.add(photo)
                imported += 1

                if imported % 50 == 0:
                    if card:
                        card = db.query(Card).filter(Card.id == card_id).first()
                        card.photo_count = imported
                    db.commit()
                    logger.info(f"Imported {imported}/{total} photos for card {card_id}")

            except Exception as e:
                logger.error(f"Error importing {src_file}: {e}")

        if card:
            card = db.query(Card).filter(Card.id == card_id).first()
            card.status = "done"
            card.photo_count = imported
        db.commit()
        logger.info(f"Import complete: {imported}/{total} photos for card {card_id}")
    except Exception as e:
        logger.error(f"Folder import error: {e}")
        try:
            card = db.query(Card).filter(Card.id == card_id).first()
            if card:
                card.status = "error"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/events/{event_id}/import-folder")
def import_from_folder(
    event_id: int,
    data: FolderImport,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    folder = Path(data.folder_path).resolve()
    # Block access to sensitive system paths
    blocked = ["/etc", "/var", "/usr", "/bin", "/sbin", "/root", "/proc", "/sys"]
    if any(str(folder).startswith(b) for b in blocked):
        raise HTTPException(status_code=400, detail="Chemin non autorise")
    if not folder.exists():
        raise HTTPException(status_code=400, detail=f"Dossier introuvable: {data.folder_path}")
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"Pas un dossier: {data.folder_path}")

    image_files = [
        f for f in folder.rglob("*")
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]
    count = len(image_files)

    if count == 0:
        raise HTTPException(status_code=400, detail="Aucune image trouvee dans le dossier")

    # Create card with sequential number
    card_name = data.card_name or folder.name
    card_number = _next_card_number(event_id, db)
    card = Card(
        event_id=event_id,
        name=card_name,
        card_number=card_number,
        source_path=str(folder),
        total_expected=count,
        status="pending",
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    background_tasks.add_task(_import_folder_task, event_id, card.id, card_number, data.folder_path)

    return {"message": f"Import started: {count} images", "total": count, "card_id": card.id}


# --- Photos list ---

@router.get("/events/{event_id}/photos", response_model=list[PhotoOut])
def list_photos(
    event_id: int,
    bib: str | None = None,
    classification: str | None = None,
    processed_only: bool = False,
    card_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    query = db.query(Photo).filter(Photo.event_id == event_id)

    if processed_only:
        query = query.filter(Photo.processed == True)

    if card_id is not None:
        query = query.filter(Photo.card_id == card_id)

    photos = query.order_by(Photo.id).all()

    result = []
    for photo in photos:
        detections = photo.detections

        if bib:
            detections = [d for d in detections if (d.validated_bib or d.bib_number) == bib]
            if not detections:
                continue

        if classification:
            detections = [d for d in detections if (d.validated_class or d.classification) == classification]
            if not detections:
                continue

        photo_out = PhotoOut.model_validate(photo)
        if bib or classification:
            photo_out.detections = [DetectionOut.model_validate(d) for d in detections]
        result.append(photo_out)

    return result


@router.get("/photos/{photo_id}", response_model=PhotoOut)
def get_photo(photo_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return PhotoOut.model_validate(photo)


@router.post("/photos/{photo_id}/rotate")
def rotate_photo(photo_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    """Rotate a photo 90° clockwise and save to disk."""
    from PIL import Image, ImageOps

    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    filepath = Path(photo.filepath)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    img = Image.open(str(filepath))
    img = ImageOps.exif_transpose(img)
    rotated = img.rotate(-90, expand=True)

    exif = rotated.getexif()
    if 0x0112 in exif:
        del exif[0x0112]

    save_kwargs = {"quality": 95}
    if filepath.suffix.lower() in (".jpg", ".jpeg"):
        save_kwargs["exif"] = exif.tobytes() if exif else b""
    rotated.save(str(filepath), **save_kwargs)

    photo.width = rotated.width
    photo.height = rotated.height
    db.commit()

    return {"message": "Photo rotated 90° CW", "width": photo.width, "height": photo.height}


@router.get("/events/{event_id}/bibs", response_model=list[BibGroupOut])
def list_bib_groups(event_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    groups = (
        db.query(BibGroup)
        .filter(BibGroup.event_id == event_id)
        .order_by(BibGroup.bib_number)
        .all()
    )

    result = []
    for group in groups:
        photos = (
            db.query(Photo)
            .join(Detection)
            .filter(
                Photo.event_id == event_id,
                Detection.bib_number == group.bib_number,
            )
            .distinct()
            .all()
        )
        result.append(BibGroupOut(
            id=group.id,
            bib_number=group.bib_number,
            photo_count=group.photo_count,
            best_photo_id=group.best_photo_id,
            photos=[PhotoOut.model_validate(p) for p in photos],
        ))

    return result


@router.put("/detections/{detection_id}/validate", response_model=DetectionOut)
def validate_detection(
    detection_id: int,
    data: ValidationUpdate,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    detection.validated = True
    if data.validated_bib is not None:
        detection.validated_bib = data.validated_bib
    if data.validated_class is not None:
        detection.validated_class = data.validated_class
    if data.should_publish is not None:
        detection.should_publish = data.should_publish
    if data.status is not None:
        detection.status = data.status

    db.commit()
    db.refresh(detection)

    photo = db.query(Photo).filter(Photo.id == detection.photo_id).first()
    if photo:
        from app.services.pipeline import rebuild_bib_groups
        rebuild_bib_groups(photo.event_id, db)

    # Auto-collect ground truth from validation
    try:
        from app.services.training_service import collect_ground_truth_from_detection
        collect_ground_truth_from_detection(detection, db)
        db.commit()
    except Exception as e:
        logger.debug(f"Ground truth collection skipped: {e}")

    return DetectionOut.model_validate(detection)
