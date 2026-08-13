"""
Import every model here so that:
  1. `Base.metadata.create_all()` knows about every table.
  2. Alembic's autogenerate can detect every model.
  3. Other modules can do `from app.models import User` etc.
"""

from app.models.book import Book
from app.models.book_interaction import BookInteraction, InteractionType
from app.models.chat_history import ChatHistory, ChatRole
from app.models.preference import PreferredLength, ReadingFrequency, UserPreference
from app.models.reading_history import ReadingHistory, ReadingStatus
from app.models.recommendation import Recommendation
from app.models.user import User, UserRole
from app.models.wishlist import Wishlist

__all__ = [
    "Book",
    "BookInteraction",
    "InteractionType",
    "ChatHistory",
    "ChatRole",
    "PreferredLength",
    "ReadingFrequency",
    "UserPreference",
    "ReadingHistory",
    "ReadingStatus",
    "Recommendation",
    "User",
    "UserRole",
    "Wishlist",
]
