from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Frame(Base):
    __tablename__ = "frames"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    image_path = Column(String(500), nullable=False)
    text_x = Column(Float, default=0.5)  # relative position (0-1)
    text_y = Column(Float, default=0.9)  # relative position (0-1)
    text_size = Column(Integer, default=48)
    text_color = Column(String(20), default="#FFFFFF")
    created_at = Column(DateTime, server_default=func.now())

    event = relationship("Event")
