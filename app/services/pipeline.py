"""
Pipeline hybride YOLO + Qwen2.5-VL — version production.

Flow par photo:
1. EXIF auto-orient
2. YOLO détecte personnes → bboxes
3. Si personne trouvée: crop torso → Qwen lit dossard
4. Si personne pas trouvée: Qwen vérifie rotation → re-YOLO
5. Si toujours rien: Qwen fallback image complète
6. OpenCV blur check (Laplacian)
7. Validation dossards connus
8. Scoring + classification

FIABILITÉ > VITESSE
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.models.models import BibGroup, Detection, Photo, Event
from app.services.detection import extract_bib_regions
from app.services.ocr_gpt import apply_rotation
from app.services.ocr_qwen import detect_rotation_qwen, read_bib_from_crop, fullimage_fallback
from app.services.orientation import auto_orient
from app.services.quality import is_blurry, is_person_cut, compute_framing_score
from app.services.scoring import classify, compute_overall_score
from config import settings

logger = logging.getLogger(__name__)

WORKERS = settings.ai_workers


def _detect_persons_from_array(img: np.ndarray, confidence: float = 0.35) -> list[dict]:
    """Run YOLO on in-memory image. Returns list of person detections sorted by area."""
    try:
        from app.services.detection import get_model
        model = get_model()
    except Exception as e:
        logger.error(f"YOLO model load failed: {e}")
        return []

    results = model.predict(img, conf=confidence, verbose=False)
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
    return persons


def _crop_torso(img: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    """Extract torso region from person bbox for bib OCR."""
    img_h, img_w = img.shape[:2]
    px, py, pw, ph = bbox
    # Generous torso: top 10% to bottom 65% of person
    crop_y1 = max(0, py + int(ph * 0.10))
    crop_y2 = min(img_h, py + int(ph * 0.65))
    crop_x1 = max(0, px - int(pw * 0.05))
    crop_x2 = min(img_w, px + pw + int(pw * 0.05))
    crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
    return crop if crop.size > 0 else np.array([])


def _build_context_hint(event: Event | None) -> str:
    """Build context hint for Qwen from race configuration."""
    if not event:
        return ""
    parts = []
    if event.sport_type and event.sport_type != "running":
        parts.append(f"Sport: {event.sport_type}.")
    if event.bib_color and event.bib_color != "white":
        parts.append(f"Couleur dossard: {event.bib_color}.")
    if event.bib_position == "back":
        parts.append("Le dossard peut etre dans le dos.")
    return " ".join(parts)


def _validate_bib_against_known(bib: str | None, known_bibs: set[str]) -> str | None:
    """Validate and potentially correct a bib against the known bibs list."""
    if not bib or not known_bibs:
        return bib

    # Exact match
    if bib in known_bibs:
        return bib

    # Try common OCR confusions: 3↔8, 6↔9, 0↔O, 1↔7
    substitutions = {
        '3': '8', '8': '3',
        '6': '9', '9': '6',
        '0': '8', '1': '7', '7': '1',
    }

    # Try single-character substitutions
    for i, char in enumerate(bib):
        if char in substitutions:
            candidate = bib[:i] + substitutions[char] + bib[i+1:]
            if candidate in known_bibs:
                logger.info(f"Bib corrected: {bib} → {candidate} (known bibs match)")
                return candidate

    # Not in list but keep original (could be a new participant)
    return bib


def _analyze_photo(
    filepath: str,
    blur_threshold: float,
    bib_min: int,
    bib_max: int,
    yolo_confidence: float,
    precision_mode: bool,
    context_hint: str,
    known_bibs: set[str],
) -> dict:
    """
    Hybrid pipeline — FIABILITÉ > VITESSE.

    1. EXIF orient
    2. YOLO detect persons
    3. If persons: crop → Qwen OCR on each
    4. If no person: Qwen rotation → re-YOLO → fallback
    5. OpenCV blur check
    6. Known bibs validation
    7. Scoring
    """
    t_start = time.time()

    # === STEP 1: Load + EXIF orient ===
    img = auto_orient(filepath)
    if img is None:
        return {"classification": "mauvais", "processing_time": time.time() - t_start}

    # === STEP 2: YOLO person detection ===
    persons = _detect_persons_from_array(img, confidence=yolo_confidence)

    # === STEP 3: If no person, try rotation ===
    rotated = False
    if not persons:
        logger.info(f"No person found, trying rotation: {filepath}")
        degrees = detect_rotation_qwen(img)
        if degrees != 0:
            img = apply_rotation(img, degrees)
            rotated = True
            logger.info(f"Rotated {degrees}°, re-running YOLO: {filepath}")
            persons = _detect_persons_from_array(img, confidence=yolo_confidence)

    # Save corrected image (only if rotated)
    if rotated:
        cv2.imwrite(filepath, img)

    # === STEP 4: Process detected persons OR fallback ===
    if persons:
        # Process the main (biggest) person
        main_person = persons[0]
        bbox = main_person["bbox"]
        detection_conf = main_person["confidence"]

        # Crop torso for bib OCR
        crop = _crop_torso(img, bbox)

        bib_number = None
        ocr_conf = 0.0
        ocr_raw = ""
        fallback_used = False

        if crop.size > 0:
            bib_number, ocr_conf, ocr_raw = read_bib_from_crop(
                crop, bib_min, bib_max, context_hint
            )

        # In precision mode, try secondary crop regions if first failed
        if precision_mode and bib_number is None and crop.size > 0:
            regions = extract_bib_regions(img, bbox)
            for region in regions:
                bib_number, ocr_conf, ocr_raw = read_bib_from_crop(
                    region["cropped_image"], bib_min, bib_max, context_hint
                )
                if bib_number:
                    break

        # Validate against known bibs
        bib_number = _validate_bib_against_known(bib_number, known_bibs)

        # Blur check
        blurry, blur_score = is_blurry(img, threshold=blur_threshold)

        # Cut check
        cut = is_person_cut(img.shape, bbox)

        # Framing
        framing_score = compute_framing_score(img.shape, bbox)

        # Classification
        if cut:
            cat = "coupe"
        elif blurry and bib_number is None:
            cat = "flou"
        elif bib_number is None:
            cat = "incertain"
        else:
            overall = compute_overall_score(detection_conf, ocr_conf, blur_score, framing_score)
            cat = classify(overall)

        overall = compute_overall_score(detection_conf, ocr_conf, blur_score, framing_score)

        result = {
            "classification": cat,
            "bib_number": bib_number,
            "confidence_detection": detection_conf,
            "confidence_ocr": ocr_conf,
            "bbox": bbox,
            "blur_score": blur_score,
            "framing_score": framing_score,
            "overall_score": overall,
            "fallback_used": fallback_used,
            "ocr_raw_response": ocr_raw[:200] if ocr_raw else None,
            "new_width": img.shape[1],
            "new_height": img.shape[0],
            "processing_time": time.time() - t_start,
        }

        # If multiple persons detected, add extra bibs
        extra_bibs = []
        if len(persons) > 1:
            for extra_person in persons[1:]:
                extra_crop = _crop_torso(img, extra_person["bbox"])
                if extra_crop.size > 0:
                    extra_bib, _, _ = read_bib_from_crop(
                        extra_crop, bib_min, bib_max, context_hint
                    )
                    if extra_bib:
                        extra_bib = _validate_bib_against_known(extra_bib, known_bibs)
                        if extra_bib:
                            extra_bibs.append({
                                "bib_number": extra_bib,
                                "bbox": extra_person["bbox"],
                                "confidence_detection": extra_person["confidence"],
                            })

        result["extra_detections"] = extra_bibs
        return result

    else:
        # === FALLBACK: Qwen full-image analysis ===
        logger.info(f"YOLO found nothing, Qwen full-image fallback: {filepath}")
        qwen_result = fullimage_fallback(img, bib_min, bib_max)

        fallback_used = True
        blurry, blur_score = is_blurry(img, threshold=blur_threshold)

        if not qwen_result["person_detected"]:
            return {
                "classification": "mauvais",
                "blur_score": blur_score,
                "fallback_used": True,
                "new_width": img.shape[1],
                "new_height": img.shape[0],
                "processing_time": time.time() - t_start,
            }

        # Qwen found person(s) but YOLO didn't — lower confidence
        bib_number = qwen_result["bib_numbers"][0] if qwen_result["bib_numbers"] else None
        bib_number = _validate_bib_against_known(bib_number, known_bibs)
        ocr_conf = 0.70 if bib_number else 0.0  # Lower confidence for fallback
        detection_conf = 0.60  # Lower since YOLO missed it

        overall = compute_overall_score(detection_conf, ocr_conf, blur_score, 0.50)

        if blurry and bib_number is None:
            cat = "flou"
        elif bib_number is None:
            cat = "incertain"
        else:
            cat = classify(overall)

        return {
            "classification": cat,
            "bib_number": bib_number,
            "confidence_detection": detection_conf,
            "confidence_ocr": ocr_conf,
            "bbox": (0, 0, 0, 0),
            "blur_score": blur_score,
            "framing_score": 0.50,
            "overall_score": overall,
            "fallback_used": True,
            "ocr_raw_response": qwen_result.get("raw", "")[:200],
            "new_width": img.shape[1],
            "new_height": img.shape[0],
            "processing_time": time.time() - t_start,
        }


def _save_result(db: Session, photo_id: int, result: dict) -> None:
    """Save analysis result to DB (upsert)."""
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
        fallback_used=result.get("fallback_used", False),
        ocr_raw_response=result.get("ocr_raw_response"),
    )

    # Upsert main detection
    existing = db.query(Detection).filter(Detection.photo_id == photo_id).first()
    if existing:
        for k, v in values.items():
            setattr(existing, k, v)
        existing.validated = False
        existing.validated_bib = None
        existing.validated_class = None
    else:
        detection = Detection(photo_id=photo_id, **values)
        db.add(detection)

    # Save extra detections (multiple persons)
    for extra in result.get("extra_detections", []):
        extra_bbox = extra.get("bbox", (0, 0, 0, 0))
        extra_det = Detection(
            photo_id=photo_id,
            bib_number=extra["bib_number"],
            confidence_detection=round(extra.get("confidence_detection", 0.0), 4),
            confidence_ocr=0.85,
            bbox_x=extra_bbox[0],
            bbox_y=extra_bbox[1],
            bbox_w=extra_bbox[2],
            bbox_h=extra_bbox[3],
            blur_score=round(result.get("blur_score", 0.0), 2),
            framing_score=round(result.get("framing_score", 0.0), 4),
            overall_score=round(result.get("overall_score", 0.0), 4),
            classification=result["classification"],
            fallback_used=False,
        )
        db.add(extra_det)


def _process_photos(
    photos: list[Photo],
    event_id: int,
    db: Session,
    blur_threshold: float,
    bib_min: int,
    bib_max: int,
    yolo_confidence: float,
    precision_mode: bool,
    context_hint: str,
    known_bibs: set[str],
    should_stop_fn,
) -> dict:
    """Shared processing logic for event-level and card-level processing."""
    total = len(photos)
    processed = 0
    errors = 0

    work = [(p.id, p.filepath) for p in photos]
    batch_size = max(1, WORKERS * 2)

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        for batch_start in range(0, len(work), batch_size):
            if should_stop_fn():
                logger.info(f"Processing STOPPED for event {event_id} at {processed}/{total}")
                break

            batch = work[batch_start:batch_start + batch_size]

            futures = {}
            for photo_id, filepath in batch:
                if should_stop_fn():
                    break
                fut = executor.submit(
                    _analyze_photo, filepath, blur_threshold, bib_min, bib_max,
                    yolo_confidence, precision_mode, context_hint, known_bibs,
                )
                futures[fut] = photo_id

            results_map = {}
            for fut in as_completed(futures):
                photo_id = futures[fut]
                try:
                    results_map[photo_id] = fut.result()
                except Exception as e:
                    logger.exception(f"Error analyzing photo {photo_id}")
                    results_map[photo_id] = None

            # Sequential DB writes
            for photo_id, result in results_map.items():
                try:
                    if result:
                        _save_result(db, photo_id, result)
                        updates = {
                            Photo.processed: True,
                            Photo.processing_time: result.get("processing_time"),
                        }
                        if result.get("new_width"):
                            updates[Photo.width] = result["new_width"]
                            updates[Photo.height] = result["new_height"]
                        db.query(Photo).filter(Photo.id == photo_id).update(updates)
                        logger.info(
                            f"Photo {photo_id}: {result['classification']} "
                            f"bib={result.get('bib_number')} "
                            f"score={result.get('overall_score', 0):.3f} "
                            f"fallback={'Y' if result.get('fallback_used') else 'N'} "
                            f"({result.get('processing_time', 0):.1f}s)"
                        )
                    else:
                        db.query(Photo).filter(Photo.id == photo_id).update({Photo.processed: True})
                    processed += 1
                except Exception as e:
                    logger.exception(f"Error saving photo {photo_id}")
                    db.rollback()
                    try:
                        db.query(Photo).filter(Photo.id == photo_id).update({Photo.processed: True})
                        db.commit()
                    except Exception:
                        pass
                    errors += 1

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
    yolo_confidence = event.yolo_confidence if event else 0.35
    precision_mode = event.precision_mode if event and event.precision_mode is not None else True
    context_hint = _build_context_hint(event)
    known_bibs = event.get_known_bibs_set() if event else set()

    return _process_photos(
        photos, event_id, db, blur_threshold, bib_min, bib_max,
        yolo_confidence, precision_mode, context_hint, known_bibs,
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
    yolo_confidence = event.yolo_confidence if event else 0.35
    precision_mode = event.precision_mode if event and event.precision_mode is not None else True
    context_hint = _build_context_hint(event)
    known_bibs = event.get_known_bibs_set() if event else set()

    return _process_photos(
        photos, event_id, db, blur_threshold, bib_min, bib_max,
        yolo_confidence, precision_mode, context_hint, known_bibs,
        lambda: should_stop_card(event_id, card_id),
    )


def rebuild_bib_groups(event_id: int, db: Session) -> None:
    """Rebuild bib groups using SQL aggregation."""
    from sqlalchemy import func as sqlfunc

    db.query(BibGroup).filter(BibGroup.event_id == event_id).delete()

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
