"""Schemas for AI Training Center."""
from datetime import datetime
from pydantic import BaseModel


# ─── Ground Truth ───

class GroundTruthOut(BaseModel):
    id: int
    detection_id: int | None
    photo_id: int | None
    event_id: int | None
    image_path: str | None
    crop_path: str | None
    bbox_x: int = 0
    bbox_y: int = 0
    bbox_w: int = 0
    bbox_h: int = 0
    orientation: int = 0
    ai_bib: str | None
    ai_classification: str | None
    ai_confidence_detection: float = 0.0
    ai_confidence_ocr: float = 0.0
    ai_blur_score: float = 0.0
    ai_ocr_raw: str | None
    ai_fallback_used: bool = False
    human_bib: str | None
    human_classification: str | None
    is_correct: bool = False
    sport_type: str | None
    condition_lighting: str | None
    condition_weather: str | None
    difficulty: str = "normal"
    error_type: str | None
    created_at: datetime | None

    class Config:
        from_attributes = True


# ─── Review Queue ───

class ReviewItemOut(BaseModel):
    id: int
    detection_id: int
    photo_id: int
    event_id: int
    reason: str
    priority: int = 5
    queue: str = "to_review"
    status: str = "pending"
    resolution: str | None
    created_at: datetime | None
    # Joined data
    photo_filename: str | None = None
    photo_filepath: str | None = None
    bib_number: str | None = None
    classification: str | None = None
    confidence_ocr: float = 0.0
    ocr_raw_response: str | None = None
    bbox_x: int = 0
    bbox_y: int = 0
    bbox_w: int = 0
    bbox_h: int = 0
    fallback_used: bool = False

    class Config:
        from_attributes = True


class ReviewResolve(BaseModel):
    resolution: str  # corrected, confirmed, rejected
    corrected_bib: str | None = None
    corrected_class: str | None = None
    difficulty: str | None = None
    error_type: str | None = None


# ─── Datasets ───

class DatasetCreate(BaseModel):
    name: str
    description: str | None = None
    tags: str | None = None


class DatasetOut(BaseModel):
    id: int
    name: str
    description: str | None
    version: str = "1.0"
    tags: str | None
    entry_count: int = 0
    correct_count: int = 0
    error_count: int = 0
    status: str = "active"
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class DatasetAddEntries(BaseModel):
    ground_truth_ids: list[int] = []
    filters: dict | None = None  # {sport_type, error_type, difficulty, event_id}


# ─── AI Models ───

class AIModelOut(BaseModel):
    id: int
    name: str
    model_type: str
    version: str
    description: str | None
    model_path: str | None
    dataset_id: int | None
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    false_positive_rate: float | None
    hallucination_rate: float | None
    avg_inference_time: float | None
    status: str = "candidate"
    author: str | None
    notes: str | None
    created_at: datetime | None

    class Config:
        from_attributes = True


class AIModelCreate(BaseModel):
    name: str
    model_type: str
    version: str
    description: str | None = None
    model_path: str | None = None
    notes: str | None = None


class AIModelPromote(BaseModel):
    status: str  # candidate, validated, production, archived


# ─── Training Sessions ───

class TrainingSessionOut(BaseModel):
    id: int
    name: str
    model_type: str
    dataset_id: int | None
    config: str | None
    epochs: int | None
    batch_size: int | None
    learning_rate: float | None
    status: str = "pending"
    progress: float = 0.0
    best_metric: float | None
    result_model_id: int | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime | None

    class Config:
        from_attributes = True


class TrainingSessionCreate(BaseModel):
    name: str
    model_type: str
    dataset_id: int | None = None
    epochs: int | None = None
    batch_size: int | None = None
    learning_rate: float | None = None
    config: str | None = None


# ─── Dashboard / Metrics ───

class TrainingDashboard(BaseModel):
    # Ground truth stats
    total_corrections: int = 0
    correct_predictions: int = 0
    accuracy_rate: float = 0.0

    # Error breakdown
    errors_by_type: dict = {}  # {hallucination: 5, digit_confusion: 12, ...}
    errors_by_sport: dict = {}
    errors_by_weather: dict = {}
    errors_by_lighting: dict = {}

    # Review queue
    pending_reviews: int = 0
    reviews_by_queue: dict = {}

    # Datasets
    total_datasets: int = 0
    total_entries: int = 0

    # Models
    models_by_status: dict = {}
    production_models: list[AIModelOut] = []

    # Suggestions
    suggestions: list[dict] = []


class PerformanceComparison(BaseModel):
    model_a: AIModelOut
    model_b: AIModelOut
    metrics_comparison: dict = {}  # {metric_name: {a: val, b: val, diff: val, winner: "a"|"b"}}
