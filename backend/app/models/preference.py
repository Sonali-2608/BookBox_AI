import enum

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ReadingFrequency(str, enum.Enum):
    daily = "daily"
    several_times_a_week = "several_times_a_week"
    weekly = "weekly"
    occasionally = "occasionally"


class PreferredLength(str, enum.Enum):
    short = "short"
    medium = "medium"
    long = "long"


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Stored as JSON arrays of strings so this works identically on
    # PostgreSQL and SQLite (used in tests).
    favorite_genres = Column(JSON, default=list)
    favorite_authors = Column(JSON, default=list)

    reading_frequency = Column(SQLEnum(ReadingFrequency), nullable=True)
    preferred_length = Column(SQLEnum(PreferredLength), nullable=True)
    onboarding_completed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preferences")
