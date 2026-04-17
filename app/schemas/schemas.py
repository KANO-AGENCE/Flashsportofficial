from datetime import date, datetime
from pydantic import BaseModel


# --- Events ---

class EventCreate(BaseModel):
    name: str
    date: date


class CardOut(BaseModel):
    id: int
    name: str
    source_path: str | None = None
    photo_count: int = 0
    total_expected: int = 0
    status: str = "pending"
    created_at: datetime | None = None

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
    sample_bib_path: str | None = None
    blur_threshold: float = 100.0
    yolo_confidence: float = 0.35
    bib_min_digits: int = 1
    bib_max_digits: int = 5

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

    class Config:
        from_attributes = True


# --- Photos ---

class PhotoOut(BaseModel):
    id: int
    event_id: int
    filename: str
    filepath: str
    width: int | None
    height: int | None
    processed: bool
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


# --- BibGroups ---

class BibGroupOut(BaseModel):
    id: int
    bib_number: str
    photo_count: int
    best_photo_id: int | None
    photos: list[PhotoOut] = []

    class Config:
        from_attributes = True
