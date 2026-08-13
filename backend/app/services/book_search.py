"""
Orchestrates book search: try Google Books, fall back to Open Library if
it's unavailable or returns nothing, then persist ("upsert") whatever we
found into the local `books` table.

We cache books locally so that (a) book detail pages don't need to
re-hit an external API, (b) wishlist/reading-history/recommendation rows
have a stable local id to point at, and (c) we know which books already
have embeddings generated (Phase 6).
"""

from sqlalchemy.orm import Session

from app.models.book import Book
from app.recommendation.embedding_pipeline import ensure_books_embedded
from app.services.google_books import BookSearchError, search_google_books
from app.services.open_library import OpenLibraryError, search_open_library

UPSERT_FIELDS = [
    "isbn",
    "title",
    "authors",
    "cover_url",
    "description",
    "categories",
    "rating",
    "page_count",
    "published_date",
    "publisher",
    "language",
]


def upsert_book(db: Session, data: dict) -> Book:
    """Find an existing Book by google_books_id (preferred) or isbn, and
    update it with any new non-empty fields; otherwise create one."""
    book = None
    if data.get("google_books_id"):
        book = db.query(Book).filter(Book.google_books_id == data["google_books_id"]).first()
    if book is None and data.get("isbn"):
        book = db.query(Book).filter(Book.isbn == data["isbn"]).first()

    if book is None:
        book = Book(
            google_books_id=data.get("google_books_id"),
            **{field: data.get(field) for field in UPSERT_FIELDS},
        )
        db.add(book)
    else:
        if data.get("google_books_id") and not book.google_books_id:
            book.google_books_id = data["google_books_id"]
        for field in UPSERT_FIELDS:
            value = data.get(field)
            if value not in (None, [], "") and getattr(book, field) != value:
                setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book


def perform_book_search(
    db: Session, query: str, search_type: str, limit: int
) -> tuple[list[Book], str]:
    """Returns (books, source) where source is "google_books",
    "open_library", or "none". Never raises — external API failures
    degrade to an empty result set rather than a 500."""
    normalized: list[dict] = []
    source = "none"

    try:
        normalized = search_google_books(query, search_type, limit)
        if normalized:
            source = "google_books"
    except BookSearchError:
        normalized = []

    if not normalized:
        try:
            normalized = search_open_library(query, search_type, limit)
            if normalized:
                source = "open_library"
        except OpenLibraryError:
            normalized = []

    books = [upsert_book(db, data) for data in normalized]
    ensure_books_embedded(db, books)
    return books, source
