"""
Ensures books have embeddings in the FAISS index. Generates them in a
single batch call and skips any book whose Book.embedding_generated
flag is already set, so the same book is never re-embedded on repeat
searches (see Phase 2's Book model docstring for why that flag exists).
"""

from sqlalchemy.orm import Session

from app.ai.embeddings import build_book_text, embed_texts
from app.models.book import Book
from app.recommendation import faiss_index


def ensure_books_embedded(db: Session, books: list[Book]) -> None:
    pending = [b for b in books if not b.embedding_generated]
    if not pending:
        return

    texts = [
        build_book_text(b.title, b.authors, b.categories, b.description) for b in pending
    ]
    vectors = embed_texts(texts)

    faiss_index.add_vectors([b.id for b in pending], vectors)

    for book in pending:
        book.embedding_generated = 1
    db.commit()


def ensure_book_embedded(db: Session, book: Book) -> None:
    ensure_books_embedded(db, [book])
