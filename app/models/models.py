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
    Text,
    UniqueConstraint,
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

    # --- Processing config ---
    sample_bib_path = Column(String(500), nullable=True)
    blur_threshold = Column(Float, default=100.0)
    yolo_confidence = Column(Float, default=0.35)
    bib_min_digits = Column(Integer, default=1)
    bib_max_digits = Column(Integer, default=5)
    precision_mode = Column(Boolean, default=True)  # True = fiabilité max, False = rapide

    # --- Race configuration ---
    # Sport
    sport_type = Column(String(50), default="running")  # running, triathlon, cycling, trail, swimming, obstacle, other
    # Bib
    bib_color = Column(String(30), default="white")  # white, black, yellow, red, blue, green, multi
    bib_position = Column(String(20), default="chest")  # chest, back, both
    # Known bib list (newline-separated for validation)
    known_bibs = Column(Text, nullable=True)
    # Conditions
    condition_lighting = Column(String(20), default="day")  # day, night, mixed
    condition_environment = Column(String(20), default="outdoor")  # outdoor, indoor, mixed
    condition_weather = Column(String(20), default="clear")  # clear, rain, mud, snow
    photos_fast_motion = Column(Boolean, default=False)
    avg_runners_per_photo = Column(Integer, default=2)

    photos = relationship("Photo", back_populates="event", cascade="all, delete-orphan")
    cards = relationship("Card", back_populates="event", cascade="all, delete-orphan")
    bib_groups = relationship("BibGroup", back_populates="event", cascade="all, delete-orphan")

    def get_known_bibs_set(self) -> set[str]:
        """Parse known_bibs text into a set of bib strings."""
        if not self.known_bibs:
            return set()
        return {b.strip() for b in self.known_bibs.strip().splitlines() if b.strip()}


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    card_number = Column(Integer, default=1)  # Sequential card number within event
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
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("cards.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)  # Original name before renaming
    filepath = Column(String(500), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    processed = Column(Boolean, default=False)
    processing_time = Column(Float, nullable=True)  # Seconds taken to process
    created_at = Column(DateTime, server_default=func.now())

    event = relationship("Event", back_populates="photos")
    card = relationship("Card", back_populates="photos")
    detections = relationship("Detection", back_populates="photo", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False, index=True)
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
    # Pipeline traceability
    fallback_used = Column(Boolean, default=False)
    ocr_raw_response = Column(String(200), nullable=True)

    # Multi-person: per-detection status and visibility
    status = Column(String(20), default="pending")  # pending, confirmed, manual, rejected, no_bib, background_runner, low_confidence
    person_index = Column(Integer, default=0)  # 0=biggest person, 1=second, etc.
    main_subject_score = Column(Float, default=0.0)  # how important this person is in the photo
    is_primary_subject = Column(Boolean, default=True)  # is this a main subject vs background
    is_usable_subject = Column(Boolean, default=True)  # passed photographer's eye filter
    should_publish = Column(Boolean, default=True)  # show on client website

    photo = relationship("Photo", back_populates="detections")


class BibGroup(Base):
    __tablename__ = "bib_groups"
    __table_args__ = (UniqueConstraint("event_id", "bib_number", name="uq_bib_group_event_bib"),)

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    bib_number = Column(String(20), nullable=False)
    photo_count = Column(Integer, default=0)
    best_photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)

    event = relationship("Event", back_populates="bib_groups")
    best_photo = relationship("Photo", foreign_keys=[best_photo_id])
