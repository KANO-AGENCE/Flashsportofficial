"""CSV exports and ZIP pack generation for events."""
import csv
import io
import logging
import zipfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.models import Detection, Photo
from app.models.participant import Participant

logger = logging.getLogger(__name__)


def get_bib_photos(db: Session, event_id: int) -> dict[str, list[Photo]]:
    """Get all photos grouped by bib number for an event."""
    detections = (
        db.query(Detection)
        .join(Photo)
        .filter(Photo.event_id == event_id, Photo.processed == True)
        .all()
    )

    bib_photos: dict[str, list[Photo]] = {}
    seen: set[tuple[str, int]] = set()  # (bib, photo_id)

    for det in detections:
        bib = det.validated_bib or det.bib_number
        if not bib:
            continue
        key = (bib, det.photo_id)
        if key in seen:
            continue
        seen.add(key)
        bib_photos.setdefault(bib, []).append(det.photo)

    return bib_photos


def export_photos_per_bib_csv(db: Session, event_id: int) -> str:
    """Generate CSV: bib, nom, prenom, photo_filename (one line per photo)."""
    bib_photos = get_bib_photos(db, event_id)
    participants = {
        p.bib_number: p
        for p in db.query(Participant).filter(Participant.event_id == event_id).all()
    }

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Dossard", "Nom", "Prenom", "Photo"])

    for bib in sorted(bib_photos.keys(), key=lambda x: x.zfill(10)):
        p = participants.get(bib)
        nom = p.last_name or "" if p else ""
        prenom = p.first_name or "" if p else ""
        for photo in bib_photos[bib]:
            writer.writerow([bib, nom, prenom, photo.filename])

    return output.getvalue()


def export_photo_count_csv(db: Session, event_id: int) -> str:
    """Generate CSV: bib, nom, prenom, photo_count (one line per participant)."""
    bib_photos = get_bib_photos(db, event_id)
    participants = {
        p.bib_number: p
        for p in db.query(Participant).filter(Participant.event_id == event_id).all()
    }

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Dossard", "Nom", "Prenom", "Nombre_Photos"])

    for bib in sorted(bib_photos.keys(), key=lambda x: x.zfill(10)):
        p = participants.get(bib)
        nom = p.last_name or "" if p else ""
        prenom = p.first_name or "" if p else ""
        writer.writerow([bib, nom, prenom, len(bib_photos[bib])])

    return output.getvalue()


def generate_bib_pack_zip(db: Session, event_id: int, bib_number: str) -> bytes | None:
    """Generate a ZIP archive with all photos for a given bib number."""
    bib_photos = get_bib_photos(db, event_id)
    photos = bib_photos.get(bib_number)
    if not photos:
        return None

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            filepath = Path(photo.filepath)
            if filepath.exists():
                zf.write(filepath, f"pack_{bib_number}/{photo.filename}")

    return buffer.getvalue()
