"""
OCR via Qwen2.5-VL local (Ollama) — lecture de dossards uniquement.
Remplace temporairement GPT-4o-mini pour la lecture de bibs.
Ne recoit que le crop du dossard, jamais la photo complete.
"""

import base64
import logging
import re
import time

import cv2
import numpy as np
import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
QWEN_MODEL = "qwen2.5vl:7b"


def _ensure_model_available() -> bool:
    """Check if the Qwen model is pulled, pull it if not."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        if any(QWEN_MODEL in m for m in models):
            return True

        logger.info(f"Model {QWEN_MODEL} not found locally, pulling...")
        pull_resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={"name": QWEN_MODEL},
            timeout=600,
        )
        pull_resp.raise_for_status()
        logger.info(f"Model {QWEN_MODEL} pulled successfully")
        return True
    except requests.ConnectionError:
        logger.error("Ollama is not running. Start it with: ollama serve")
        return False
    except Exception as e:
        logger.error(f"Failed to ensure Qwen model: {e}")
        return False


def _encode_image(image: np.ndarray) -> str:
    """Encode a cv2 image to base64 JPEG."""
    _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode("utf-8")


def read_bib_qwen(
    image: np.ndarray,
    person_bbox: tuple[int, int, int, int],
    min_digits: int = 1,
    max_digits: int = 5,
) -> tuple[str | None, float]:
    """
    Use Qwen2.5-VL local via Ollama to read the bib number.
    Sends ONLY the cropped torso region, never the full photo.

    Returns (bib_number, confidence).
    """
    t_start = time.time()

    px, py, pw, ph = person_bbox
    img_h, img_w = image.shape[:2]

    # Crop generous torso region (top 10% to bottom 65% of person)
    crop_y1 = max(0, py + int(ph * 0.10))
    crop_y2 = min(img_h, py + int(ph * 0.65))
    crop_x1 = max(0, px - int(pw * 0.05))
    crop_x2 = min(img_w, px + pw + int(pw * 0.05))

    crop = image[crop_y1:crop_y2, crop_x1:crop_x2]
    if crop.size == 0:
        logger.warning("Qwen OCR: empty crop, skipping")
        return None, 0.0

    # Resize if too large
    max_dim = 512
    h, w = crop.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        crop = cv2.resize(crop, (int(w * scale), int(h * scale)))

    b64 = _encode_image(crop)

    try:
        if not _ensure_model_available():
            logger.error("Qwen OCR: model not available, skipping")
            return None, 0.0

        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": QWEN_MODEL,
                "prompt": (
                    "Lis uniquement le numero du dossard visible. "
                    "Reponds uniquement avec les chiffres. "
                    "Aucun texte supplementaire."
                ),
                "images": [b64],
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 20,
                },
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("response", "").strip()
        elapsed = time.time() - t_start

        logger.info(f"Qwen OCR raw response: '{answer}' ({elapsed:.2f}s)")

        if not answer:
            logger.info(f"Qwen OCR: empty response ({elapsed:.2f}s)")
            return None, 0.0

        # Extract digits only
        digits = re.sub(r"[^0-9]", "", answer)
        if not digits or len(digits) < min_digits or len(digits) > max_digits:
            logger.info(f"Qwen OCR: invalid digits '{digits}' from '{answer}' ({elapsed:.2f}s)")
            return None, 0.0

        logger.info(f"Qwen OCR: bib={digits} ({elapsed:.2f}s)")
        return digits, 0.85

    except requests.ConnectionError:
        elapsed = time.time() - t_start
        logger.error(f"Qwen OCR: Ollama not reachable ({elapsed:.2f}s). Is 'ollama serve' running?")
        return None, 0.0
    except requests.Timeout:
        elapsed = time.time() - t_start
        logger.error(f"Qwen OCR: timeout after {elapsed:.2f}s")
        return None, 0.0
    except Exception as e:
        elapsed = time.time() - t_start
        logger.error(f"Qwen OCR error: {e} ({elapsed:.2f}s)")
        return None, 0.0
