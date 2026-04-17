import cv2
import numpy as np


def is_blurry(image: np.ndarray, threshold: float = 100.0) -> tuple[bool, float]:
    """
    Check if image is blurry using Laplacian variance.
    Returns (is_blurry, blur_score).
    Higher score = sharper. Below threshold = blurry.
    """
    if image is None or image.size == 0:
        return True, 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return score < threshold, score


def is_person_cut(image_shape: tuple[int, ...], person_bbox: tuple[int, int, int, int]) -> bool:
    """
    Check if person is cut off at the top (head not visible).
    A person is considered cut if the top of their bounding box
    is within 3% of the image top edge.
    """
    img_h = image_shape[0]
    _, y, _, _ = person_bbox
    margin = img_h * 0.03
    return y < margin


def compute_framing_score(
    image_shape: tuple[int, ...],
    bbox: tuple[int, int, int, int],
) -> float:
    """
    Evaluate how well the subject is framed. Score 0.0-1.0.
    """
    img_h, img_w = image_shape[:2]
    x, y, w, h = bbox

    if img_w == 0 or img_h == 0:
        return 0.0

    margin_x = img_w * 0.02
    margin_y = img_h * 0.02
    edge_penalty = 1.0

    if x < margin_x:
        edge_penalty -= 0.25
    if y < margin_y:
        edge_penalty -= 0.25
    if (x + w) > (img_w - margin_x):
        edge_penalty -= 0.25
    if (y + h) > (img_h - margin_y):
        edge_penalty -= 0.25

    edge_penalty = max(0.0, edge_penalty)

    area_ratio = (w * h) / (img_w * img_h)
    if 0.10 <= area_ratio <= 0.60:
        size_score = 1.0
    elif area_ratio < 0.05 or area_ratio > 0.85:
        size_score = 0.3
    else:
        size_score = 0.7

    return round(edge_penalty * 0.5 + size_score * 0.5, 4)
