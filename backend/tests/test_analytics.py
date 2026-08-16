from datetime import datetime, timedelta, timezone

from app.models.book import Book
from app.models.reading_history import ReadingHistory, ReadingStatus
from app.models.user import User
from app.models.wishlist import Wishlist
from app.services.analytics import compute_analytics


def make_user(db, google_id="g-1", email="reader@example.com"):
    user = User(google_id=google_id, name="Ada Reader", email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_book(db, **overrides):
    defaults = dict(title="Book", authors=["Author"], categories=["Fiction"])
    defaults.update(overrides)
    book = Book(**defaults)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def test_analytics_all_zero_for_new_user(db_session):
    user = make_user(db_session)
    result = compute_analytics(db_session, user.id)

    assert result["books_completed"] == 0
    assert result["currently_reading"] == 0
    assert result["want_to_read"] == 0
    assert result["favorite_genres"] == []
    assert result["favorite_authors"] == []
    assert result["monthly_activity"] == []
    assert result["reading_streak_days"] == 0


def test_analytics_counts_by_status(db_session):
    user = make_user(db_session)
    completed_book = make_book(db_session, google_books_id="gb-1")
    reading_book = make_book(db_session, google_books_id="gb-2")
    wishlisted_book = make_book(db_session, google_books_id="gb-3")

    db_session.add(
        ReadingHistory(
            user_id=user.id,
            book_id=completed_book.id,
            status=ReadingStatus.completed,
            completed_at=datetime.now(timezone.utc),
        )
    )
    db_session.add(
        ReadingHistory(user_id=user.id, book_id=reading_book.id, status=ReadingStatus.reading)
    )
    db_session.add(Wishlist(user_id=user.id, book_id=wishlisted_book.id))
    db_session.commit()

    result = compute_analytics(db_session, user.id)

    assert result["books_completed"] == 1
    assert result["currently_reading"] == 1
    assert result["want_to_read"] == 1


def test_analytics_favorite_genres_and_authors_by_frequency(db_session):
    user = make_user(db_session)
    b1 = make_book(db_session, google_books_id="gb-1", categories=["Fantasy"], authors=["A"])
    b2 = make_book(db_session, google_books_id="gb-2", categories=["Fantasy"], authors=["B"])
    b3 = make_book(db_session, google_books_id="gb-3", categories=["Biography"], authors=["A"])

    for b in (b1, b2, b3):
        db_session.add(
            ReadingHistory(user_id=user.id, book_id=b.id, status=ReadingStatus.reading)
        )
    db_session.commit()

    result = compute_analytics(db_session, user.id)

    assert result["favorite_genres"][0] == {"name": "Fantasy", "count": 2}
    assert result["favorite_authors"][0] == {"name": "A", "count": 2}


def test_analytics_monthly_activity_groups_by_completion_month(db_session):
    user = make_user(db_session)
    b1 = make_book(db_session, google_books_id="gb-1")
    b2 = make_book(db_session, google_books_id="gb-2")

    db_session.add(
        ReadingHistory(
            user_id=user.id,
            book_id=b1.id,
            status=ReadingStatus.completed,
            completed_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
    )
    db_session.add(
        ReadingHistory(
            user_id=user.id,
            book_id=b2.id,
            status=ReadingStatus.completed,
            completed_at=datetime(2026, 1, 20, tzinfo=timezone.utc),
        )
    )
    db_session.commit()

    result = compute_analytics(db_session, user.id)
    assert result["monthly_activity"] == [{"month": "2026-01", "completed": 2}]


def test_reading_streak_counts_consecutive_days_ending_today(db_session):
    user = make_user(db_session)
    today = datetime.now(timezone.utc)

    for days_ago in range(3):
        book = make_book(db_session, google_books_id=f"gb-{days_ago}")
        db_session.add(
            ReadingHistory(
                user_id=user.id,
                book_id=book.id,
                status=ReadingStatus.completed,
                completed_at=today - timedelta(days=days_ago),
            )
        )
    db_session.commit()

    result = compute_analytics(db_session, user.id)
    assert result["reading_streak_days"] == 3


def test_reading_streak_breaks_on_gap(db_session):
    user = make_user(db_session)
    today = datetime.now(timezone.utc)

    recent_book = make_book(db_session, google_books_id="gb-recent")
    old_book = make_book(db_session, google_books_id="gb-old")

    db_session.add(
        ReadingHistory(
            user_id=user.id,
            book_id=recent_book.id,
            status=ReadingStatus.completed,
            completed_at=today,
        )
    )
    db_session.add(
        ReadingHistory(
            user_id=user.id,
            book_id=old_book.id,
            status=ReadingStatus.completed,
            completed_at=today - timedelta(days=5),  # gap before this
        )
    )
    db_session.commit()

    result = compute_analytics(db_session, user.id)
    assert result["reading_streak_days"] == 1
