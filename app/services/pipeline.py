import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import BibGroup, Detection, Photo, Event
from app.services.detection import get_foreground_person
from app.services.ocr_gpt import detect_rotation_gpt, apply_rotation, read_bib_gpt
from app.services.orientation import auto_orient
from app.services.quality import is_blurry, is_person_cut, compute_framing_score
from app.services.scoring import classify, compute_overall_score
from config import settings

logger = logging.getLogger(__name__)

# Number of parallel workers (GPT API calls are I/O bound, safe to parallelize)
WORKERS = 3


def _analyze_photo(filepath: str, blur_threshold: float, bib_min: int, bib_max: int) -> dict:
    """
    Flow:
    1. Load + EXIF orient
    2. GPT detects correct rotation (cheap, reliable)
    3. Rotate + save to disk
    4. YOLO detect person (on upright image)
    5. Blur check
    6. Cut check
    7. GPT bib read
    """
    # === STEP 1: Load image with EXIF auto-orient ===
    img = auto_orient(filepath)
    if img is None:
        return {"classification": "mauvais"}

    # Always save after EXIF orient so file on disk matches what we process
    cv2.imwrite(filepath, img)

    # === STEP 2: GPT detects rotation needed ===
    degrees = detect_rotation_gpt(img)

    # === STEP 3: Apply rotation + save ===
    if degrees != 0:
        img = apply_rotation(img, degrees)
        cv2.imwrite(filepath, img)
        logger.info(f"Rotated {degrees}° and saved: {filepath}")

    # === STEP 4: YOLO person detection (on upright image) ===
    person = get_foreground_person(filepath)
    if person is None:
        return {"classification": "mauvais", "new_width": img.shape[1], "new_height": img.shape[0]}

    # === STEP 5: Blur check (on upright image) ===
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

    # === STEP 7: GPT bib detection (on upright image) ===
    bib_number, ocr_confidence = read_bib_gpt(
        img, person["bbox"], min_digits=bib_min, max_digits=bib_max,
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
    """Save analysis result to DB."""
    detection = Detection(
        photo_id=photo_id,
        bib_number=result.get("bib_number"),
        confidence_detection=round(result.get("confidence_detection", 0.0), 4),
        confidence_ocr=round(result.get("confidence_ocr", 0.0), 4),
        bbox_x=result.get("bbox", (0, 0, 0, 0))[0],
        bbox_y=result.get("bbox", (0, 0, 0, 0))[1],
        bbox_w=result.get("bbox", (0, 0, 0, 0))[2],
        bbox_h=result.get("bbox", (0, 0, 0, 0))[3],
        blur_score=round(result.get("blur_score", 0.0), 2),
        framing_score=round(result.get("framing_score", 0.0), 4),
        overall_score=round(result.get("overall_score", 0.0), 4),
        classification=result["classification"],
    )
    db.add(detection)


def process_event(event_id: int, db: Session) -> dict:
    from app.services.stop import should_stop, clear_stop
    clear_stop(event_id)

    photos = db.query(Photo).filter(
        Photo.event_id == event_id,
        Photo.processed == False,
    ).all()

    # Load event config once
    event = db.query(Event).filter(Event.id == event_id).first()
    blur_threshold = event.blur_threshold if event else 100.0
    bib_min = event.bib_min_digits if event else 1
    bib_max = event.bib_max_digits if event else 5

    total = len(photos)
    processed = 0
    errors = 0

    # Build work items: (photo_id, filepath)
    work = [(p.id, p.filepath) for p in photos]

    # Process in parallel batches — analysis is thread-safe (no DB),
    # then save results on the main thread with its own session
    batch_size = WORKERS * 2
    for batch_start in range(0, len(work), batch_size):
        if should_stop(event_id):
            logger.info(f"Processing STOPPED for event {event_id} at {processed}/{total}")
            break

        batch = work[batch_start:batch_start + batch_size]

        # Parallel analysis (pure computation, no DB access)
        results_map = {}
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = {}
            for photo_id, filepath in batch:
                if should_stop(event_id):
                    break
                fut = executor.submit(_analyze_photo, filepath, blur_threshold, bib_min, bib_max)
                futures[fut] = photo_id

            for fut in as_completed(futures):
                photo_id = futures[fut]
                try:
                    results_map[photo_id] = fut.result()
                except Exception as e:
                    logger.error(f"Error analyzing photo {photo_id}: {e}")
                    results_map[photo_id] = None

        # Sequential DB writes on main thread (thread-safe)
        for photo_id, result in results_map.items():
            try:
                if result:
                    _save_result(db, photo_id, result)
                    # Update photo dimensions if image was rotated
                    updates = {Photo.processed: True}
                    if result.get("new_width"):
                        updates[Photo.width] = result["new_width"]
                        updates[Photo.height] = result["new_height"]
                    db.query(Photo).filter(Photo.id == photo_id).update(updates)
                    logger.info(f"Photo {photo_id}: {result['classification']} bib={result.get('bib_number')}")
                else:
                    db.query(Photo).filter(Photo.id == photo_id).update({Photo.processed: True})
                processed += 1
            except Exception as e:
                logger.error(f"Error saving photo {photo_id}: {e}")
                db.query(Photo).filter(Photo.id == photo_id).update({Photo.processed: True})
                errors += 1

        # Commit each batch
        db.commit()

    rebuild_bib_groups(event_id, db)
    return {"total": total, "processed": processed, "errors": errors}


def rebuild_bib_groups(event_id: int, db: Session) -> None:
    db.query(BibGroup).filter(BibGroup.event_id == event_id).delete()

    detections = (
        db.query(Detection)
        .join(Photo)
        .filter(Photo.event_id == event_id)
        .all()
    )

    groups: dict[str, list[Detection]] = {}
    for det in detections:
        bib = det.validated_bib or det.bib_number
        if not bib:
            continue
        groups.setdefault(bib, []).append(det)

    for bib_number, dets in groups.items():
        best_det = max(dets, key=lambda d: d.overall_score)
        unique_photos = set(d.photo_id for d in dets)
        group = BibGroup(
            event_id=event_id,
            bib_number=bib_number,
            photo_count=len(unique_photos),
            best_photo_id=best_det.photo_id,
        )
        db.add(group)

    db.commit()
