"""
AI Training Center service — ground truth, review queues, metrics, auto-detection.
Fully separated from production pipeline.
"""
import logging
from datetime import datetime

from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from app.models.models import Detection, Event, Photo
from app.models.training import (
    AIModel, Dataset, DatasetEntry, GroundTruth, ReviewItem, TrainingSession,
)

logger = logging.getLogger(__name__)


# ─── Auto-detection: flag problematic cases ───

REASON_THRESHOLDS = {
    "low_confidence": {"ocr_threshold": 0.5, "det_threshold": 0.4},
    "high_blur": {"blur_threshold": 50.0},
}


def auto_flag_detection(detection: Detection, photo: Photo, event: Event, db: Session) -> list[str]:
    """
    Analyze a detection and auto-flag it for human review if problematic.
    Called after processing. Returns list of reasons flagged.
    """
    reasons = []

    # Low OCR confidence
    if detection.bib_number and detection.confidence_ocr < 0.5:
        reasons.append(("low_confidence", 3, "ocr_ambiguous"))

    # Low detection confidence
    if detection.confidence_detection < 0.4:
        reasons.append(("low_confidence", 4, "bad_detection"))

    # Fallback used (YOLO missed, Qwen full-image)
    if detection.fallback_used:
        reasons.append(("fallback", 3, "bad_detection"))

    # High blur with bib detected (might be misread)
    if detection.bib_number and detection.blur_score < 50.0:
        reasons.append(("high_blur", 5, "blur"))

    # Hallucination patterns
    if detection.bib_number and detection.bib_number in {"1234", "12345", "0000", "1111", "9999"}:
        reasons.append(("hallucination", 1, "hallucination"))

    # Multiple detections on same photo
    det_count = db.query(sqlfunc.count(Detection.id)).filter(
        Detection.photo_id == photo.id
    ).scalar()
    if det_count and det_count > 1:
        reasons.append(("multi_bib", 4, "multi_bib"))

    # Known bibs mismatch
    if detection.bib_number and event and event.known_bibs:
        known = event.get_known_bibs_set()
        if known and detection.bib_number not in known:
            reasons.append(("known_bibs_mismatch", 2, "ocr_ambiguous"))

    # Rotation applied (check if image was rotated)
    if detection.bbox_w > 0 and detection.bbox_h > 0:
        ratio = detection.bbox_h / detection.bbox_w
        if ratio < 0.8:  # Very wide bbox = maybe still sideways
            reasons.append(("rotation_doubt", 3, "rotation"))

    # Create review items
    created = []
    for reason, priority, queue in reasons:
        existing = db.query(ReviewItem).filter(
            ReviewItem.detection_id == detection.id,
            ReviewItem.reason == reason,
        ).first()
        if not existing:
            item = ReviewItem(
                detection_id=detection.id,
                photo_id=photo.id,
                event_id=photo.event_id,
                reason=reason,
                priority=priority,
                queue=queue,
            )
            db.add(item)
            created.append(reason)

    return created


def auto_flag_event(event_id: int, db: Session) -> int:
    """Flag all problematic detections for an event. Returns count."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return 0

    photos = db.query(Photo).filter(
        Photo.event_id == event_id, Photo.processed == True
    ).all()

    total = 0
    for photo in photos:
        for det in photo.detections:
            flags = auto_flag_detection(det, photo, event, db)
            total += len(flags)

    db.commit()
    logger.info(f"Auto-flagged {total} issues for event {event_id}")
    return total


# ─── Ground Truth: collect from validations ───

def collect_ground_truth_from_detection(detection: Detection, db: Session) -> GroundTruth | None:
    """
    Convert a validated detection into a ground truth entry.
    Called when a human validates a detection.
    """
    if not detection.validated:
        return None

    # Check if already collected
    existing = db.query(GroundTruth).filter(
        GroundTruth.detection_id == detection.id
    ).first()

    photo = db.query(Photo).filter(Photo.id == detection.photo_id).first()
    event = db.query(Event).filter(Event.id == photo.event_id).first() if photo else None

    human_bib = detection.validated_bib
    human_class = detection.validated_class
    ai_correct = (
        human_bib == detection.bib_number and
        human_class == detection.classification
    ) if human_bib and human_class else False

    # Determine error type
    error_type = None
    if not ai_correct and human_bib and detection.bib_number:
        if detection.bib_number in {"1234", "12345", "0000"}:
            error_type = "hallucination"
        elif len(detection.bib_number) != len(human_bib):
            error_type = "digit_count"
        else:
            error_type = "digit_confusion"
    elif not ai_correct and human_bib and not detection.bib_number:
        error_type = "missed_bib"
    elif not ai_correct and not human_bib and detection.bib_number:
        error_type = "false_positive"

    # Determine difficulty
    difficulty = "normal"
    if detection.blur_score < 60:
        difficulty = "hard"
    if detection.fallback_used:
        difficulty = "hard"
    if detection.confidence_ocr < 0.5 and detection.bib_number:
        difficulty = "hard"

    gt_data = dict(
        detection_id=detection.id,
        photo_id=detection.photo_id,
        event_id=photo.event_id if photo else None,
        image_path=photo.filepath if photo else None,
        bbox_x=detection.bbox_x,
        bbox_y=detection.bbox_y,
        bbox_w=detection.bbox_w,
        bbox_h=detection.bbox_h,
        ai_bib=detection.bib_number,
        ai_classification=detection.classification,
        ai_confidence_detection=detection.confidence_detection,
        ai_confidence_ocr=detection.confidence_ocr,
        ai_blur_score=detection.blur_score,
        ai_ocr_raw=detection.ocr_raw_response,
        ai_fallback_used=detection.fallback_used or False,
        human_bib=human_bib,
        human_classification=human_class,
        is_correct=ai_correct,
        sport_type=event.sport_type if event else None,
        condition_lighting=event.condition_lighting if event else None,
        condition_weather=event.condition_weather if event else None,
        condition_environment=event.condition_environment if event else None,
        bib_color=event.bib_color if event else None,
        difficulty=difficulty,
        error_type=error_type,
    )

    if existing:
        for k, v in gt_data.items():
            setattr(existing, k, v)
        return existing
    else:
        gt = GroundTruth(**gt_data)
        db.add(gt)
        return gt


def collect_all_ground_truth(event_id: int, db: Session) -> int:
    """Collect ground truth from all validated detections for an event."""
    detections = (
        db.query(Detection)
        .join(Photo)
        .filter(Photo.event_id == event_id, Detection.validated == True)
        .all()
    )

    count = 0
    for det in detections:
        gt = collect_ground_truth_from_detection(det, db)
        if gt:
            count += 1

    db.commit()
    logger.info(f"Collected {count} ground truth entries from event {event_id}")
    return count


# ─── Dashboard Metrics ───

def get_dashboard_metrics(db: Session) -> dict:
    """Compute global training center metrics."""
    # Ground truth stats
    total_gt = db.query(sqlfunc.count(GroundTruth.id)).scalar() or 0
    correct_gt = db.query(sqlfunc.count(GroundTruth.id)).filter(
        GroundTruth.is_correct == True
    ).scalar() or 0
    accuracy = round(correct_gt / total_gt, 4) if total_gt > 0 else 0.0

    # Errors by type
    error_rows = (
        db.query(GroundTruth.error_type, sqlfunc.count(GroundTruth.id))
        .filter(GroundTruth.error_type.isnot(None))
        .group_by(GroundTruth.error_type)
        .all()
    )
    errors_by_type = {r[0]: r[1] for r in error_rows}

    # Errors by sport
    sport_rows = (
        db.query(GroundTruth.sport_type, sqlfunc.count(GroundTruth.id))
        .filter(GroundTruth.is_correct == False, GroundTruth.sport_type.isnot(None))
        .group_by(GroundTruth.sport_type)
        .all()
    )
    errors_by_sport = {r[0]: r[1] for r in sport_rows}

    # Errors by weather
    weather_rows = (
        db.query(GroundTruth.condition_weather, sqlfunc.count(GroundTruth.id))
        .filter(GroundTruth.is_correct == False, GroundTruth.condition_weather.isnot(None))
        .group_by(GroundTruth.condition_weather)
        .all()
    )
    errors_by_weather = {r[0]: r[1] for r in weather_rows}

    # Errors by lighting
    lighting_rows = (
        db.query(GroundTruth.condition_lighting, sqlfunc.count(GroundTruth.id))
        .filter(GroundTruth.is_correct == False, GroundTruth.condition_lighting.isnot(None))
        .group_by(GroundTruth.condition_lighting)
        .all()
    )
    errors_by_lighting = {r[0]: r[1] for r in lighting_rows}

    # Review queue
    pending = db.query(sqlfunc.count(ReviewItem.id)).filter(
        ReviewItem.status == "pending"
    ).scalar() or 0

    queue_rows = (
        db.query(ReviewItem.queue, sqlfunc.count(ReviewItem.id))
        .filter(ReviewItem.status == "pending")
        .group_by(ReviewItem.queue)
        .all()
    )
    reviews_by_queue = {r[0]: r[1] for r in queue_rows}

    # Datasets
    total_datasets = db.query(sqlfunc.count(Dataset.id)).scalar() or 0
    total_entries = db.query(sqlfunc.count(DatasetEntry.id)).scalar() or 0

    # Models by status
    model_rows = (
        db.query(AIModel.status, sqlfunc.count(AIModel.id))
        .group_by(AIModel.status)
        .all()
    )
    models_by_status = {r[0]: r[1] for r in model_rows}

    prod_models = db.query(AIModel).filter(AIModel.status == "production").all()

    # Suggestions
    suggestions = _generate_suggestions(total_gt, errors_by_type, pending, db)

    return {
        "total_corrections": total_gt,
        "correct_predictions": correct_gt,
        "accuracy_rate": accuracy,
        "errors_by_type": errors_by_type,
        "errors_by_sport": errors_by_sport,
        "errors_by_weather": errors_by_weather,
        "errors_by_lighting": errors_by_lighting,
        "pending_reviews": pending,
        "reviews_by_queue": reviews_by_queue,
        "total_datasets": total_datasets,
        "total_entries": total_entries,
        "models_by_status": models_by_status,
        "production_models": prod_models,
        "suggestions": suggestions,
    }


def _generate_suggestions(total_gt: int, errors_by_type: dict, pending: int, db: Session) -> list[dict]:
    """Auto-generate improvement suggestions."""
    suggestions = []

    if pending > 20:
        suggestions.append({
            "type": "review",
            "priority": "high",
            "title": f"{pending} photos en attente de validation",
            "description": "Des cas problematiques attendent votre verification.",
            "action": "review_queue",
        })

    if total_gt > 100:
        suggestions.append({
            "type": "dataset",
            "priority": "medium",
            "title": f"{total_gt} corrections disponibles pour un dataset",
            "description": "Suffisamment de donnees pour creer un dataset d'entrainement.",
            "action": "create_dataset",
        })

    hallucinations = errors_by_type.get("hallucination", 0)
    if hallucinations > 5:
        suggestions.append({
            "type": "training",
            "priority": "high",
            "title": f"{hallucinations} hallucinations detectees",
            "description": "Le modele OCR produit des numeros inventes. Un re-entrainement est recommande.",
            "action": "train_ocr",
        })

    digit_conf = errors_by_type.get("digit_confusion", 0)
    if digit_conf > 10:
        suggestions.append({
            "type": "training",
            "priority": "medium",
            "title": f"{digit_conf} confusions de chiffres",
            "description": "Le modele confond regulierement certains chiffres (3/8, 6/9, etc).",
            "action": "train_ocr",
        })

    missed = errors_by_type.get("missed_bib", 0)
    if missed > 10:
        suggestions.append({
            "type": "training",
            "priority": "medium",
            "title": f"{missed} dossards manques",
            "description": "Le modele ne detecte pas certains dossards. Ameliorer le crop ou le prompt.",
            "action": "improve_crop",
        })

    return suggestions


# ─── Dataset operations ───

def update_dataset_stats(dataset_id: int, db: Session):
    """Recompute cached stats for a dataset."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        return

    ds.entry_count = db.query(sqlfunc.count(DatasetEntry.id)).filter(
        DatasetEntry.dataset_id == dataset_id
    ).scalar() or 0

    ds.correct_count = (
        db.query(sqlfunc.count(DatasetEntry.id))
        .join(GroundTruth, DatasetEntry.ground_truth_id == GroundTruth.id)
        .filter(DatasetEntry.dataset_id == dataset_id, GroundTruth.is_correct == True)
        .scalar() or 0
    )

    ds.error_count = ds.entry_count - ds.correct_count
    db.commit()


def add_ground_truths_to_dataset(dataset_id: int, gt_ids: list[int], db: Session) -> int:
    """Add specific ground truth entries to a dataset."""
    added = 0
    for gt_id in gt_ids:
        existing = db.query(DatasetEntry).filter(
            DatasetEntry.dataset_id == dataset_id,
            DatasetEntry.ground_truth_id == gt_id,
        ).first()
        if not existing:
            entry = DatasetEntry(dataset_id=dataset_id, ground_truth_id=gt_id)
            db.add(entry)
            added += 1

    db.commit()
    update_dataset_stats(dataset_id, db)
    return added


def add_filtered_ground_truths(dataset_id: int, filters: dict, db: Session) -> int:
    """Add ground truths matching filters to a dataset."""
    query = db.query(GroundTruth.id)

    if filters.get("sport_type"):
        query = query.filter(GroundTruth.sport_type == filters["sport_type"])
    if filters.get("error_type"):
        query = query.filter(GroundTruth.error_type == filters["error_type"])
    if filters.get("difficulty"):
        query = query.filter(GroundTruth.difficulty == filters["difficulty"])
    if filters.get("event_id"):
        query = query.filter(GroundTruth.event_id == filters["event_id"])
    if filters.get("is_correct") is not None:
        query = query.filter(GroundTruth.is_correct == filters["is_correct"])

    gt_ids = [r[0] for r in query.all()]
    return add_ground_truths_to_dataset(dataset_id, gt_ids, db)
