from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    bib_number = Column(String(20), nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    race_time = Column(String(20), nullable=True)  # e.g. "02:34:12"
    country = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    event = relationship("Event")
