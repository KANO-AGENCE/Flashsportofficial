import logging

import cv2
import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


def auto_orient(filepath: str) -> np.ndarray:
    """
    Read image and auto-rotate based on EXIF orientation tag.
    Uses Pillow's ImageOps.exif_transpose for reliable EXIF handling.
    Returns a cv2 BGR image (correctly oriented).
    """
    try:
        pil_img = Image.open(filepath)
        pil_img = ImageOps.exif_transpose(pil_img)

        # Convert PIL (RGB) -> cv2 (BGR)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        pil_img.close()
        return img

    except Exception as e:
        logger.warning(f"EXIF read failed for {filepath}, falling back to cv2: {e}")
        return cv2.imread(filepath)
