from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), default="")
    last_name = Column(String(100), default="")
    role = Column(String(20), nullable=False, default="POSTE_TRI")  # SUPERADMIN, ADMIN, POSTE_TRI
    modules = Column(JSONB, default=["TRI"])  # activated modules
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
