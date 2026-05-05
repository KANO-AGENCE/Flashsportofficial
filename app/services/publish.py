"""Publish validated photos from TRI to the web storefront."""
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.models import Detection, Event, Photo
from app.models.web import WebEvent, WebPhoto
from app.services.watermark import create_watermarked_thumbnail
from config import settings

logger = logging.getLogger(__name__)

THUMBNAILS_DIR = Path(settings.upload_dir) / "thumbnails"


def publish_event_to_web(event_id: int, db: Session) -> dict:
    """
    Publish all validated photos from an event to the web storefront.
    Creates watermarked thumbnails and WebPhoto entries grouped by bib.

    Bib rules (from TRI verification):
    - "x" = rejected photo -> stored as is_rejected=True
    - "123" = single bib -> one WebPhoto entry
    - "123 456" = multi-bib -> one WebPhoto entry per bib number
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise ValueError(f"Event {event_id} not found")

    # Get or create WebEvent
    web_event = db.query(WebEvent).filter(WebEvent.event_id == event_id).first()
    if not web_event:
        slug = event.name.lower().replace(" ", "-").replace("'", "")
        # Deduplicate slug
        base_slug = slug
        counter = 1
        while db.query(WebEvent).filter(WebEvent.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        web_event = WebEvent(
            event_id=event_id,
            slug=slug,
        )
        db.add(web_event)
        db.commit()
        db.refresh(web_event)

    # Clear existing web photos for re-publish
    db.query(WebPhoto).filter(WebPhoto.web_event_id == web_event.id).delete()
    db.commit()

    # Get all detections from processed photos (validated or not)
    detections = (
        db.query(Detection)
        .join(Photo)
        .filter(
            Photo.event_id == event_id,
            Photo.processed == True,
        )
        .all()
    )

    thumb_dir = THUMBNAILS_DIR / str(event_id)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    published = 0
    rejected = 0
    sort_order = 0

    for det in detections:
        photo = det.photo
        # Use validated values if available, otherwise fall back to AI
        effective_class = det.validated_class or det.classification
        effective_bib = det.validated_bib or det.bib_number

        # Rejected classifications = "x"
        if effective_class in ("mauvais", "coupe", "flou"):
            bib_raw = "x"
        else:
            bib_raw = effective_bib or "x"

        # Generate thumbnail
        thumb_name = f"{photo.id}_thumb.jpg"
        thumb_path = str(thumb_dir / thumb_name)

        create_watermarked_thumbnail(photo.filepath, thumb_path)

        # Handle multi-bib (space-separated)
        bib_numbers = bib_raw.strip().split()

        for bib in bib_numbers:
            is_rejected = bib.lower() == "x"

            web_photo = WebPhoto(
                web_event_id=web_event.id,
                photo_id=photo.id,
                bib_number=bib,
                thumbnail_path=thumb_path,
                is_rejected=is_rejected,
                sort_order=sort_order,
            )
            db.add(web_photo)

            if is_rejected:
                rejected += 1
            else:
                published += 1

        sort_order += 1

    db.commit()

    # Count unique bibs
    unique_bibs = set()
    for wp in db.query(WebPhoto).filter(
        WebPhoto.web_event_id == web_event.id,
        WebPhoto.is_rejected == False,
    ).all():
        unique_bibs.add(wp.bib_number)

    logger.info(f"Published event {event_id}: {published} photos, {len(unique_bibs)} bibs, {rejected} rejected")

    return {
        "web_event_id": web_event.id,
        "slug": web_event.slug,
        "published": published,
        "rejected": rejected,
        "unique_bibs": len(unique_bibs),
    }
