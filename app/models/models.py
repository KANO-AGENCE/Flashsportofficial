from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    # Config
    sample_bib_path = Column(String(500), nullable=True)
    blur_threshold = Column(Float, default=100.0)
    yolo_confidence = Column(Float, default=0.35)
    bib_min_digits = Column(Integer, default=1)
    bib_max_digits = Column(Integer, default=5)

    photos = relationship("Photo", back_populates="event", cascade="all, delete-orphan")
    cards = relationship("Card", back_populates="event", cascade="all, delete-orphan")
    bib_groups = relationship("BibGroup", back_populates="event", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    source_path = Column(String(500), nullable=True)
    photo_count = Column(Integer, default=0)
    total_expected = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, importing, done, error, stopped
    created_at = Column(DateTime, server_default=func.now())

    event = relationship("Event", back_populates="cards")
    photos = relationship("Photo", back_populates="card", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(500), nullable=False)
    filepath = Column(String(500), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    event = relationship("Event", back_populates="photos")
    card = relationship("Card", back_populates="photos")
    detections = relationship("Detection", back_populates="photo", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    bib_number = Column(String(20), nullable=True)
    confidence_detection = Column(Float, default=0.0)
    confidence_ocr = Column(Float, default=0.0)
    bbox_x = Column(Integer, default=0)
    bbox_y = Column(Integer, default=0)
    bbox_w = Column(Integer, default=0)
    bbox_h = Column(Integer, default=0)
    blur_score = Column(Float, default=0.0)
    framing_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    classification = Column(String(20), default="mauvais")
    validated = Column(Boolean, default=False)
    validated_bib = Column(String(20), nullable=True)
    validated_class = Column(String(20), nullable=True)

    photo = relationship("Photo", back_populates="detections")


class BibGroup(Base):
    __tablename__ = "bib_groups"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    bib_number = Column(String(20), nullable=False)
    photo_count = Column(Integer, default=0)
    best_photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)

    event = relationship("Event", back_populates="bib_groups")
    best_photo = relationship("Photo", foreign_keys=[best_photo_id])
