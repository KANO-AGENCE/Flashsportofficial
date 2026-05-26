"""
Subject quality filter — "photographer's eye" before OCR.

Determines if a YOLO-detected person is a real, exploitable photo subject
or just technical noise (background, too far, too cut, too blurry).

Activated by ADVANCED_SUBJECT_FILTERING_ENABLED=true in config.
When disabled, pipeline is unchanged — all persons go to OCR.

Returns:
    photo_subject_quality_score: 0.0 (garbage) to 1.0 (perfect subject)
    is_usable_subject: bool (score >= threshold)
    penalties: dict with individual penalty breakdowns for logging
"""

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def compute_subject_quality(
    img: np.ndarray,
    bbox: tuple[int, int, int, int],
    yolo_confidence: float,
    all_persons: list[dict],
    blur_threshold: float = 100.0,
) -> dict:
    """
    Compute photo_subject_quality_score for one detected person.

    Returns {
        "score": float 0-1,
        "is_usable": bool,
        "size_score": float,
        "blur_score": float,
        "blur_raw": float,
        "cut_penalty": float,
        "center_score": float,
        "foreground_score": float,
        "yolo_score": float,
        "torso_visible": bool,
        "reason": str,
    }
    """
    img_h, img_w = img.shape[:2]
    px, py, pw, ph = bbox

    if img_w == 0 or img_h == 0 or pw == 0 or ph == 0:
        return _reject("empty image or bbox", 0.0)

    # =====================================================
    # 1. SIZE — is the person big enough to be a real subject?
    # =====================================================
    area_ratio = (pw * ph) / (img_w * img_h)

    if area_ratio >= 0.15:
        size_score = 1.0
    elif area_ratio >= 0.05:
        # Linear ramp: 5% → 0.3, 15% → 1.0
        size_score = 0.3 + (area_ratio - 0.05) / 0.10 * 0.7
    elif area_ratio >= 0.01:
        # Very small: 1% → 0.0, 5% → 0.3
        size_score = (area_ratio - 0.01) / 0.04 * 0.3
    else:
        # Tiny — silhouette, reject
        return _reject("too small (< 1% image area)", 0.0, size_score=0.0)

    # Absolute pixel size check — bbox smaller than 80px height is unusable
    if ph < 80:
        return _reject(f"too small ({ph}px height)", 0.0, size_score=0.0)

    # =====================================================
    # 2. CUT PENALTY — how much of the body is visible?
    # =====================================================
    cut_penalty = _compute_cut_penalty(img_h, img_w, px, py, pw, ph)

    # Hard reject: more than 50% cut
    if cut_penalty >= 0.50:
        return _reject(
            f"heavily cut ({cut_penalty:.0%})",
            0.0,
            size_score=size_score,
            cut_penalty=cut_penalty,
        )

    # =====================================================
    # 3. BLUR — is the person sharp enough?
    # =====================================================
    blur_raw = _measure_person_blur(img, bbox)

    if blur_raw >= blur_threshold * 2:
        blur_score = 1.0  # Very sharp
    elif blur_raw >= blur_threshold:
        blur_score = 0.5 + (blur_raw - blur_threshold) / blur_threshold * 0.5
    elif blur_raw >= blur_threshold * 0.3:
        blur_score = (blur_raw - blur_threshold * 0.3) / (blur_threshold * 0.7) * 0.5
    else:
        blur_score = 0.0

    # Hard reject: extremely blurry (less than 30% of threshold)
    if blur_raw < blur_threshold * 0.3:
        return _reject(
            f"extremely blurry (score={blur_raw:.0f}, threshold={blur_threshold:.0f})",
            0.0,
            size_score=size_score,
            cut_penalty=cut_penalty,
            blur_score=blur_score,
            blur_raw=blur_raw,
        )

    # =====================================================
    # 4. CENTER — how well positioned in the frame?
    # =====================================================
    cx = (px + pw / 2) / img_w
    cy = (py + ph / 2) / img_h
    dist = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
    center_score = max(0.0, 1.0 - dist * 1.5)

    # =====================================================
    # 5. FOREGROUND — relative to other persons in the photo
    # =====================================================
    person_area = pw * ph
    if all_persons:
        max_area = max(p["area"] for p in all_persons)
        foreground_score = person_area / max_area if max_area > 0 else 0.0
    else:
        foreground_score = 1.0

    # =====================================================
    # 6. TORSO VISIBILITY — can we even read a bib?
    # =====================================================
    torso_y1 = py + int(ph * 0.10)
    torso_y2 = py + int(ph * 0.65)
    torso_visible = torso_y1 >= 0 and torso_y2 <= img_h and torso_y1 < torso_y2
    torso_penalty = 0.0 if torso_visible else 0.15

    # =====================================================
    # 7. YOLO confidence as-is
    # =====================================================
    yolo_score = min(1.0, yolo_confidence)

    # =====================================================
    # FINAL SCORE — weighted combination
    # =====================================================
    raw_score = (
        size_score * 0.30
        + blur_score * 0.20
        + (1.0 - cut_penalty) * 0.20
        + center_score * 0.10
        + foreground_score * 0.10
        + yolo_score * 0.05
        + (1.0 - torso_penalty) * 0.05
    )

    # Clamp
    final_score = round(max(0.0, min(1.0, raw_score)), 4)

    from config import settings
    is_usable = final_score >= settings.subject_min_quality

    reason = "usable" if is_usable else f"below threshold ({final_score:.2f} < {settings.subject_min_quality})"

    return {
        "score": final_score,
        "is_usable": is_usable,
        "size_score": round(size_score, 3),
        "blur_score": round(blur_score, 3),
        "blur_raw": round(blur_raw, 1),
        "cut_penalty": round(cut_penalty, 3),
        "center_score": round(center_score, 3),
        "foreground_score": round(foreground_score, 3),
        "yolo_score": round(yolo_score, 3),
        "torso_visible": torso_visible,
        "reason": reason,
    }


def _compute_cut_penalty(
    img_h: int, img_w: int,
    px: int, py: int, pw: int, ph: int,
) -> float:
    """
    Compute how much of the person is cut off by image edges.
    Returns 0.0 (fully visible) to 1.0 (mostly cut).

    Heavily penalizes:
    - Head cut (top edge) — worst case, person unrecognizable
    - Torso cut (left/right) — can't read bib
    - Half body missing
    """
    margin_pct = 0.02  # 2% of image = "touching edge"

    penalties = []

    # Top edge (head cut) — MOST IMPORTANT
    top_margin = img_h * margin_pct
    if py < top_margin:
        # How much of the person is above the image?
        # If py is negative (shouldn't happen with YOLO but just in case)
        cut_ratio = min(1.0, (top_margin - py) / ph) if ph > 0 else 0.0
        penalties.append(cut_ratio * 0.5)  # Head cut = up to 50% penalty

    # Bottom edge (feet cut) — less important for bib reading
    bottom_margin = img_h * margin_pct
    if (py + ph) > (img_h - bottom_margin):
        cut_ratio = min(1.0, ((py + ph) - (img_h - bottom_margin)) / ph) if ph > 0 else 0.0
        penalties.append(cut_ratio * 0.15)

    # Left edge
    left_margin = img_w * margin_pct
    if px < left_margin:
        cut_ratio = min(1.0, (left_margin - px) / pw) if pw > 0 else 0.0
        penalties.append(cut_ratio * 0.30)

    # Right edge
    right_margin = img_w * margin_pct
    if (px + pw) > (img_w - right_margin):
        cut_ratio = min(1.0, ((px + pw) - (img_w - right_margin)) / pw) if pw > 0 else 0.0
        penalties.append(cut_ratio * 0.30)

    return min(1.0, sum(penalties))


def _measure_person_blur(img: np.ndarray, bbox: tuple[int, int, int, int]) -> float:
    """Laplacian variance on person bbox region."""
    img_h, img_w = img.shape[:2]
    px, py, pw, ph = bbox
    x1, y1 = max(0, px), max(0, py)
    x2, y2 = min(img_w, px + pw), min(img_h, py + ph)

    if x2 <= x1 or y2 <= y1:
        return 0.0

    region = img[y1:y2, x1:x2]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _reject(reason: str, score: float = 0.0, **extra) -> dict:
    """Build a rejection result."""
    result = {
        "score": score,
        "is_usable": False,
        "size_score": extra.get("size_score", 0.0),
        "blur_score": extra.get("blur_score", 0.0),
        "blur_raw": extra.get("blur_raw", 0.0),
        "cut_penalty": extra.get("cut_penalty", 0.0),
        "center_score": 0.0,
        "foreground_score": 0.0,
        "yolo_score": 0.0,
        "torso_visible": False,
        "reason": reason,
    }
    return result


def log_subject_quality(person_index: int, quality: dict) -> None:
    """Log subject quality assessment."""
    logger.info(
        f"[SubjectFilter] person_{person_index}: "
        f"score={quality['score']:.3f} "
        f"usable={quality['is_usable']} "
        f"size={quality['size_score']:.2f} "
        f"blur={quality['blur_score']:.2f}(raw={quality['blur_raw']:.0f}) "
        f"cut={quality['cut_penalty']:.2f} "
        f"center={quality['center_score']:.2f} "
        f"fg={quality['foreground_score']:.2f} "
        f"torso={quality['torso_visible']} "
        f"reason='{quality['reason']}'"
    )
