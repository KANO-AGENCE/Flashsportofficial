import numpy as np
import cv2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.quality import compute_blur_score, compute_framing_score


def test_blur_score_sharp():
    """A high-contrast checkerboard pattern should have high blur score."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[::2, ::2] = 255
    score = compute_blur_score(img)
    assert score > 100, f"Sharp image should score > 100, got {score}"


def test_blur_score_blurry():
    """A heavily blurred image should have low blur score."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[::2, ::2] = 255
    blurred = cv2.GaussianBlur(img, (31, 31), 10)
    score = compute_blur_score(blurred)
    assert score < 100, f"Blurry image should score < 100, got {score}"


def test_blur_score_empty():
    """Empty image should return 0."""
    img = np.array([], dtype=np.uint8)
    score = compute_blur_score(img)
    assert score == 0.0


def test_framing_good():
    """Subject well centered, good size."""
    score = compute_framing_score((1000, 1000), (200, 200, 400, 500))
    assert score > 0.7, f"Good framing should score > 0.7, got {score}"


def test_framing_edge():
    """Subject touching left edge."""
    score = compute_framing_score((1000, 1000), (0, 200, 400, 500))
    assert score < 1.0, f"Edge subject should score < 1.0, got {score}"


def test_framing_too_small():
    """Very small subject."""
    score = compute_framing_score((1000, 1000), (400, 400, 30, 30))
    assert score < 0.7, f"Tiny subject should score < 0.7, got {score}"
