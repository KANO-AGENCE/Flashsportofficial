"""
Advanced OCR with consensus — reduces hallucinations and false bibs.

Philosophy:
- First check if a bib is actually visible (has_bib gate)
- Multi-crop: 3 torso crop variants
- Multi-read: multiple independent OCR reads per crop
- Consensus: only trust a number if reads agree
- Real confidence from Qwen (not a fixed 0.85)
- Prefer "no bib" over "wrong bib"

Activated by ADVANCED_OCR_ENABLED=true in config.
When disabled, pipeline uses the original read_bib_from_crop unchanged.
"""

import json
import logging
import re
import time
from collections import Counter

import cv2
import numpy as np

from app.services.ocr_qwen import _encode_image, _call_qwen

logger = logging.getLogger(__name__)


def _validate_bib_against_known(bib: str | None, known_bibs: set[str]) -> str | None:
    """Validate and potentially correct a bib against the known bibs list."""
    if not bib or not known_bibs:
        return bib
    if bib in known_bibs:
        return bib
    substitutions = {
        '3': '8', '8': '3', '6': '9', '9': '6',
        '0': '8', '1': '7', '7': '1',
    }
    for i, char in enumerate(bib):
        if char in substitutions:
            candidate = bib[:i] + substitutions[char] + bib[i+1:]
            if candidate in known_bibs:
                logger.info(f"[AdvOCR] Bib corrected: {bib} -> {candidate}")
                return candidate
    return bib


# ---------------------------------------------------------------------------
# Step 1: Has-bib gate
# ---------------------------------------------------------------------------

def check_has_bib(crop: np.ndarray) -> dict:
    """
    Ask Qwen: is there actually a sports bib visible in this crop?
    Returns {"has_bib": bool, "visibility": float, "reason": str}
    """
    if crop is None or crop.size == 0:
        return {"has_bib": False, "visibility": 0.0, "reason": "empty crop"}

    t_start = time.time()
    b64 = _encode_image(crop, max_dim=384)

    prompt = (
        "Look at this cropped image from a sports race photo.\n"
        "Is there a RACE BIB (dossard) with printed digits visible?\n"
        "A race bib is a paper/fabric rectangle pinned to the runner's chest or belly, "
        "with large printed race numbers.\n"
        "Do NOT confuse with: brand logos, sponsor text, shirt prints, shoe numbers, "
        "event banners, timing chips, or decorative text.\n"
        "Answer ONLY with valid JSON:\n"
        '{"has_bib": true, "visibility": 0.85, "reason": "white bib with black digits on chest"}\n'
        "or\n"
        '{"has_bib": false, "visibility": 0.1, "reason": "only brand logo visible"}\n'
        "visibility = 0.0 (nothing) to 1.0 (perfectly clear bib)."
    )

    answer = _call_qwen(prompt, b64, num_predict=80, timeout=60)
    elapsed = time.time() - t_start

    result = {"has_bib": False, "visibility": 0.0, "reason": "no response"}

    if not answer:
        logger.info(f"[AdvOCR] has_bib: no response ({elapsed:.2f}s)")
        return result

    logger.info(f"[AdvOCR] has_bib raw: '{answer}' ({elapsed:.2f}s)")

    try:
        json_match = re.search(r'\{[^{}]*\}', answer)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(answer)

        result["has_bib"] = bool(data.get("has_bib", False))
        result["visibility"] = min(1.0, max(0.0, float(data.get("visibility", 0.0))))
        result["reason"] = str(data.get("reason", ""))[:200]
    except (json.JSONDecodeError, ValueError, TypeError):
        # Fallback: check for yes/true keywords
        lower = answer.lower()
        if "true" in lower or '"has_bib": true' in lower:
            result["has_bib"] = True
            result["visibility"] = 0.6
            result["reason"] = f"parsed from: {answer[:100]}"

    return result


# ---------------------------------------------------------------------------
# Step 2: Multi-crop generation
# ---------------------------------------------------------------------------

CROP_VARIANTS = [
    ("A", 0.10, 0.65),  # Current default — wide torso
    ("B", 0.15, 0.70),  # Slightly lower (belly bibs)
    ("C", 0.20, 0.55),  # Tighter center band
]


def generate_multi_crops(
    img: np.ndarray,
    bbox: tuple[int, int, int, int],
) -> list[tuple[str, np.ndarray]]:
    """
    Generate multiple torso crop variants from a person bbox.
    Returns list of (crop_name, crop_image).
    """
    img_h, img_w = img.shape[:2]
    px, py, pw, ph = bbox
    crops = []

    for name, y_start_pct, y_end_pct in CROP_VARIANTS:
        crop_y1 = max(0, py + int(ph * y_start_pct))
        crop_y2 = min(img_h, py + int(ph * y_end_pct))
        crop_x1 = max(0, px - int(pw * 0.05))
        crop_x2 = min(img_w, px + pw + int(pw * 0.05))

        crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
        if crop.size > 0:
            crops.append((name, crop))

    return crops


# ---------------------------------------------------------------------------
# Step 3: Single OCR read with real confidence
# ---------------------------------------------------------------------------

def _read_bib_once(
    crop: np.ndarray,
    min_digits: int,
    max_digits: int,
    context_hint: str = "",
) -> dict:
    """
    Single OCR read with confidence and reason from Qwen.
    Returns {"bib": str|None, "confidence": float, "reason": str, "raw": str}
    """
    if crop is None or crop.size == 0:
        return {"bib": None, "confidence": 0.0, "reason": "empty crop", "raw": ""}

    b64 = _encode_image(crop, max_dim=512)

    prompt = (
        "Read the race bib number (dossard) in this image.\n"
        "ONLY read digits that are clearly part of a race bib number.\n"
        "Do NOT read: brand names, sponsor logos, dates, shoe numbers, event text.\n"
        "If you're not sure, say null.\n"
        f"Expected: {min_digits} to {max_digits} digits.\n"
    )
    if context_hint:
        prompt += context_hint + "\n"

    prompt += (
        "Answer ONLY with valid JSON:\n"
        '{"bib": "320", "confidence": 0.92, "reason": "clear black digits on white bib"}\n'
        "or\n"
        '{"bib": null, "confidence": 0.0, "reason": "no readable bib digits"}\n'
        "confidence = your certainty from 0.0 to 1.0."
    )

    answer = _call_qwen(prompt, b64, num_predict=80, timeout=120)

    result = {"bib": None, "confidence": 0.0, "reason": "", "raw": answer or ""}

    if not answer:
        return result

    try:
        json_match = re.search(r'\{[^{}]*\}', answer)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(answer)

        raw_bib = data.get("bib") or data.get("number") or data.get("dossard")
        if raw_bib and str(raw_bib).lower() != "null":
            bib = re.sub(r"[^0-9]", "", str(raw_bib))
            if bib and min_digits <= len(bib) <= max_digits:
                result["bib"] = bib

        result["confidence"] = min(1.0, max(0.0, float(data.get("confidence", 0.0))))
        result["reason"] = str(data.get("reason", ""))[:200]

    except (json.JSONDecodeError, ValueError, TypeError):
        # Fallback: extract digits
        digits = re.sub(r"[^0-9]", "", answer)
        if digits and min_digits <= len(digits) <= max_digits:
            result["bib"] = digits
            result["confidence"] = 0.5
            result["reason"] = f"fallback parse: {answer[:100]}"

    return result


# ---------------------------------------------------------------------------
# Step 4: Consensus logic
# ---------------------------------------------------------------------------

# Known hallucination patterns
HALLUCINATION_BIBS = {"1234", "12345", "1111", "0000", "9999", "123", "0001", "0123"}


def compute_consensus(reads: list[dict]) -> dict:
    """
    Compute consensus from multiple OCR reads.

    Returns {
        "bib": str|None,
        "confidence": float,        # real consensus confidence
        "agreement": float,          # 0.0-1.0 how much reads agree
        "reads": list[dict],         # individual reads for logging
        "reason": str,
    }
    """
    valid_bibs = []
    all_bibs = []

    for r in reads:
        bib = r.get("bib")
        all_bibs.append(bib)
        if bib and bib not in HALLUCINATION_BIBS:
            valid_bibs.append(bib)

    total_reads = len(reads)
    result = {
        "bib": None,
        "confidence": 0.0,
        "agreement": 0.0,
        "reads": reads,
        "reason": "",
    }

    if not valid_bibs:
        result["reason"] = f"no valid bibs in {total_reads} reads: {all_bibs}"
        return result

    # Count occurrences
    counter = Counter(valid_bibs)
    best_bib, best_count = counter.most_common(1)[0]

    agreement = best_count / total_reads
    result["agreement"] = round(agreement, 2)

    # Average confidence of reads that agree with consensus
    agreeing_confs = [r["confidence"] for r in reads if r.get("bib") == best_bib]
    avg_conf = sum(agreeing_confs) / len(agreeing_confs) if agreeing_confs else 0.0

    # Final confidence = agreement ratio * average Qwen confidence
    final_conf = agreement * avg_conf

    if best_count >= 2:
        # Majority agrees
        result["bib"] = best_bib
        result["confidence"] = round(final_conf, 4)
        result["reason"] = f"consensus {best_count}/{total_reads} reads agree on {best_bib}"
    elif total_reads == 1 and avg_conf >= 0.85:
        # Single read, high confidence (adaptive fast path)
        result["bib"] = best_bib
        result["confidence"] = round(avg_conf * 0.8, 4)  # Penalize single-read
        result["reason"] = f"single read high-conf: {best_bib} ({avg_conf:.2f})"
    else:
        # No consensus — prefer no bib over wrong bib
        result["bib"] = None
        result["confidence"] = 0.0
        result["reason"] = f"no consensus: {all_bibs}"

    return result


# ---------------------------------------------------------------------------
# Step 5: Main advanced OCR pipeline for one person
# ---------------------------------------------------------------------------

def advanced_ocr_person(
    img: np.ndarray,
    bbox: tuple[int, int, int, int],
    min_digits: int = 1,
    max_digits: int = 5,
    context_hint: str = "",
    known_bibs: set[str] | None = None,
) -> dict:
    """
    Full advanced OCR pipeline for one detected person.

    Returns {
        "bib_number": str|None,
        "confidence_ocr": float,
        "ocr_raw_response": str,
        "has_bib_check": dict,
        "consensus": dict,
    }
    """
    t_start = time.time()
    known_bibs = known_bibs or set()

    # --- Step 1: Generate primary crop for has_bib check ---
    crops = generate_multi_crops(img, bbox)
    if not crops:
        logger.info("[AdvOCR] No valid crops generated")
        return {
            "bib_number": None,
            "confidence_ocr": 0.0,
            "ocr_raw_response": "",
            "has_bib_check": {"has_bib": False, "visibility": 0.0, "reason": "no crop"},
            "consensus": None,
        }

    primary_crop = crops[0][1]  # Crop A

    # --- Step 2: Has-bib gate ---
    bib_check = check_has_bib(primary_crop)
    logger.info(
        f"[AdvOCR] has_bib={bib_check['has_bib']} "
        f"visibility={bib_check['visibility']:.2f} "
        f"reason='{bib_check['reason']}'"
    )

    if not bib_check["has_bib"]:
        elapsed = time.time() - t_start
        logger.info(f"[AdvOCR] Skipping OCR — no bib detected ({elapsed:.2f}s)")
        return {
            "bib_number": None,
            "confidence_ocr": 0.0,
            "ocr_raw_response": f"has_bib=false: {bib_check['reason']}",
            "has_bib_check": bib_check,
            "consensus": None,
        }

    # --- Step 3: Adaptive multi-read ---
    all_reads = []

    # First read on primary crop
    read1 = _read_bib_once(primary_crop, min_digits, max_digits, context_hint)
    all_reads.append(read1)
    logger.info(
        f"[AdvOCR] read_1: bib={read1['bib']} "
        f"conf={read1['confidence']:.2f} "
        f"reason='{read1['reason']}'"
    )

    # Adaptive: if first read is very confident, do one confirmation read only
    need_full_multi = True
    if read1["bib"] and read1["confidence"] >= 0.90:
        # High confidence — just one confirmation read on crop B
        if len(crops) >= 2:
            read2 = _read_bib_once(crops[1][1], min_digits, max_digits, context_hint)
            all_reads.append(read2)
            logger.info(
                f"[AdvOCR] read_2 (confirm): bib={read2['bib']} "
                f"conf={read2['confidence']:.2f}"
            )
            if read1["bib"] == read2["bib"]:
                # Fast consensus — both agree
                need_full_multi = False

    if need_full_multi:
        # Full multi-read: read remaining crops
        for crop_name, crop_img in crops[1:]:
            if len(all_reads) >= 3:
                break
            read = _read_bib_once(crop_img, min_digits, max_digits, context_hint)
            # Avoid duplicate appends from the adaptive path
            if len(all_reads) < 2 or crop_name != "B":
                all_reads.append(read)
            logger.info(
                f"[AdvOCR] read_{len(all_reads)} (crop_{crop_name}): "
                f"bib={read['bib']} conf={read['confidence']:.2f}"
            )

    # --- Step 4: Consensus ---
    consensus = compute_consensus(all_reads)
    bib_number = consensus["bib"]

    # --- Step 5: Validate against known bibs ---
    if bib_number and known_bibs:
        bib_number = _validate_bib_against_known(bib_number, known_bibs)

    elapsed = time.time() - t_start

    # Build raw response summary for DB storage
    raw_parts = []
    for i, r in enumerate(all_reads):
        raw_parts.append(f"r{i+1}={r['bib']}({r['confidence']:.2f})")
    raw_summary = (
        f"adv_ocr: {' '.join(raw_parts)} "
        f"consensus={consensus['bib']}({consensus['confidence']:.2f}) "
        f"agree={consensus['agreement']:.0%} "
        f"vis={bib_check['visibility']:.2f} "
        f"[{elapsed:.1f}s]"
    )

    logger.info(
        f"[AdvOCR] FINAL: bib={bib_number} "
        f"conf={consensus['confidence']:.2f} "
        f"agreement={consensus['agreement']:.0%} "
        f"reads={[r['bib'] for r in all_reads]} "
        f"({elapsed:.2f}s)"
    )

    return {
        "bib_number": bib_number,
        "confidence_ocr": consensus["confidence"],
        "ocr_raw_response": raw_summary[:200],
        "has_bib_check": bib_check,
        "consensus": consensus,
    }
