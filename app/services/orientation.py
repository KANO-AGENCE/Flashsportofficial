import logging

import cv2
import numpy as np
from PIL import Image, ExifTags

logger = logging.getLogger(__name__)


def auto_orient(filepath: str) -> np.ndarray:
    """
    Read image and auto-rotate based on EXIF orientation tag.
    Cameras save landscape photos with EXIF rotation info —
    this ensures the image is always upright before processing.
    Returns a cv2 BGR image (correctly oriented).
    """
    try:
        pil_img = Image.open(filepath)

        # Apply EXIF orientation
        exif = pil_img.getexif()
        if exif:
            for tag, value in exif.items():
                if ExifTags.TAGS.get(tag) == "Orientation":
                    if value == 2:
                        pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
                    elif value == 3:
                        pil_img = pil_img.rotate(180, expand=True)
                    elif value == 4:
                        pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)
                    elif value == 5:
                        pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT).rotate(270, expand=True)
                    elif value == 6:
                        pil_img = pil_img.rotate(270, expand=True)
                    elif value == 7:
                        pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True)
                    elif value == 8:
                        pil_img = pil_img.rotate(90, expand=True)
                    logger.info(f"EXIF orientation {value} applied to {filepath}")
                    break

        # Convert PIL (RGB) -> cv2 (BGR)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        pil_img.close()
        return img

    except Exception as e:
        logger.warning(f"EXIF read failed for {filepath}, falling back to cv2: {e}")
        return cv2.imread(filepath)


def ensure_person_upright(image: np.ndarray, person_bbox: tuple[int, int, int, int], yolo_model=None) -> tuple[np.ndarray, bool]:
    """
    Check if the person bounding box suggests the image is rotated
    (person wider than tall = likely sideways).
    If so, try both 90° CW and 90° CCW, pick the one where YOLO
    detects the tallest person (= most upright).

    Returns (image, was_rotated).
    """
    _, _, pw, ph = person_bbox

    if pw <= ph * 1.3:
        return image, False

    # Person is sideways — try both rotations
    img_cw = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    img_ccw = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    if yolo_model is None:
        from app.services.detection import get_model
        yolo_model = get_model()

    def best_person_ratio(img):
        """Return height/width ratio of the biggest person. Higher = more upright."""
        results = yolo_model.predict(img, conf=0.25, verbose=False)
        best_area = 0
        best_ratio = 0
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) != 0:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                bw, bh = x2 - x1, y2 - y1
                area = bw * bh
                if area > best_area:
                    best_area = area
                    best_ratio = bh / max(bw, 1)
        return best_ratio

    ratio_cw = best_person_ratio(img_cw)
    ratio_ccw = best_person_ratio(img_ccw)

    logger.info(f"Person {pw}x{ph} sideways — CW ratio={ratio_cw:.2f}, CCW ratio={ratio_ccw:.2f}")

    if ratio_cw >= ratio_ccw:
        logger.info("Chose 90° CW rotation")
        return img_cw, True
    else:
        logger.info("Chose 90° CCW rotation")
        return img_ccw, True
