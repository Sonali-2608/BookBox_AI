import enum

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InteractionType(str, enum.Enum):
    view = "view"
    search_click = "search_click"
    wishlist_add = "wishlist_add"
    rating = "rating"


class BookInteraction(Base):
    """
    Lightweight event log of how a user interacts with books. Feeds the
    recommendation engine (Phase 6) as an implicit-feedback signal
    alongside wishlist/reading history.
    """

    __tablename__ = "book_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    interaction_type = Column(SQLEnum(InteractionType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="interactions")
    book = relationship("Book")
