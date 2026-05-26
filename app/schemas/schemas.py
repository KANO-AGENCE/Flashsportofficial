from datetime import date, datetime
from pydantic import BaseModel


# --- Events ---

class EventCreate(BaseModel):
    name: str
    date: date
    slug: str | None = None
    description: str | None = None
    photo_price: float = 2.0
    pack_price: float = 9.90
    all_photos_price: float = 49.90


class RaceConfig(BaseModel):
    """Race configuration — all fields optional for partial updates."""
    # Processing
    blur_threshold: float | None = None
    yolo_confidence: float | None = None
    bib_min_digits: int | None = None
    bib_max_digits: int | None = None
    precision_mode: bool | None = None
    # Sport
    sport_type: str | None = None
    # Bib
    bib_color: str | None = None
    bib_position: str | None = None
    known_bibs: str | None = None
    # Conditions
    condition_lighting: str | None = None
    condition_environment: str | None = None
    condition_weather: str | None = None
    photos_fast_motion: bool | None = None
    avg_runners_per_photo: int | None = None


class CardOut(BaseModel):
    id: int
    name: str
    card_number: int = 1
    source_path: str | None = None
    photo_count: int = 0
    total_expected: int = 0
    status: str = "pending"
    created_at: datetime | None = None
    processed_count: int = 0
    pending_count: int = 0
    validated_count: int = 0
    unique_bibs: int = 0

    class Config:
        from_attributes = True


class EventStats(BaseModel):
    bon: int = 0
    mauvais: int = 0
    flou: int = 0
    coupe: int = 0
    incertain: int = 0
    unique_bibs: int = 0
    validated: int = 0


class EventOut(BaseModel):
    id: int
    name: str
    date: date
    created_at: datetime | None = None
    photo_count: int = 0
    processed_count: int = 0
    pending_count: int = 0
    stats: EventStats | None = None
    cards: list[CardOut] = []
    # Processing config
    sample_bib_path: str | None = None
    blur_threshold: float = 100.0
    yolo_confidence: float = 0.35
    bib_min_digits: int = 1
    bib_max_digits: int = 5
    precision_mode: bool = True
    # Race config
    sport_type: str = "running"
    bib_color: str = "white"
    bib_position: str = "chest"
    known_bibs: str | None = None
    condition_lighting: str = "day"
    condition_environment: str = "outdoor"
    condition_weather: str = "clear"
    photos_fast_motion: bool = False
    avg_runners_per_photo: int = 2
    # Web event info
    web_event_id: int | None = None
    slug: str | None = None
    is_published: bool = False

    class Config:
        from_attributes = True


# --- Detections ---

class DetectionOut(BaseModel):
    id: int
    bib_number: str | None
    confidence_detection: float
    confidence_ocr: float
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    blur_score: float
    framing_score: float
    overall_score: float
    classification: str
    validated: bool
    validated_bib: str | None
    validated_class: str | None
    fallback_used: bool = False
    ocr_raw_response: str | None = None
    # Multi-person
    status: str = "pending"
    person_index: int = 0
    main_subject_score: float = 0.0
    is_primary_subject: bool = True
    is_usable_subject: bool = True
    should_publish: bool = True

    class Config:
        from_attributes = True


# --- Photos ---

class PhotoOut(BaseModel):
    id: int
    event_id: int
    filename: str
    original_filename: str | None = None
    filepath: str
    width: int | None
    height: int | None
    processed: bool
    processing_time: float | None = None
    created_at: datetime | None = None
    detections: list[DetectionOut] = []

    class Config:
        from_attributes = True


# --- Processing ---

class ProcessResponse(BaseModel):
    message: str
    total: int
    already_processed: int


class ProcessStatus(BaseModel):
    total: int
    processed: int
    pending: int


# --- Validation ---

class ValidationUpdate(BaseModel):
    validated_bib: str | None = None
    validated_class: str | None = None
    should_publish: bool | None = None
    status: str | None = None


# --- BibGroups ---

class BibGroupOut(BaseModel):
    id: int
    bib_number: str
    photo_count: int
    best_photo_id: int | None
    photos: list[PhotoOut] = []

    class Config:
        from_attributes = True
