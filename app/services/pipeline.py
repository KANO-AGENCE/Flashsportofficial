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
from app.services.ocr_qwen import detect_rotation_qwen, read_bib_from_crop, fullimage_fallback
from app.services.orientation import auto_orient
from app.services.quality import is_blurry, is_person_cut, compute_framing_score
from app.services.scoring import classify, compute_overall_score
from config import settings

logger = logging.getLogger(__name__)

WORKERS = settings.ai_workers


def apply_rotation(image: np.ndarray, degrees: int) -> np.ndarray:
    """Apply clockwise rotation to image."""
    if degrees == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif degrees == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    elif degrees == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image


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


def _upright_score(persons: list[dict]) -> float:
    """
    Score how 'upright' detected persons are.
    A standing person has bbox height > width (ratio > 1).
    Returns average (h/w ratio * confidence). Higher = more upright.
    Returns -1 if no persons.
    """
    if not persons:
        return -1.0
    total = 0.0
    for p in persons:
        _, _, w, h = p["bbox"]
        if w > 0:
            ratio = h / w  # Standing person: ratio > 1.0
            total += ratio * p["confidence"]
        else:
            total += 0.0
    return total / len(persons)


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


def _compute_main_subject_score(
    img_shape: tuple[int, ...],
    bbox: tuple[int, int, int, int],
    yolo_conf: float,
    blur_score: float,
    all_persons: list[dict],
) -> float:
    """
    Score how important this person is as the photo's main subject.
    0.0 = background noise, 1.0 = clearly the main subject.
    Based on: bbox size, center proximity, sharpness, YOLO confidence.
    """
    img_h, img_w = img_shape[:2]
    px, py, pw, ph = bbox
    if img_w == 0 or img_h == 0:
        return 0.0

    # Size ratio (bigger = more important)
    area_ratio = (pw * ph) / (img_w * img_h)
    size_score = min(1.0, area_ratio / 0.3)  # 30% of image = score 1.0

    # Center proximity (center of bbox vs center of image)
    cx = (px + pw / 2) / img_w
    cy = (py + ph / 2) / img_h
    dist_from_center = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
    center_score = max(0.0, 1.0 - dist_from_center * 2)

    # Sharpness (higher blur_score = sharper)
    sharp_score = min(1.0, blur_score / 200.0)

    # Relative size (biggest person gets bonus)
    max_area = max(p["area"] for p in all_persons) if all_persons else 1
    relative_size = (pw * ph) / max_area if max_area > 0 else 0.0

    score = (
        size_score * 0.35 +
        center_score * 0.20 +
        sharp_score * 0.15 +
        yolo_conf * 0.15 +
        relative_size * 0.15
    )
    return round(min(1.0, score), 4)


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


def _process_single_person(
    img: np.ndarray,
    person: dict,
    person_index: int,
    all_persons: list[dict],
    blur_threshold: float,
    bib_min: int,
    bib_max: int,
    precision_mode: bool,
    context_hint: str,
    known_bibs: set[str],
) -> dict:
    """Process a single YOLO-detected person: OCR, blur, scoring. Returns detection dict."""
    bbox = person["bbox"]
    detection_conf = person["confidence"]

    # ============================================================
    # ADVANCED SUBJECT FILTERING — photographer's eye gate
    # ============================================================
    subject_quality = None
    is_usable_subject = True  # default: all pass (flag off)

    if settings.advanced_subject_filtering_enabled:
        from app.services.subject_filter import compute_subject_quality, log_subject_quality
        subject_quality = compute_subject_quality(
            img, bbox, detection_conf, all_persons, blur_threshold,
        )
        is_usable_subject = subject_quality["is_usable"]
        log_subject_quality(person_index, subject_quality)

        if not is_usable_subject:
            # Skip OCR entirely — not a real photo subject
            blurry, blur_score = is_blurry(img, threshold=blur_threshold, person_bbox=bbox)
            cut = is_person_cut(img.shape, bbox)
            framing_score = compute_framing_score(img.shape, bbox)

            if cut:
                cat = "coupe"
            elif blurry:
                cat = "flou"
            else:
                cat = "mauvais"

            overall = compute_overall_score(detection_conf, 0.0, blur_score, framing_score)

            return {
                "bib_number": None,
                "confidence_detection": detection_conf,
                "confidence_ocr": 0.0,
                "bbox": bbox,
                "blur_score": blur_score,
                "framing_score": framing_score,
                "overall_score": overall,
                "classification": cat,
                "fallback_used": False,
                "ocr_raw_response": f"subject_filter: {subject_quality['reason']}",
                "person_index": person_index,
                "main_subject_score": subject_quality["score"],
                "is_primary_subject": False,
                "is_usable_subject": False,
                "should_publish": False,
                "status": "background_runner",
            }

    # ============================================================
    # OCR — only reached for usable subjects
    # ============================================================
    bib_number = None
    ocr_conf = 0.0
    ocr_raw = ""

    if settings.advanced_ocr_enabled:
        # === Advanced OCR: has_bib gate + multi-crop + consensus ===
        from app.services.ocr_advanced import advanced_ocr_person
        adv = advanced_ocr_person(
            img, bbox, bib_min, bib_max, context_hint, known_bibs,
        )
        bib_number = adv["bib_number"]
        ocr_conf = adv["confidence_ocr"]
        ocr_raw = adv.get("ocr_raw_response", "")
    else:
        # === Original OCR pipeline (unchanged) ===
        crop = _crop_torso(img, bbox)

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

    # Blur check (on person region only)
    blurry, blur_score = is_blurry(img, threshold=blur_threshold, person_bbox=bbox)

    # Cut check
    cut = is_person_cut(img.shape, bbox)

    # Framing
    framing_score = compute_framing_score(img.shape, bbox)

    # Main subject score — use subject_quality if available, else legacy
    if subject_quality:
        main_subject_score = subject_quality["score"]
    else:
        main_subject_score = _compute_main_subject_score(
            img.shape, bbox, detection_conf, blur_score, all_persons
        )

    # Is this a primary subject? Top 2 by area, or >40% of max area
    max_area = max(p["area"] for p in all_persons) if all_persons else 1
    is_primary = person_index < 2 or (person["area"] / max_area > 0.4)

    # Classification per detection
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

    # Status assignment
    if bib_number:
        status = "pending"  # has bib, awaiting validation
    elif is_primary:
        status = "no_bib"  # important person, no bib read
    else:
        status = "background_runner"  # small/background, no bib

    # Should publish: primary subjects with bibs always, background runners with bibs too
    should_publish = bib_number is not None

    return {
        "bib_number": bib_number,
        "confidence_detection": detection_conf,
        "confidence_ocr": ocr_conf,
        "bbox": bbox,
        "blur_score": blur_score,
        "framing_score": framing_score,
        "overall_score": overall,
        "classification": cat,
        "fallback_used": False,
        "ocr_raw_response": ocr_raw[:200] if ocr_raw else None,
        "person_index": person_index,
        "main_subject_score": main_subject_score,
        "is_primary_subject": is_primary,
        "is_usable_subject": is_usable_subject,
        "should_publish": should_publish,
        "status": status,
    }


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
    Returns dict with 'detections' list (one per person) + image metadata.

    1. EXIF orient
    2. YOLO detect persons
    3. Rotation correction if needed
    4. Process EVERY detected person independently (OCR, blur, scoring)
    5. Fallback if no person found
    """
    t_start = time.time()

    # === STEP 1: Load + EXIF orient ===
    img = auto_orient(filepath)
    if img is None:
        return {
            "detections": [],
            "new_width": 0, "new_height": 0,
            "processing_time": time.time() - t_start,
        }

    # === STEP 2: YOLO person detection ===
    persons = _detect_persons_from_array(img, confidence=yolo_confidence)

    # === STEP 3: Check orientation using bbox aspect ratio ===
    rotated = False
    current_score = _upright_score(persons)

    if current_score < 1.0:
        logger.info(f"Upright score={current_score:.2f}, trying rotations: {filepath}")
        original = auto_orient(filepath)
        if original is not None:
            best_rotation = 0
            best_score = current_score
            best_persons = persons

            for test_deg in [90, 180, 270]:
                test_img = apply_rotation(original, test_deg)
                test_persons = _detect_persons_from_array(test_img, confidence=yolo_confidence)
                test_score = _upright_score(test_persons)
                logger.debug(f"Rotation {test_deg}°: {len(test_persons)} persons, upright={test_score:.2f}")
                if test_score > best_score:
                    best_score = test_score
                    best_rotation = test_deg
                    best_persons = test_persons

            if best_rotation != 0:
                img = apply_rotation(original, best_rotation)
                persons = best_persons
                rotated = True
                logger.info(f"Best rotation={best_rotation}° upright={best_score:.2f} ({len(persons)} persons): {filepath}")

    if rotated:
        cv2.imwrite(filepath, img)

    # === STEP 4: Process ALL detected persons independently ===
    detections = []

    if persons:
        for idx, person in enumerate(persons):
            det = _process_single_person(
                img, person, idx, persons,
                blur_threshold, bib_min, bib_max,
                precision_mode, context_hint, known_bibs,
            )
            detections.append(det)
            logger.info(
                f"Person {idx}: bib={det['bib_number']} "
                f"score={det['overall_score']:.3f} "
                f"subject={det['main_subject_score']:.3f} "
                f"primary={det['is_primary_subject']} "
                f"status={det['status']}"
            )
    else:
        # === FALLBACK: Qwen full-image analysis ===
        logger.info(f"YOLO found nothing, Qwen full-image fallback: {filepath}")
        qwen_result = fullimage_fallback(img, bib_min, bib_max)

        blurry, blur_score = is_blurry(img, threshold=blur_threshold)

        if qwen_result["person_detected"]:
            bib_number = qwen_result["bib_numbers"][0] if qwen_result["bib_numbers"] else None
            bib_number = _validate_bib_against_known(bib_number, known_bibs)
            ocr_conf = 0.70 if bib_number else 0.0
            detection_conf = 0.60

            overall = compute_overall_score(detection_conf, ocr_conf, blur_score, 0.50)

            if blurry and bib_number is None:
                cat = "flou"
            elif bib_number is None:
                cat = "incertain"
            else:
                cat = classify(overall)

            detections.append({
                "bib_number": bib_number,
                "confidence_detection": detection_conf,
                "confidence_ocr": ocr_conf,
                "bbox": (0, 0, 0, 0),
                "blur_score": blur_score,
                "framing_score": 0.50,
                "overall_score": overall,
                "classification": cat,
                "fallback_used": True,
                "ocr_raw_response": qwen_result.get("raw", "")[:200],
                "person_index": 0,
                "main_subject_score": 0.5,
                "is_primary_subject": True,
                "should_publish": bib_number is not None,
                "status": "pending" if bib_number else "no_bib",
            })
        # If Qwen finds no person either, detections stays empty

    return {
        "detections": detections,
        "new_width": img.shape[1],
        "new_height": img.shape[0],
        "processing_time": time.time() - t_start,
    }


def _save_result(db: Session, photo_id: int, result: dict) -> None:
    """Save analysis result to DB — one Detection per person detected."""
    detections_data = result.get("detections", [])

    # Clear previous detections for this photo (re-processing)
    db.query(Detection).filter(Detection.photo_id == photo_id).delete()

    for det_data in detections_data:
        bbox = det_data.get("bbox", (0, 0, 0, 0))
        detection = Detection(
            photo_id=photo_id,
            bib_number=det_data.get("bib_number"),
            confidence_detection=round(det_data.get("confidence_detection", 0.0), 4),
            confidence_ocr=round(det_data.get("confidence_ocr", 0.0), 4),
            bbox_x=bbox[0],
            bbox_y=bbox[1],
            bbox_w=bbox[2],
            bbox_h=bbox[3],
            blur_score=round(det_data.get("blur_score", 0.0), 2),
            framing_score=round(det_data.get("framing_score", 0.0), 4),
            overall_score=round(det_data.get("overall_score", 0.0), 4),
            classification=det_data.get("classification", "mauvais"),
            fallback_used=det_data.get("fallback_used", False),
            ocr_raw_response=det_data.get("ocr_raw_response"),
            # Multi-person fields
            status=det_data.get("status", "pending"),
            person_index=det_data.get("person_index", 0),
            main_subject_score=round(det_data.get("main_subject_score", 0.0), 4),
            is_primary_subject=det_data.get("is_primary_subject", True),
            is_usable_subject=det_data.get("is_usable_subject", True),
            should_publish=det_data.get("should_publish", True),
        )
        db.add(detection)


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
                        dets = result.get("detections", [])
                        bibs = [d.get("bib_number") or "?" for d in dets]
                        logger.info(
                            f"Photo {photo_id}: {len(dets)} persons, "
                            f"bibs={bibs} "
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
    from app.services.stop import should_stop_card, clear_stop, clear_stop_card
    clear_stop(event_id)      # Clear event-level flag (may be stale from delete_card)
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
    """Rebuild bib groups — only indexes detections with should_publish=True."""
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
            Detection.should_publish == True,
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
                Detection.should_publish == True,
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
