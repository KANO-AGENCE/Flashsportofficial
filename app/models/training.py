"""
AI Training Center models — fully separated from production pipeline.
Ground truth, review queues, datasets, model versions, training sessions.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
    func, Enum,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


# ─── Ground Truth (human corrections = training data) ───

class GroundTruth(Base):
    __tablename__ = "ground_truths"

    id = Column(Integer, primary_key=True, index=True)
    # Link to production
    detection_id = Column(Integer, ForeignKey("detections.id", ondelete="SET NULL"), nullable=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)

    # Image data
    image_path = Column(String(500), nullable=True)  # original image
    crop_path = Column(String(500), nullable=True)    # cropped torso

    # Bbox
    bbox_x = Column(Integer, default=0)
    bbox_y = Column(Integer, default=0)
    bbox_w = Column(Integer, default=0)
    bbox_h = Column(Integer, default=0)
    orientation = Column(Integer, default=0)  # final rotation applied

    # AI result
    ai_bib = Column(String(20), nullable=True)
    ai_classification = Column(String(20), nullable=True)
    ai_confidence_detection = Column(Float, default=0.0)
    ai_confidence_ocr = Column(Float, default=0.0)
    ai_blur_score = Column(Float, default=0.0)
    ai_ocr_raw = Column(String(200), nullable=True)
    ai_fallback_used = Column(Boolean, default=False)

    # Human correction (GROUND TRUTH)
    human_bib = Column(String(20), nullable=True)
    human_classification = Column(String(20), nullable=True)  # bon, mauvais, flou, coupe
    is_correct = Column(Boolean, default=False)  # AI was right

    # Context
    sport_type = Column(String(50), nullable=True)
    condition_lighting = Column(String(20), nullable=True)
    condition_weather = Column(String(20), nullable=True)
    condition_environment = Column(String(20), nullable=True)
    bib_color = Column(String(30), nullable=True)

    # Meta
    difficulty = Column(String(20), default="normal")  # easy, normal, hard, extreme
    error_type = Column(String(50), nullable=True)  # hallucination, digit_confusion, missed_bib, false_positive, rotation, blur_false_positive
    corrector_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    detection = relationship("Detection", foreign_keys=[detection_id])
    photo = relationship("Photo", foreign_keys=[photo_id])


# ─── Review Queue (auto-flagged problematic cases) ───

class ReviewItem(Base):
    __tablename__ = "review_items"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)

    # Why flagged
    reason = Column(String(50), nullable=False)  # low_confidence, ocr_ambiguous, multi_bib, fallback, hallucination, bad_bbox, rotation_doubt, high_blur, known_bibs_mismatch
    priority = Column(Integer, default=5)  # 1=urgent, 10=low
    queue = Column(String(30), default="to_review")  # to_review, difficult, hallucination, ocr_ambiguous, multi_bib, bad_detection, rotation, blur, user_error

    # Status
    status = Column(String(20), default="pending")  # pending, in_progress, resolved, skipped
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution = Column(String(50), nullable=True)  # corrected, confirmed, rejected

    created_at = Column(DateTime, server_default=func.now())

    detection = relationship("Detection", foreign_keys=[detection_id])
    photo = relationship("Photo", foreign_keys=[photo_id])


# ─── Datasets ───

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0")
    tags = Column(String(200), nullable=True)  # comma-separated: "running,day,rain"

    # Stats (cached)
    entry_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)

    status = Column(String(20), default="active")  # active, archived, training
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    entries = relationship("DatasetEntry", back_populates="dataset", cascade="all, delete-orphan")


class DatasetEntry(Base):
    __tablename__ = "dataset_entries"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    ground_truth_id = Column(Integer, ForeignKey("ground_truths.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    dataset = relationship("Dataset", back_populates="entries")
    ground_truth = relationship("GroundTruth", foreign_keys=[ground_truth_id])


# ─── AI Model Versions ───

class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(30), nullable=False)  # yolo, ocr, scorer, rotation
    version = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)

    # File
    model_path = Column(String(500), nullable=True)

    # Training info
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    training_session_id = Column(Integer, ForeignKey("training_sessions.id", ondelete="SET NULL"), nullable=True)

    # Metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    false_positive_rate = Column(Float, nullable=True)
    hallucination_rate = Column(Float, nullable=True)
    avg_inference_time = Column(Float, nullable=True)  # ms

    # Status
    status = Column(String(20), default="candidate")  # training, candidate, validated, production, archived
    promoted_at = Column(DateTime, nullable=True)
    promoted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    author = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    dataset = relationship("Dataset", foreign_keys=[dataset_id])


# ─── Training Sessions ───

class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(30), nullable=False)  # yolo, ocr, scorer
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)

    # Config
    config = Column(Text, nullable=True)  # JSON config
    epochs = Column(Integer, nullable=True)
    batch_size = Column(Integer, nullable=True)
    learning_rate = Column(Float, nullable=True)

    # Status
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)  # 0-100

    # Results
    best_metric = Column(Float, nullable=True)
    result_model_id = Column(Integer, ForeignKey("ai_models.id", ondelete="SET NULL"), nullable=True)
    logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    dataset = relationship("Dataset", foreign_keys=[dataset_id])
    result_model = relationship("AIModel", foreign_keys=[result_model_id])
