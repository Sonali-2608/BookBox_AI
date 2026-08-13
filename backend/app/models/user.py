import enum

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    profile_image = Column(String, nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.user, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    preferences = relationship(
        "UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    wishlist_items = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")
    reading_history = relationship(
        "ReadingHistory", back_populates="user", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "Recommendation", back_populates="user", cascade="all, delete-orphan"
    )
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship(
        "BookInteraction", back_populates="user", cascade="all, delete-orphan"
    )
