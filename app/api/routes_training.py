"""
AI Training Center API — fully separated from production.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from app.core.dependencies import require_module
from app.db.database import get_db
from app.models.models import Detection, Event, Photo
from app.models.training import (
    AIModel, Dataset, DatasetEntry, GroundTruth, ReviewItem, TrainingSession,
)
from app.schemas.training import (
    AIModelCreate, AIModelOut, AIModelPromote,
    DatasetAddEntries, DatasetCreate, DatasetOut,
    GroundTruthOut, ReviewItemOut, ReviewResolve,
    TrainingDashboard, TrainingSessionCreate, TrainingSessionOut,
    PerformanceComparison,
)
from app.services.training_service import (
    auto_flag_event, collect_all_ground_truth, collect_ground_truth_from_detection,
    get_dashboard_metrics, add_ground_truths_to_dataset, add_filtered_ground_truths,
    update_dataset_stats,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/training", tags=["training"])
_tri_user = require_module("TRI")


# ═══════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(_tri_user)):
    return get_dashboard_metrics(db)


# ═══════════════════════════════════════════
# GROUND TRUTH
# ═══════════════════════════════════════════

@router.get("/ground-truth", response_model=list[GroundTruthOut])
def list_ground_truth(
    event_id: int | None = None,
    error_type: str | None = None,
    sport_type: str | None = None,
    is_correct: bool | None = None,
    difficulty: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    query = db.query(GroundTruth)
    if event_id:
        query = query.filter(GroundTruth.event_id == event_id)
    if error_type:
        query = query.filter(GroundTruth.error_type == error_type)
    if sport_type:
        query = query.filter(GroundTruth.sport_type == sport_type)
    if is_correct is not None:
        query = query.filter(GroundTruth.is_correct == is_correct)
    if difficulty:
        query = query.filter(GroundTruth.difficulty == difficulty)
    return query.order_by(GroundTruth.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/ground-truth/stats")
def ground_truth_stats(db: Session = Depends(get_db), _=Depends(_tri_user)):
    total = db.query(sqlfunc.count(GroundTruth.id)).scalar() or 0
    correct = db.query(sqlfunc.count(GroundTruth.id)).filter(GroundTruth.is_correct == True).scalar() or 0
    by_error = dict(
        db.query(GroundTruth.error_type, sqlfunc.count(GroundTruth.id))
        .filter(GroundTruth.error_type.isnot(None))
        .group_by(GroundTruth.error_type).all()
    )
    by_sport = dict(
        db.query(GroundTruth.sport_type, sqlfunc.count(GroundTruth.id))
        .filter(GroundTruth.sport_type.isnot(None))
        .group_by(GroundTruth.sport_type).all()
    )
    by_difficulty = dict(
        db.query(GroundTruth.difficulty, sqlfunc.count(GroundTruth.id))
        .group_by(GroundTruth.difficulty).all()
    )
    return {
        "total": total, "correct": correct,
        "accuracy": round(correct / total, 4) if total else 0,
        "by_error": by_error, "by_sport": by_sport, "by_difficulty": by_difficulty,
    }


@router.post("/ground-truth/collect/{event_id}")
def collect_ground_truth(event_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    count = collect_all_ground_truth(event_id, db)
    return {"message": f"{count} ground truth entries collected", "count": count}


@router.post("/ground-truth/collect-all")
def collect_all(db: Session = Depends(get_db), _=Depends(_tri_user)):
    events = db.query(Event.id).all()
    total = 0
    for (eid,) in events:
        total += collect_all_ground_truth(eid, db)
    return {"message": f"{total} ground truth entries collected", "count": total}


# ═══════════════════════════════════════════
# REVIEW QUEUE
# ═══════════════════════════════════════════

@router.get("/review", response_model=list[ReviewItemOut])
def list_review_items(
    queue: str | None = None,
    status: str = "pending",
    event_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    query = db.query(ReviewItem).filter(ReviewItem.status == status)
    if queue:
        query = query.filter(ReviewItem.queue == queue)
    if event_id:
        query = query.filter(ReviewItem.event_id == event_id)

    items = query.order_by(ReviewItem.priority, ReviewItem.created_at).offset(offset).limit(limit).all()

    result = []
    for item in items:
        det = db.query(Detection).filter(Detection.id == item.detection_id).first()
        photo = db.query(Photo).filter(Photo.id == item.photo_id).first()
        out = ReviewItemOut(
            id=item.id,
            detection_id=item.detection_id,
            photo_id=item.photo_id,
            event_id=item.event_id,
            reason=item.reason,
            priority=item.priority,
            queue=item.queue,
            status=item.status,
            resolution=item.resolution,
            created_at=item.created_at,
            photo_filename=photo.filename if photo else None,
            photo_filepath=photo.filepath if photo else None,
            bib_number=det.bib_number if det else None,
            classification=det.classification if det else None,
            confidence_ocr=det.confidence_ocr if det else 0,
            ocr_raw_response=det.ocr_raw_response if det else None,
            bbox_x=det.bbox_x if det else 0,
            bbox_y=det.bbox_y if det else 0,
            bbox_w=det.bbox_w if det else 0,
            bbox_h=det.bbox_h if det else 0,
            fallback_used=det.fallback_used if det else False,
        )
        result.append(out)
    return result


@router.get("/review/counts")
def review_counts(db: Session = Depends(get_db), _=Depends(_tri_user)):
    rows = (
        db.query(ReviewItem.queue, sqlfunc.count(ReviewItem.id))
        .filter(ReviewItem.status == "pending")
        .group_by(ReviewItem.queue)
        .all()
    )
    total = sum(r[1] for r in rows)
    return {"total": total, "by_queue": {r[0]: r[1] for r in rows}}


@router.post("/review/{item_id}/resolve")
def resolve_review(item_id: int, data: ReviewResolve, db: Session = Depends(get_db), _=Depends(_tri_user)):
    item = db.query(ReviewItem).filter(ReviewItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")

    item.status = "resolved"
    item.resolution = data.resolution
    item.resolved_at = datetime.utcnow()

    # If corrected, update detection and collect ground truth
    det = db.query(Detection).filter(Detection.id == item.detection_id).first()
    if det and data.resolution == "corrected":
        if data.corrected_bib is not None:
            det.validated_bib = data.corrected_bib
        if data.corrected_class is not None:
            det.validated_class = data.corrected_class
        det.validated = True
        collect_ground_truth_from_detection(det, db)
    elif det and data.resolution == "confirmed":
        det.validated = True
        det.validated_bib = det.bib_number
        det.validated_class = det.classification
        collect_ground_truth_from_detection(det, db)

    db.commit()
    return {"message": "Review resolved"}


@router.post("/review/flag-event/{event_id}")
def flag_event(event_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    count = auto_flag_event(event_id, db)
    return {"message": f"{count} issues flagged", "count": count}


# ═══════════════════════════════════════════
# DATASETS
# ═══════════════════════════════════════════

@router.get("/datasets", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db), _=Depends(_tri_user)):
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


@router.post("/datasets", response_model=DatasetOut)
def create_dataset(data: DatasetCreate, db: Session = Depends(get_db), _=Depends(_tri_user)):
    ds = Dataset(name=data.name, description=data.description, tags=data.tags)
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


@router.get("/datasets/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    return ds


@router.post("/datasets/{dataset_id}/add-entries")
def dataset_add_entries(dataset_id: int, data: DatasetAddEntries, db: Session = Depends(get_db), _=Depends(_tri_user)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")

    if data.ground_truth_ids:
        count = add_ground_truths_to_dataset(dataset_id, data.ground_truth_ids, db)
    elif data.filters:
        count = add_filtered_ground_truths(dataset_id, data.filters, db)
    else:
        # Add all ground truths
        all_ids = [r[0] for r in db.query(GroundTruth.id).all()]
        count = add_ground_truths_to_dataset(dataset_id, all_ids, db)

    return {"message": f"{count} entries added", "count": count}


@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404)
    db.delete(ds)
    db.commit()
    return {"message": "Dataset deleted"}


# ═══════════════════════════════════════════
# AI MODELS
# ═══════════════════════════════════════════

@router.get("/models", response_model=list[AIModelOut])
def list_models(
    model_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    query = db.query(AIModel)
    if model_type:
        query = query.filter(AIModel.model_type == model_type)
    if status:
        query = query.filter(AIModel.status == status)
    return query.order_by(AIModel.created_at.desc()).all()


@router.post("/models", response_model=AIModelOut)
def create_model(data: AIModelCreate, db: Session = Depends(get_db), _=Depends(_tri_user)):
    m = AIModel(**data.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.put("/models/{model_id}/promote")
def promote_model(model_id: int, data: AIModelPromote, db: Session = Depends(get_db), _=Depends(_tri_user)):
    m = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not m:
        raise HTTPException(404)

    if data.status == "production":
        # Demote current production model of same type
        db.query(AIModel).filter(
            AIModel.model_type == m.model_type,
            AIModel.status == "production",
            AIModel.id != model_id,
        ).update({"status": "archived"})
        m.promoted_at = datetime.utcnow()

    m.status = data.status
    db.commit()
    return {"message": f"Model {m.name} promoted to {data.status}"}


@router.get("/models/compare")
def compare_models(
    model_a_id: int = Query(...),
    model_b_id: int = Query(...),
    db: Session = Depends(get_db),
    _=Depends(_tri_user),
):
    a = db.query(AIModel).filter(AIModel.id == model_a_id).first()
    b = db.query(AIModel).filter(AIModel.id == model_b_id).first()
    if not a or not b:
        raise HTTPException(404, "Model not found")

    metrics = ["accuracy", "precision", "recall", "f1_score", "false_positive_rate", "hallucination_rate", "avg_inference_time"]
    comparison = {}
    for metric in metrics:
        va = getattr(a, metric)
        vb = getattr(b, metric)
        if va is not None and vb is not None:
            # For inference time, lower is better
            better_is_lower = metric in ("false_positive_rate", "hallucination_rate", "avg_inference_time")
            if better_is_lower:
                winner = "a" if va < vb else "b" if vb < va else "tie"
            else:
                winner = "a" if va > vb else "b" if vb > va else "tie"
            comparison[metric] = {"a": va, "b": vb, "diff": round(va - vb, 4), "winner": winner}

    return {
        "model_a": AIModelOut.model_validate(a),
        "model_b": AIModelOut.model_validate(b),
        "metrics_comparison": comparison,
    }


# ═══════════════════════════════════════════
# TRAINING SESSIONS
# ═══════════════════════════════════════════

@router.get("/sessions", response_model=list[TrainingSessionOut])
def list_sessions(db: Session = Depends(get_db), _=Depends(_tri_user)):
    return db.query(TrainingSession).order_by(TrainingSession.created_at.desc()).all()


@router.post("/sessions", response_model=TrainingSessionOut)
def create_session(data: TrainingSessionCreate, db: Session = Depends(get_db), _=Depends(_tri_user)):
    session = TrainingSession(**data.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=TrainingSessionOut)
def get_session(session_id: int, db: Session = Depends(get_db), _=Depends(_tri_user)):
    s = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not s:
        raise HTTPException(404)
    return s
