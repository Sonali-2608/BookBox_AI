from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.book import BookOut


class WishlistAddRequest(BaseModel):
    book_id: int


class WishlistItemOut(BaseModel):
    book: BookOut
    added_at: datetime


class WishlistResponse(BaseModel):
    count: int
    items: list[WishlistItemOut]


class ReadingStatusUpdateRequest(BaseModel):
    book_id: int
    status: str  # want_to_read | reading | completed


class ReadingHistoryItemOut(BaseModel):
    book: BookOut
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime


class ReadingHistoryResponse(BaseModel):
    count: int
    items: list[ReadingHistoryItemOut]
