import cv2
import numpy as np
from ultralytics import YOLO

from config import settings

_model: YOLO | None = None


def get_model() -> YOLO:
    global _model
    if _model is None:
        _model = YOLO(settings.yolo_model_path)
    return _model


def detect_persons(image_path: str) -> list[dict]:
    """Detect persons in the image using YOLOv8. Returns sorted by area (biggest first)."""
    model = get_model()
    img = cv2.imread(image_path)
    if img is None:
        return []

    results = model.predict(img, conf=settings.yolo_confidence, verbose=False)

    persons = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            if cls_id != 0:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            w, h = x2 - x1, y2 - y1
            conf = float(box.conf[0])
            area = w * h
            persons.append({
                "bbox": (x1, y1, w, h),
                "confidence": conf,
                "area": area,
            })

    persons.sort(key=lambda p: p["area"], reverse=True)
    return persons


def get_foreground_person(image_path: str) -> dict | None:
    """Get the biggest (foreground) person detected."""
    persons = detect_persons(image_path)
    return persons[0] if persons else None


def extract_bib_regions(image: np.ndarray, person_bbox: tuple[int, int, int, int]) -> list[dict]:
    """
    Extract MULTIPLE candidate bib regions from a person.
    Scans overlapping horizontal bands on the torso to cover different bib positions.
    Returns list of cropped regions sorted by likelihood of containing a bib.
    """
    img_h, img_w = image.shape[:2]
    px, py, pw, ph = person_bbox

    # Focused bands: 80% of bibs are on lower-center torso
    # Manual review catches edge cases — no need for 5 bands
    bands = [
        (0.25, 0.55),  # primary: lower-center torso (most bibs)
        (0.15, 0.45),  # secondary: standard chest fallback
    ]

    regions = []
    seen_areas = set()

    for (y_start, y_end) in bands:
        bib_y1 = py + int(ph * y_start)
        bib_y2 = py + int(ph * y_end)
        bib_x1 = px + int(pw * 0.05)
        bib_x2 = px + int(pw * 0.95)

        # Clamp
        bib_x1 = max(0, bib_x1)
        bib_y1 = max(0, bib_y1)
        bib_x2 = min(img_w, bib_x2)
        bib_y2 = min(img_h, bib_y2)

        if bib_x2 <= bib_x1 or bib_y2 <= bib_y1:
            continue

        # Avoid duplicate similar regions
        area_key = (bib_x1 // 10, bib_y1 // 10, bib_x2 // 10, bib_y2 // 10)
        if area_key in seen_areas:
            continue
        seen_areas.add(area_key)

        cropped = image[bib_y1:bib_y2, bib_x1:bib_x2]
        regions.append({
            "bbox": (bib_x1, bib_y1, bib_x2 - bib_x1, bib_y2 - bib_y1),
            "cropped_image": cropped,
        })

    return regions


def looks_like_bib(crop: np.ndarray) -> float:
    """
    Heuristic score (0-1) for whether a crop looks like it contains a bib.
    Bibs typically have:
    - High contrast rectangular area
    - Dense edge content (printed numbers on contrasting background)
    """
    if crop is None or crop.size == 0:
        return 0.0

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Edge density - bibs have lots of edges from printed text
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (h * w)

    # Contrast - bibs usually have high contrast
    contrast = float(gray.std())

    # Combine: high edge density + high contrast = likely bib
    score = min(1.0, (edge_density * 3) * 0.5 + (contrast / 80) * 0.5)
    return score
