import enum

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ReadingStatus(str, enum.Enum):
    want_to_read = "want_to_read"
    reading = "reading"
    completed = "completed"


class ReadingHistory(Base):
    __tablename__ = "reading_history"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_user_book_reading"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    status = Column(SQLEnum(ReadingStatus), nullable=False, default=ReadingStatus.want_to_read)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="reading_history")
    book = relationship("Book")
