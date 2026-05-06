"""
Qwen2.5-VL via Ollama local — strict bib OCR on cropped regions.
Never receives full photos. Only processes YOLO-detected person crops.
"""

import base64
import json
import logging
import re
import time

import cv2
import numpy as np
import requests

from config import settings

logger = logging.getLogger(__name__)


def _ensure_model_available() -> bool:
    """Check if the Qwen model is pulled, pull it if not."""
    try:
        resp = requests.get(f"{settings.ollama_url}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        if any(settings.qwen_model in m for m in models):
            return True

        logger.info(f"Model {settings.qwen_model} not found locally, pulling...")
        pull_resp = requests.post(
            f"{settings.ollama_url}/api/pull",
            json={"name": settings.qwen_model},
            timeout=600,
        )
        pull_resp.raise_for_status()
        logger.info(f"Model {settings.qwen_model} pulled successfully")
        return True
    except requests.ConnectionError:
        logger.error("Ollama is not running. Start it with: ollama serve")
        return False
    except Exception as e:
        logger.error(f"Failed to ensure Qwen model: {e}")
        return False


def _encode_image(image: np.ndarray, max_dim: int = 512) -> str:
    """Encode a cv2 image to base64 JPEG, resized to max_dim."""
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)))
    _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode("utf-8")


def _call_qwen(prompt: str, b64_image: str, num_predict: int = 100, timeout: int = 120) -> str | None:
    """Send a prompt + image to Qwen via Ollama. Returns raw response text.
    Long timeout by default — fiabilité > vitesse.
    """
    try:
        if not _ensure_model_available():
            return None

        resp = requests.post(
            f"{settings.ollama_url}/api/generate",
            json={
                "model": settings.qwen_model,
                "prompt": prompt,
                "images": [b64_image],
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": num_predict,
                },
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.ConnectionError:
        logger.error("Qwen: Ollama not reachable. Is 'ollama serve' running?")
        return None
    except requests.Timeout:
        logger.error(f"Qwen: timeout after {timeout}s")
        return None
    except Exception as e:
        logger.error(f"Qwen error: {e}")
        return None


def detect_rotation_qwen(image: np.ndarray) -> int:
    """
    Determine image rotation using Qwen2.5-VL.
    Sends a 384px thumbnail.
    Returns rotation in degrees clockwise: 0, 90, 180, or 270.
    """
    t_start = time.time()
    b64 = _encode_image(image, max_dim=384)

    answer = _call_qwen(
        "This is a sports race photo. Are people standing upright "
        "(head at top, feet at bottom)? If not, how many degrees clockwise "
        "should I rotate? Answer with ONLY one number: 0, 90, 180, or 270.",
        b64,
        num_predict=5,
        timeout=60,
    )

    elapsed = time.time() - t_start

    if not answer:
        logger.warning(f"Qwen rotation: no response ({elapsed:.2f}s)")
        return 0

    logger.info(f"Qwen rotation raw: '{answer}' ({elapsed:.2f}s)")

    digits = re.sub(r"[^0-9]", "", answer)
    if not digits:
        return 0

    degrees = int(digits)
    if degrees in (0, 90, 180, 270):
        return degrees

    logger.warning(f"Qwen rotation: unexpected '{answer}', defaulting to 0")
    return 0


def read_bib_from_crop(
    crop: np.ndarray,
    min_digits: int = 1,
    max_digits: int = 5,
    context_hint: str = "",
) -> tuple[str | None, float, str]:
    """
    Read bib number from a CROPPED torso region.
    Never receives full photos.

    Args:
        crop: Cropped torso image (already extracted by YOLO bbox)
        min_digits: Minimum expected digits
        max_digits: Maximum expected digits
        context_hint: Extra context for the prompt (sport type, bib color, etc.)

    Returns:
        (bib_number, confidence, raw_response)
    """
    t_start = time.time()

    if crop is None or crop.size == 0:
        return None, 0.0, ""

    b64 = _encode_image(crop, max_dim=512)

    prompt = (
        "Tu analyses un crop contenant potentiellement un dossard sportif. "
        "Lis uniquement les numeros visibles. "
        "Reponds exclusivement en JSON valide. "
        "N'invente jamais de numero. "
        "Ignore les sponsors, logos, dates et textes decoratifs. "
        f"Le numero a entre {min_digits} et {max_digits} chiffres. "
    )
    if context_hint:
        prompt += context_hint

    prompt += '\nFormat: {"bib": "1234"} ou {"bib": null} si aucun dossard lisible.'

    answer = _call_qwen(prompt, b64, num_predict=50, timeout=120)
    elapsed = time.time() - t_start

    if not answer:
        logger.info(f"Qwen OCR: no response ({elapsed:.2f}s)")
        return None, 0.0, ""

    logger.info(f"Qwen OCR raw: '{answer}' ({elapsed:.2f}s)")

    # Try JSON parse
    bib = None
    try:
        json_match = re.search(r'\{[^{}]*\}', answer)
        if json_match:
            data = json.loads(json_match.group())
            raw_bib = data.get("bib") or data.get("number") or data.get("dossard")
            if raw_bib and raw_bib != "null":
                bib = re.sub(r"[^0-9]", "", str(raw_bib))
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: extract digits from raw text
    if not bib:
        digits = re.sub(r"[^0-9]", "", answer)
        if digits:
            bib = digits

    # Validate digit count
    if bib and (len(bib) < min_digits or len(bib) > max_digits):
        logger.info(f"Qwen OCR: rejected '{bib}' (digit count {len(bib)} out of range {min_digits}-{max_digits})")
        return None, 0.0, answer

    if bib:
        logger.info(f"Qwen OCR: bib={bib} ({elapsed:.2f}s)")
        return bib, 0.85, answer
    else:
        logger.info(f"Qwen OCR: no bib found ({elapsed:.2f}s)")
        return None, 0.0, answer


def fullimage_fallback(
    image: np.ndarray,
    min_digits: int = 1,
    max_digits: int = 5,
) -> dict:
    """
    Full-image fallback when YOLO finds nothing.
    Asks Qwen to analyze the entire image.
    Returns: {"person_detected": bool, "bib_numbers": list[str], "raw": str}
    """
    t_start = time.time()
    b64 = _encode_image(image, max_dim=512)

    prompt = (
        "Analyse cette photo de course sportive.\n"
        "Reponds UNIQUEMENT en JSON valide strict.\n"
        '{"person": true/false, "bibs": ["123"]}\n'
        "- person: y a-t-il au moins un coureur visible?\n"
        "- bibs: liste des numeros de dossard lisibles (chiffres uniquement, liste vide si aucun).\n"
        "N'invente jamais de numero. Ignore sponsors et logos.\n"
        "Reponds UNIQUEMENT avec le JSON."
    )

    answer = _call_qwen(prompt, b64, num_predict=100, timeout=120)
    elapsed = time.time() - t_start

    result = {"person_detected": False, "bib_numbers": [], "raw": answer or ""}

    if not answer:
        logger.warning(f"Qwen fallback: no response ({elapsed:.2f}s)")
        return result

    logger.info(f"Qwen fallback raw: '{answer}' ({elapsed:.2f}s)")

    try:
        json_match = re.search(r'\{[^{}]*\}', answer)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(answer)

        result["person_detected"] = bool(data.get("person", False))

        raw_bibs = data.get("bibs", [])
        if isinstance(raw_bibs, list):
            for bib in raw_bibs:
                digits = re.sub(r"[^0-9]", "", str(bib))
                if digits and min_digits <= len(digits) <= max_digits:
                    result["bib_numbers"].append(digits)
        elif isinstance(raw_bibs, str):
            digits = re.sub(r"[^0-9]", "", raw_bibs)
            if digits and min_digits <= len(digits) <= max_digits:
                result["bib_numbers"].append(digits)

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Qwen fallback: failed to parse '{answer}': {e}")
        digits_found = re.findall(r'\b(\d{1,5})\b', answer)
        for d in digits_found:
            if min_digits <= len(d) <= max_digits:
                result["bib_numbers"].append(d)
        if result["bib_numbers"]:
            result["person_detected"] = True

    return result
