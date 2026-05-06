"""
Vision IA locale via Qwen2.5-VL (Ollama).
Modele unique pour toute l'analyse : rotation, detection de personnes,
lecture de dossards. Remplace YOLO + GPT-4o.
"""

import base64
import json
import logging
import os
import re
import time

import cv2
import numpy as np
import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
# Use 3b for Mac mini, 7b for servers with more RAM/GPU
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen2.5vl:3b")


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


def _encode_image(image: np.ndarray, max_dim: int = 512) -> str:
    """Encode a cv2 image to base64 JPEG, resized to max_dim."""
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)))
    _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode("utf-8")


def _call_qwen(prompt: str, b64_image: str, num_predict: int = 100, timeout: int = 60) -> str | None:
    """Send a prompt + image to Qwen via Ollama. Returns raw response text."""
    try:
        if not _ensure_model_available():
            return None

        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": QWEN_MODEL,
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
        logger.error("Qwen: timeout")
        return None
    except Exception as e:
        logger.error(f"Qwen error: {e}")
        return None


def detect_rotation_qwen(image: np.ndarray) -> int:
    """
    Use Qwen2.5-VL to determine image rotation.
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
        timeout=30,
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


def analyze_photo_qwen(
    image: np.ndarray,
    min_digits: int = 1,
    max_digits: int = 5,
) -> dict:
    """
    Single Qwen call to analyze a sports photo.
    Returns dict with:
      - person_detected: bool
      - bib_numbers: list[str]
      - blurry: bool
    """
    t_start = time.time()
    b64 = _encode_image(image, max_dim=512)

    prompt = (
        "Analyse cette photo de course sportive. Reponds UNIQUEMENT en JSON strict, rien d'autre.\n"
        "Format exact:\n"
        '{"person": true/false, "bibs": ["123", "456"], "blurry": true/false}\n\n'
        "- person: y a-t-il au moins une personne/coureur visible?\n"
        "- bibs: liste des numeros de dossard lisibles (chiffres uniquement). Liste vide si aucun dossard visible.\n"
        "- blurry: l'image est-elle floue?\n"
        "Reponds UNIQUEMENT avec le JSON, sans explication."
    )

    answer = _call_qwen(prompt, b64, num_predict=100, timeout=60)
    elapsed = time.time() - t_start

    result = {"person_detected": False, "bib_numbers": [], "blurry": False}

    if not answer:
        logger.warning(f"Qwen analyze: no response ({elapsed:.2f}s)")
        return result

    logger.info(f"Qwen analyze raw: '{answer}' ({elapsed:.2f}s)")

    # Try to parse JSON from response
    try:
        # Extract JSON from response (might have extra text around it)
        json_match = re.search(r'\{[^{}]*\}', answer)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(answer)

        result["person_detected"] = bool(data.get("person", False))
        result["blurry"] = bool(data.get("blurry", False))

        # Parse bib numbers
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
        logger.warning(f"Qwen analyze: failed to parse JSON '{answer}': {e} ({elapsed:.2f}s)")
        # Fallback: try to extract bib numbers from raw text
        digits_found = re.findall(r'\b(\d{1,5})\b', answer)
        for d in digits_found:
            if min_digits <= len(d) <= max_digits:
                result["bib_numbers"].append(d)
        # If we got bibs, there's probably a person
        if result["bib_numbers"]:
            result["person_detected"] = True

    logger.info(
        f"Qwen analyze result: person={result['person_detected']} "
        f"bibs={result['bib_numbers']} blurry={result['blurry']} ({elapsed:.2f}s)"
    )
    return result
