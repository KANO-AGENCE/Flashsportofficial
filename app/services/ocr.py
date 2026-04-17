import re
import logging

import cv2
import numpy as np
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

_ocr: PaddleOCR | None = None


def get_ocr() -> PaddleOCR:
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(lang="en")
    return _ocr


def _run_ocr(image: np.ndarray, min_digits: int, max_digits: int) -> list[dict]:
    """Single OCR pass on an image. Returns candidates."""
    if image is None or image.size == 0:
        return []

    ocr = get_ocr()
    try:
        results = ocr.predict(image)
        candidates = []
        for page in results:
            if not page:
                continue
            texts = page.get("rec_texts", [])
            scores = page.get("rec_scores", [])
            boxes = page.get("dt_polys", [])

            for i, (text, score) in enumerate(zip(texts, scores)):
                digits = re.sub(r"[^0-9]", "", text)
                if not digits or len(digits) < min_digits or len(digits) > max_digits:
                    continue

                box_area = 0
                box = (0, 0, 0, 0)
                if i < len(boxes):
                    poly = np.array(boxes[i])
                    x_min, y_min = poly.min(axis=0).astype(int)
                    x_max, y_max = poly.max(axis=0).astype(int)
                    box = (int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min))
                    box_area = box[2] * box[3]

                candidates.append({
                    "text": digits,
                    "confidence": float(score),
                    "bbox_in_crop": box,
                    "area": box_area,
                })
        return candidates
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return []


def read_all_numbers(cropped_image: np.ndarray, min_digits: int = 1, max_digits: int = 5) -> list[dict]:
    """
    Run OCR on an image. First try CLAHE-enhanced, then adaptive threshold if nothing found.
    """
    if cropped_image is None or cropped_image.size == 0:
        return []

    # Pass 1: CLAHE enhanced
    enhanced = enhance_for_ocr(cropped_image)
    candidates = _run_ocr(enhanced, min_digits, max_digits)

    # Pass 2: adaptive threshold (only if pass 1 found nothing good)
    best_conf = max((c["confidence"] for c in candidates), default=0)
    if best_conf < 0.6:
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10)
        thresh_bgr = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        extra = _run_ocr(thresh_bgr, min_digits, max_digits)

        seen = {c["text"] for c in candidates}
        for c in extra:
            if c["text"] not in seen:
                candidates.append(c)
                seen.add(c["text"])
            else:
                # Keep better confidence
                for existing in candidates:
                    if existing["text"] == c["text"] and c["confidence"] > existing["confidence"]:
                        existing["confidence"] = c["confidence"]
                        existing["bbox_in_crop"] = c["bbox_in_crop"]
                        existing["area"] = c["area"]

    return candidates


def _bbox_inside_person(bbox: tuple, person_bbox: tuple, margin: float = 0.1) -> bool:
    """Check if a detected text bbox center falls inside the person bbox (with margin)."""
    bx, by, bw, bh = bbox
    px, py, pw, ph = person_bbox
    # Center of the text
    cx = bx + bw / 2
    cy = by + bh / 2
    # Expanded person bbox
    mx = pw * margin
    my = ph * margin
    return (px - mx <= cx <= px + pw + mx) and (py - my <= cy <= py + ph + my)


def find_best_bib(
    image: np.ndarray,
    regions: list[dict],
    min_digits: int = 1,
    max_digits: int = 5,
    person_bbox: tuple[int, int, int, int] | None = None,
) -> tuple[str | None, float, tuple[int, int, int, int]]:
    """
    Try OCR on multiple candidate regions + full image fallback.
    Only considers numbers inside the person bounding box.

    Returns (bib_number, confidence, bbox_in_image).
    """
    from app.services.detection import looks_like_bib

    all_candidates = []

    # --- Pass 1: Scan torso regions (early exit on high confidence) ---
    for region in regions:
        crop = region["cropped_image"]
        rx, ry, rw, rh = region["bbox"]

        numbers = read_all_numbers(crop, min_digits, max_digits)
        bib_score = looks_like_bib(crop)

        for num in numbers:
            lx, ly, lw, lh = num["bbox_in_crop"]
            global_bbox = (rx + lx, ry + ly, lw, lh)

            size_score = min(1.0, num["area"] / max(1, rw * rh) * 5)
            digit_bonus = min(1.0, len(num["text"]) / 3)

            combined = (
                num["confidence"] * 0.3
                + size_score * 0.2
                + bib_score * 0.2
                + digit_bonus * 0.3
            )

            all_candidates.append({
                "text": num["text"],
                "ocr_confidence": num["confidence"],
                "combined_score": combined,
                "bbox": global_bbox,
                "text_area": num["area"],
                "source": "region",
            })

        # Early exit: if we found a high-confidence bib, skip remaining regions
        best_so_far = max((c["ocr_confidence"] for c in all_candidates), default=0)
        if best_so_far >= 0.75:
            break

    # --- Pass 2: Full image OCR fallback (only if regions found nothing) ---
    if not all_candidates:
        full_numbers = read_all_numbers(image, min_digits, max_digits)

        for num in full_numbers:
            lx, ly, lw, lh = num["bbox_in_crop"]

            # Filter: only keep numbers inside the person bbox
            if person_bbox and not _bbox_inside_person((lx, ly, lw, lh), person_bbox):
                continue

            digit_bonus = min(1.0, len(num["text"]) / 3)

            combined = (
                num["confidence"] * 0.4
                + digit_bonus * 0.3
                + 0.1
            )

            all_candidates.append({
                "text": num["text"],
                "ocr_confidence": num["confidence"],
                "combined_score": combined,
                "bbox": (lx, ly, lw, lh),
                "text_area": num["area"],
                "source": "full",
            })

    if not all_candidates:
        return None, 0.0, (0, 0, 0, 0)

    best = max(all_candidates, key=lambda c: c["combined_score"])
    logger.info(
        f"Bib candidates: "
        f"{[(c['text'], round(c['combined_score'], 3), c['source']) for c in sorted(all_candidates, key=lambda x: -x['combined_score'])[:5]]}"
    )
    return best["text"], best["ocr_confidence"], best["bbox"]


def enhance_for_ocr(image: np.ndarray) -> np.ndarray:
    """Enhance image for better OCR: increase contrast."""
    if image is None or image.size == 0:
        return image

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    return enhanced
