import base64
import logging
import re

import cv2
import numpy as np
from openai import OpenAI

from config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _encode_image(image: np.ndarray) -> str:
    """Encode a cv2 image to base64 JPEG."""
    _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode("utf-8")


def detect_rotation_gpt(image: np.ndarray) -> int:
    """
    Use GPT-4o to determine how to rotate the image so the person
    is upright (head up, feet down).
    Sends a 384px thumbnail for reliable detection.

    Returns rotation in degrees clockwise: 0, 90, 180, or 270.
    """
    if not settings.openai_api_key:
        return 0

    h, w = image.shape[:2]
    max_dim = 384
    scale = max_dim / max(h, w)
    thumb = cv2.resize(image, (int(w * scale), int(h * scale)))
    b64 = _encode_image(thumb)

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an image orientation detector. You analyze sports/race photos "
                        "and determine if the image needs rotation so that people are standing "
                        "upright with their HEAD at the TOP and FEET at the BOTTOM of the image. "
                        "You MUST reply with exactly one number: 0, 90, 180, or 270. "
                        "0 means the image is already correct. "
                        "90 means rotate 90 degrees clockwise. "
                        "180 means the image is upside down. "
                        "270 means rotate 90 degrees counter-clockwise. "
                        "Most photos are already correct (0). Only suggest rotation if "
                        "people are clearly sideways or upside down."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Look at this sports race photo. Are the people standing upright "
                                "(head at top, feet at bottom)? If not, how many degrees clockwise "
                                "should I rotate it? Answer with ONLY: 0, 90, 180, or 270"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=5,
            temperature=0,
        )

        answer = response.choices[0].message.content.strip()
        digits = re.sub(r"[^0-9]", "", answer)
        if not digits:
            logger.warning(f"GPT rotation no digits in answer: '{answer}', defaulting to 0")
            return 0
        degrees = int(digits)
        if degrees in (0, 90, 180, 270):
            logger.info(f"GPT rotation detection: {degrees}°")
            return degrees
        logger.warning(f"GPT rotation unexpected answer: '{answer}', defaulting to 0")
        return 0

    except Exception as e:
        logger.error(f"GPT rotation detection error: {e}")
        return 0


def apply_rotation(image: np.ndarray, degrees: int) -> np.ndarray:
    """Apply clockwise rotation to image."""
    if degrees == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif degrees == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    elif degrees == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image


def read_bib_gpt(
    image: np.ndarray,
    person_bbox: tuple[int, int, int, int],
    min_digits: int = 1,
    max_digits: int = 5,
) -> tuple[str | None, float]:
    """
    Use GPT-4 Vision to read the bib number on a person.
    Sends a cropped torso region to minimize tokens/cost.

    Returns (bib_number, confidence).
    """
    if not settings.openai_api_key:
        logger.warning("No OpenAI API key configured, skipping GPT OCR")
        return None, 0.0

    px, py, pw, ph = person_bbox
    img_h, img_w = image.shape[:2]

    # Crop generous torso region (top 15% to bottom 65% of person)
    crop_y1 = max(0, py + int(ph * 0.10))
    crop_y2 = min(img_h, py + int(ph * 0.65))
    crop_x1 = max(0, px - int(pw * 0.05))
    crop_x2 = min(img_w, px + pw + int(pw * 0.05))

    crop = image[crop_y1:crop_y2, crop_x1:crop_x2]
    if crop.size == 0:
        return None, 0.0

    # Resize if too large (save tokens)
    max_dim = 512
    h, w = crop.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        crop = cv2.resize(crop, (int(w * scale), int(h * scale)))

    b64 = _encode_image(crop)

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"This is a cropped photo of a runner in a sports race. "
                                f"Read the bib number (race number) on the runner's chest/torso. "
                                f"The number has between {min_digits} and {max_digits} digits. "
                                f"Reply with ONLY the number, nothing else. "
                                f"If you cannot read any bib number, reply with: NONE"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}",
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_tokens=20,
            temperature=0,
        )

        answer = response.choices[0].message.content.strip()
        logger.info(f"GPT Vision response: '{answer}'")

        if answer.upper() == "NONE" or not answer:
            return None, 0.0

        # Extract digits only
        digits = re.sub(r"[^0-9]", "", answer)
        if not digits or len(digits) < min_digits or len(digits) > max_digits:
            return None, 0.0

        # GPT-4V is very reliable when it returns a number
        return digits, 0.95

    except Exception as e:
        logger.error(f"GPT Vision OCR error: {e}")
        return None, 0.0
