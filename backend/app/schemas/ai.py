from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.book import BookOut


class ChatRequest(BaseModel):
    message: str


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    books: list[BookOut]


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageOut]


class BookSummaryResponse(BaseModel):
    book_id: int
    summary: Optional[str] = None
    key_takeaways: list[str] = []
    target_audience: Optional[str] = None


class WhyResponse(BaseModel):
    book_id: int
    explanation: Optional[str] = None
