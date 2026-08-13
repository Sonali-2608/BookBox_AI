from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Book(Base):
    """
    Local cache of book metadata pulled from Google Books / Open Library.

    We persist books we've seen so we can (a) avoid re-hitting external
    APIs, (b) attach wishlist/reading-history/recommendation rows to a
    stable local id, and (c) know which books already have embeddings
    generated for semantic search (Phase 6).
    """

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    google_books_id = Column(String, unique=True, index=True, nullable=True)
    isbn = Column(String, index=True, nullable=True)

    title = Column(String, nullable=False, index=True)
    authors = Column(JSON, default=list)  # list[str]
    cover_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    categories = Column(JSON, default=list)  # list[str]

    rating = Column(Float, nullable=True)
    page_count = Column(Integer, nullable=True)
    published_date = Column(String, nullable=True)
    publisher = Column(String, nullable=True)
    language = Column(String, nullable=True)

    # Set once a Sentence-Transformers embedding for this book has been
    # computed and added to the FAISS index (Phase 6). We avoid
    # regenerating embeddings for books we've already indexed.
    embedding_generated = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
