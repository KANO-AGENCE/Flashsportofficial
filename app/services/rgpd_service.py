"""RGPD deletion: remove participant photos from web and optionally from disk."""
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.models import Detection, Photo
from app.models.web import WebPhoto

logger = logging.getLogger(__name__)


def delete_bib_photos(
    db: Session, event_id: int, bib_number: str, delete_files: bool = True
) -> dict:
    """Delete all photos associated with a bib number from web and optionally from disk.

    Returns summary of what was deleted.
    """
    # Find all detections for this bib in this event
    detections = (
        db.query(Detection)
        .join(Photo)
        .filter(
            Photo.event_id == event_id,
            (Detection.validated_bib == bib_number) | (Detection.bib_number == bib_number),
        )
        .all()
    )

    photo_ids = list({d.photo_id for d in detections})

    # Remove from web storefront
    web_deleted = 0
    if photo_ids:
        web_deleted = (
            db.query(WebPhoto)
            .filter(WebPhoto.photo_id.in_(photo_ids))
            .delete(synchronize_session=False)
        )

    # Delete detection records for this bib
    det_deleted = 0
    for det in detections:
        if (det.validated_bib == bib_number) or (det.bib_number == bib_number):
            db.delete(det)
            det_deleted += 1

    # Delete files from disk if requested
    files_deleted = 0
    if delete_files:
        photos = db.query(Photo).filter(Photo.id.in_(photo_ids)).all()
        for photo in photos:
            # Only delete if no other detections remain for this photo
            remaining = (
                db.query(Detection)
                .filter(Detection.photo_id == photo.id)
                .count()
            )
            if remaining == 0:
                filepath = Path(photo.filepath)
                if filepath.exists():
                    filepath.unlink()
                    files_deleted += 1
                db.delete(photo)

    db.commit()

    return {
        "bib_number": bib_number,
        "web_photos_removed": web_deleted,
        "detections_removed": det_deleted,
        "files_deleted": files_deleted,
    }
