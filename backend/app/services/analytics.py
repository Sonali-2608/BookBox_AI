"""
Computes reading analytics for a user directly from their ReadingHistory
and Wishlist rows — there's no separate analytics table, everything is
derived fresh from data that's already tracked elsewhere.
"""

from collections import Counter
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.reading_history import ReadingHistory, ReadingStatus
from app.models.wishlist import Wishlist


def compute_analytics(db: Session, user_id: int) -> dict:
    history = db.query(ReadingHistory).filter(ReadingHistory.user_id == user_id).all()
    wishlist_count = db.query(Wishlist).filter(Wishlist.user_id == user_id).count()

    completed = [h for h in history if h.status == ReadingStatus.completed]
    reading = [h for h in history if h.status == ReadingStatus.reading]
    tracked_want_to_read = [h for h in history if h.status == ReadingStatus.want_to_read]

    genre_counter: Counter = Counter()
    author_counter: Counter = Counter()
    for h in history:
        if not h.book:
            continue
        for genre in h.book.categories or []:
            genre_counter[genre] += 1
        for author in h.book.authors or []:
            author_counter[author] += 1

    return {
        "books_completed": len(completed),
        "currently_reading": len(reading),
        "want_to_read": wishlist_count + len(tracked_want_to_read),
        "favorite_genres": [
            {"name": name, "count": count} for name, count in genre_counter.most_common(5)
        ],
        "favorite_authors": [
            {"name": name, "count": count} for name, count in author_counter.most_common(5)
        ],
        "monthly_activity": _monthly_completion_counts(completed),
        "reading_streak_days": _reading_streak_days(completed),
    }


def _monthly_completion_counts(completed: list[ReadingHistory]) -> list[dict]:
    counter: Counter = Counter()
    for h in completed:
        if h.completed_at:
            counter[h.completed_at.strftime("%Y-%m")] += 1
    return [{"month": month, "completed": count} for month, count in sorted(counter.items())]


def _reading_streak_days(completed: list[ReadingHistory]) -> int:
    """Consecutive days, ending today, with at least one book marked
    completed. This tracks completion-logging consistency, not daily
    reading time — we don't have data for the latter."""
    completion_dates = {h.completed_at.date() for h in completed if h.completed_at}
    if not completion_dates:
        return 0

    streak = 0
    day = date.today()
    while day in completion_dates:
        streak += 1
        day -= timedelta(days=1)
    return streak
