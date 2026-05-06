import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import BibGroup, Detection, Photo, Event
from app.services.detection import detect_persons
from app.services.ocr_gpt import apply_rotation
from app.services.ocr_qwen import detect_rotation_qwen, read_bib_qwen
from app.services.orientation import auto_orient
from app.services.quality import is_blurry, is_person_cut, compute_framing_score
from app.services.scoring import classify, compute_overall_score
from config import settings

logger = logging.getLogger(__name__)

# Parallel workers: Ollama supports NUM_PARALLEL concurrent requests
WORKERS = 4


def _detect_person_from_array(img: np.ndarray) -> dict | None:
    """Run YOLO on in-memory image (avoids re-reading from disk)."""
    model = None
    try:
        from app.services.detection import get_model
        model = get_model()
    except Exception:
        return None

    results = model.predict(img, conf=settings.yolo_confidence, verbose=False)
    persons = []
    for result in results:
        for box in result.boxes:
            if int(box.cls[0]) != 0:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            w, h = x2 - x1, y2 - y1
            persons.append({
                "bbox": (x1, y1, w, h),
                "confidence": float(box.conf[0]),
                "area": w * h,
            })
    persons.sort(key=lambda p: p["area"], reverse=True)
    return persons[0] if persons else None


def _read_bib_with_fallback(
    img: np.ndarray,
    person_bbox: tuple[int, int, int, int],
    min_digits: int,
    max_digits: int,
) -> tuple[str | None, float]:
    """Read bib number: Qwen local first, PaddleOCR fallback if Qwen fails or returns None."""
    # Try Qwen local first
    bib_number, confidence = read_bib_qwen(img, person_bbox, min_digits, max_digits)
    if bib_number is not None:
        return bib_number, confidence

    # Fallback: PaddleOCR local
    try:
        from app.services.detection import extract_bib_regions
        from app.services.ocr import find_best_bib
        regions = extract_bib_regions(img, person_bbox)
        bib, ocr_conf, _ = find_best_bib(img, regions, min_digits, max_digits, person_bbox)
        if bib is not None:
            logger.info(f"PaddleOCR fallback found bib: {bib} (conf={ocr_conf:.2f})")
            return bib, ocr_conf
    except Exception as e:
        logger.warning(f"PaddleOCR fallback failed: {e}")

    return None, 0.0


def _analyze_photo(filepath: str, blur_threshold: float, bib_min: int, bib_max: int) -> dict:
    """
    Flow:
    1. Load + EXIF orient
    2. GPT detects correct rotation
    3. Rotate if needed + single disk write
    4. YOLO detect person (in-memory, no re-read)
    5. Blur check
    6. Cut check
    7. Bib read (GPT + PaddleOCR fallback)
    """
    # === STEP 1: Load image with EXIF auto-orient ===
    img = auto_orient(filepath)
    if img is None:
        return {"classification": "mauvais"}

    # === STEP 2: Skip AI rotation (EXIF orient is enough for race photos) ===
    # Save EXIF-corrected image
    cv2.imwrite(filepath, img)

    # === STEP 4: YOLO person detection (in-memory) ===
    person = _detect_person_from_array(img)
    if person is None:
        return {"classification": "mauvais", "new_width": img.shape[1], "new_height": img.shape[0]}

    # === STEP 5: Blur check ===
    blurry, blur_score = is_blurry(img, threshold=blur_threshold)

    # === STEP 6: Cut check (on upright image) ===
    if is_person_cut(img.shape, person["bbox"]):
        return {
            "classification": "coupe",
            "confidence_detection": person["confidence"],
            "bbox": person["bbox"],
            "blur_score": blur_score,
            "new_width": img.shape[1],
            "new_height": img.shape[0],
        }

    # === STEP 7: Bib read (GPT + PaddleOCR fallback) ===
    bib_number, ocr_confidence = _read_bib_with_fallback(
        img, person["bbox"], bib_min, bib_max,
    )

    framing_score = compute_framing_score(img.shape, person["bbox"])
    overall = compute_overall_score(
        person["confidence"], ocr_confidence, blur_score, framing_score
    )
    cat = classify(overall)

    if blurry and bib_number is None:
        cat = "flou"
    elif bib_number is None:
        cat = "incertain"

    return {
        "classification": cat,
        "bib_number": bib_number,
        "confidence_detection": person["confidence"],
        "confidence_ocr": ocr_confidence,
        "bbox": person["bbox"],
        "blur_score": blur_score,
        "framing_score": framing_score,
        "overall_score": overall,
        "new_width": img.shape[1],
        "new_height": img.shape[0],
    }


def _save_result(db: Session, photo_id: int, result: dict) -> None:
    """Save analysis result to DB (upsert: update existing detection if reprocessing)."""
    bbox = result.get("bbox", (0, 0, 0, 0))
    values = dict(
        bib_number=result.get("bib_number"),
        confidence_detection=round(result.get("confidence_detection", 0.0), 4),
        confidence_ocr=round(result.get("confidence_ocr", 0.0), 4),
        bbox_x=bbox[0],
        bbox_y=bbox[1],
        bbox_w=bbox[2],
        bbox_h=bbox[3],
        blur_score=round(result.get("blur_score", 0.0), 2),
        framing_score=round(result.get("framing_score", 0.0), 4),
        overall_score=round(result.get("overall_score", 0.0), 4),
        classification=result["classification"],
    )

    # Upsert: if detection exists for this photo, update it
    existing = db.query(Detection).filter(Detection.photo_id == photo_id).first()
    if existing:
        for k, v in values.items():
            setattr(existing, k, v)
        # Reset validation on reprocess
        existing.validated = False
        existing.validated_bib = None
        existing.validated_class = None
    else:
        detection = Detection(photo_id=photo_id, **values)
        db.add(detection)


def _process_photos(
    photos: list[Photo],
    event_id: int,
    db: Session,
    blur_threshold: float,
    bib_min: int,
    bib_max: int,
    should_stop_fn,
) -> dict:
    """Shared processing logic for event-level and card-level processing."""
    total = len(photos)
    processed = 0
    errors = 0

    work = [(p.id, p.filepath) for p in photos]
    batch_size = WORKERS * 2

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        for batch_start in range(0, len(work), batch_size):
            if should_stop_fn():
                logger.info(f"Processing STOPPED for event {event_id} at {processed}/{total}")
                break

            batch = work[batch_start:batch_start + batch_size]

            # Parallel analysis (pure computation, no DB access)
            futures = {}
            for photo_id, filepath in batch:
                if should_stop_fn():
                    break
                fut = executor.submit(_analyze_photo, filepath, blur_threshold, bib_min, bib_max)
                futures[fut] = photo_id

            results_map = {}
            for fut in as_completed(futures):
                photo_id = futures[fut]
                try:
                    results_map[photo_id] = fut.result()
                except Exception as e:
                    logger.exception(f"Error analyzing photo {photo_id}")
                    results_map[photo_id] = None

            # Sequential DB writes on main thread
            for photo_id, result in results_map.items():
                try:
                    if result:
                        _save_result(db, photo_id, result)
                        updates = {Photo.processed: True}
                        if result.get("new_width"):
                            updates[Photo.width] = result["new_width"]
                            updates[Photo.height] = result["new_height"]
                        db.query(Photo).filter(Photo.id == photo_id).update(updates)
                        logger.info(
                            f"Photo {photo_id}: {result['classification']} "
                            f"bib={result.get('bib_number')} "
                            f"score={result.get('overall_score', 0):.3f}"
                        )
                    else:
                        db.query(Photo).filter(Photo.id == photo_id).update({Photo.processed: True})
                    processed += 1
                except Exception as e:
                    logger.exception(f"Error saving photo {photo_id}")
                    db.rollback()
                    # Mark as processed so we don't retry forever
                    try:
                        db.query(Photo).filter(Photo.id == photo_id).update({Photo.processed: True})
                        db.commit()
                    except Exception:
                        pass
                    errors += 1

            # Commit each batch
            try:
                db.commit()
            except Exception as e:
                logger.exception(f"Batch commit failed for event {event_id}")
                db.rollback()
                errors += len(results_map)

    rebuild_bib_groups(event_id, db)
    return {"total": total, "processed": processed, "errors": errors}


def process_event(event_id: int, db: Session) -> dict:
    from app.services.stop import should_stop, clear_stop
    clear_stop(event_id)

    photos = db.query(Photo).filter(
        Photo.event_id == event_id,
        Photo.processed == False,
    ).all()

    event = db.query(Event).filter(Event.id == event_id).first()
    blur_threshold = event.blur_threshold if event else 100.0
    bib_min = event.bib_min_digits if event else 1
    bib_max = event.bib_max_digits if event else 5

    return _process_photos(
        photos, event_id, db, blur_threshold, bib_min, bib_max,
        lambda: should_stop(event_id),
    )


def process_card(event_id: int, card_id: int, db: Session) -> dict:
    """Process only unprocessed photos from a specific card."""
    from app.services.stop import should_stop_card, clear_stop_card
    clear_stop_card(card_id)

    photos = db.query(Photo).filter(
        Photo.card_id == card_id,
        Photo.processed == False,
    ).all()

    event = db.query(Event).filter(Event.id == event_id).first()
    blur_threshold = event.blur_threshold if event else 100.0
    bib_min = event.bib_min_digits if event else 1
    bib_max = event.bib_max_digits if event else 5

    return _process_photos(
        photos, event_id, db, blur_threshold, bib_min, bib_max,
        lambda: should_stop_card(event_id, card_id),
    )


def rebuild_bib_groups(event_id: int, db: Session) -> None:
    """Rebuild bib groups using SQL aggregation instead of loading all detections."""
    from sqlalchemy import func as sqlfunc

    db.query(BibGroup).filter(BibGroup.event_id == event_id).delete()

    # Use SQL aggregation: group detections by effective bib
    effective_bib = sqlfunc.coalesce(Detection.validated_bib, Detection.bib_number)

    rows = (
        db.query(
            effective_bib.label("bib"),
            sqlfunc.count(sqlfunc.distinct(Detection.photo_id)).label("photo_count"),
        )
        .join(Photo)
        .filter(
            Photo.event_id == event_id,
            effective_bib.isnot(None),
            effective_bib != "",
        )
        .group_by(effective_bib)
        .all()
    )

    # Find best photo per bib (highest overall_score)
    for row in rows:
        best_det = (
            db.query(Detection)
            .join(Photo)
            .filter(
                Photo.event_id == event_id,
                sqlfunc.coalesce(Detection.validated_bib, Detection.bib_number) == row.bib,
            )
            .order_by(Detection.overall_score.desc())
            .first()
        )

        group = BibGroup(
            event_id=event_id,
            bib_number=row.bib,
            photo_count=row.photo_count,
            best_photo_id=best_det.photo_id if best_det else None,
        )
        db.add(group)

    db.commit()
