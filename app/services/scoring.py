from config import settings


def compute_overall_score(
    detection_confidence: float,
    ocr_confidence: float,
    blur_score: float,
    framing_score: float,
) -> float:
    """
    Weighted composite score 0.0-1.0.
    Weights: detection 20%, OCR 30%, blur 30%, framing 20%.
    """
    # Normalize blur to 0-1
    threshold = settings.quality_blur_threshold
    good = settings.quality_blur_good

    if blur_score >= good:
        blur_norm = 1.0
    elif blur_score <= threshold:
        blur_norm = 0.0
    else:
        blur_norm = (blur_score - threshold) / (good - threshold)

    score = (
        0.20 * detection_confidence
        + 0.30 * ocr_confidence
        + 0.30 * blur_norm
        + 0.20 * framing_score
    )
    return round(min(1.0, max(0.0, score)), 4)


def classify(score: float) -> str:
    """Classify based on score thresholds."""
    if score >= settings.score_threshold_bon:
        return "bon"
    elif score >= settings.score_threshold_incertain:
        return "incertain"
    else:
        return "mauvais"


def score_to_percent(score: float) -> int:
    """Convert 0-1 score to 0-100 for display."""
    return round(score * 100)
