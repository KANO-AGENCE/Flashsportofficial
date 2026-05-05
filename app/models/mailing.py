"""Models for the mailing module."""
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Mailing(Base):
    """A mailing campaign."""
    __tablename__ = "mailings"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(500), nullable=False)
    raw_content = Column(Text, nullable=True)
    html_content = Column(Text, nullable=True)
    # Segment filter: event_id to target, null = all customers
    event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="draft")  # draft, ready, sent
    sent_count = Column(Integer, default=0)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    event = relationship("Event")
