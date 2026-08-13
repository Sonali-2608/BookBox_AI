from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Recommendation(Base):
    """
    A persisted recommendation Lexora made to a user, with the score and
    a human-readable reason ("Why Lexora recommends this"). Persisting
    these lets the dashboard show recent recommendations without
    recomputing them, and lets us track recommendation -> interaction
    outcomes later.
    """

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    score = Column(Float, nullable=False, default=0.0)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recommendations")
    book = relationship("Book")
