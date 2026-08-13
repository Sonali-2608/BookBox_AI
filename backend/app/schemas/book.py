from typing import Optional

from pydantic import BaseModel, ConfigDict


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    google_books_id: Optional[str] = None
    isbn: Optional[str] = None
    title: str
    authors: list[str] = []
    cover_url: Optional[str] = None
    description: Optional[str] = None
    categories: list[str] = []
    rating: Optional[float] = None
    page_count: Optional[int] = None
    published_date: Optional[str] = None
    publisher: Optional[str] = None
    language: Optional[str] = None


class BookSearchResponse(BaseModel):
    query: str
    search_type: str
    source: str  # "google_books" | "open_library" | "none"
    count: int
    results: list[BookOut]


class ScoredBookOut(BookOut):
    score: float
    reason: str


class SimilarBooksResponse(BaseModel):
    book_id: int
    count: int
    results: list[ScoredBookOut]


class RecommendationsResponse(BaseModel):
    count: int
    results: list[ScoredBookOut]
