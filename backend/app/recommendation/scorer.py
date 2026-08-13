"""
Combines semantic similarity (FAISS), genre/author preference match, and
book rating into a single ranked recommendation list for a user.

Cold start: if the user has no wishlist/reading-history signal AND no
stated genre/author preferences, there's nothing to base a
recommendation on — this returns an empty list rather than guessing
(no "popular books" fallback, since that wouldn't be grounded in
anything the user actually told us). The frontend already has an
honest empty state for this.

Note on ordering: Wishlist and ReadingHistory (the CRUD endpoints for
which ship in Phase 9) are the main signal source here. Until a user
has used those features, get_recommendations will only have stated
UserPreference genres/authors to go on, or nothing at all — the scoring
logic itself is complete now and "lights up" automatically as those
signals get populated.
"""

from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.preference import UserPreference
from app.models.reading_history import ReadingHistory
from app.models.user import User
from app.models.wishlist import Wishlist
from app.recommendation import faiss_index

WEIGHT_SEMANTIC = 0.5
WEIGHT_GENRE = 0.2
WEIGHT_AUTHOR = 0.2
WEIGHT_RATING = 0.1

PREFERENCE_CANDIDATE_POOL = 500  # cap on how many books we scan for genre/author matches


def _signal_book_ids(db: Session, user_id: int) -> set[int]:
    """Books the user already has some relationship with — used both to
    build their taste profile and to exclude from new recommendations."""
    wishlist_ids = {w.book_id for w in db.query(Wishlist).filter(Wishlist.user_id == user_id)}
    history_ids = {
        h.book_id for h in db.query(ReadingHistory).filter(ReadingHistory.user_id == user_id)
    }
    return wishlist_ids | history_ids


def _build_taste_vector(signal_ids: set[int]) -> Optional[np.ndarray]:
    if not signal_ids:
        return None

    vectors = [faiss_index.reconstruct(book_id) for book_id in signal_ids]
    vectors = [v for v in vectors if v is not None]
    if not vectors:
        return None

    mean = np.mean(vectors, axis=0)
    norm = np.linalg.norm(mean)
    if norm > 0:
        mean = mean / norm
    return mean.astype("float32")


def _build_reason(semantic: float, genre_score: float, author_score: float) -> str:
    reasons = []
    if semantic > 0.55:
        reasons.append("similar to books on your shelf")
    if genre_score > 0:
        reasons.append("matches your favorite genres")
    if author_score > 0:
        reasons.append("by an author you follow")
    if not reasons:
        return "Recommended for you"
    return "Recommended because it's " + " and ".join(reasons)


def get_recommendations(
    db: Session, user: User, limit: int = 20
) -> list[tuple[Book, float, str]]:
    signal_ids = _signal_book_ids(db, user.id)
    taste_vector = _build_taste_vector(signal_ids)

    preferences = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    favorite_genres = set(preferences.favorite_genres or []) if preferences else set()
    favorite_authors = set(preferences.favorite_authors or []) if preferences else set()

    if taste_vector is None and not favorite_genres and not favorite_authors:
        return []

    semantic_scores: dict[int, float] = {}
    if taste_vector is not None:
        semantic_scores = dict(
            faiss_index.search(taste_vector, k=limit * 3, exclude_ids=signal_ids)
        )

    candidate_ids: set[int] = set(semantic_scores.keys())

    if favorite_genres or favorite_authors:
        pool = (
            db.query(Book)
            .filter(Book.id.notin_(signal_ids))
            .limit(PREFERENCE_CANDIDATE_POOL)
            .all()
        )
        for book in pool:
            if set(book.categories or []) & favorite_genres or set(book.authors or []) & favorite_authors:
                candidate_ids.add(book.id)

    if not candidate_ids:
        return []

    candidates = db.query(Book).filter(Book.id.in_(candidate_ids)).all()

    scored: list[tuple[Book, float, str]] = []
    for book in candidates:
        semantic = semantic_scores.get(book.id, 0.0)
        genre_overlap = len(set(book.categories or []) & favorite_genres)
        genre_score = min(genre_overlap / 2, 1.0)
        author_score = 1.0 if set(book.authors or []) & favorite_authors else 0.0
        rating_score = (book.rating or 0) / 5.0

        total = (
            WEIGHT_SEMANTIC * semantic
            + WEIGHT_GENRE * genre_score
            + WEIGHT_AUTHOR * author_score
            + WEIGHT_RATING * rating_score
        )
        reason = _build_reason(semantic, genre_score, author_score)
        scored.append((book, round(total, 4), reason))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]
