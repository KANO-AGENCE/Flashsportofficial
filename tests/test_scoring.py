import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.scoring import compute_overall_score, classify, score_to_percent


def test_perfect_score():
    score = compute_overall_score(
        detection_confidence=1.0,
        ocr_confidence=1.0,
        blur_score=500.0,
        framing_score=1.0,
    )
    assert score >= 0.95, f"Perfect inputs should give ~1.0, got {score}"


def test_zero_score():
    score = compute_overall_score(
        detection_confidence=0.0,
        ocr_confidence=0.0,
        blur_score=0.0,
        framing_score=0.0,
    )
    assert score == 0.0, f"Zero inputs should give 0.0, got {score}"


def test_mixed_score():
    score = compute_overall_score(
        detection_confidence=0.8,
        ocr_confidence=0.5,
        blur_score=200.0,
        framing_score=0.7,
    )
    assert 0.3 < score < 0.8, f"Mixed inputs should be moderate, got {score}"


def test_classify_bon():
    assert classify(0.8) == "bon"
    assert classify(0.7) == "bon"


def test_classify_incertain():
    assert classify(0.5) == "incertain"
    assert classify(0.4) == "incertain"


def test_classify_mauvais():
    assert classify(0.3) == "mauvais"
    assert classify(0.0) == "mauvais"


def test_score_to_percent():
    assert score_to_percent(0.75) == 75
    assert score_to_percent(1.0) == 100
    assert score_to_percent(0.0) == 0
