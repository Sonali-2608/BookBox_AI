import pytest
from sqlalchemy.exc import IntegrityError

from app.models.book import Book
from app.models.preference import PreferredLength, ReadingFrequency, UserPreference
from app.models.reading_history import ReadingHistory, ReadingStatus
from app.models.user import User
from app.models.wishlist import Wishlist


def make_user(db, google_id="g-1", email="reader@example.com"):
    user = User(google_id=google_id, name="Ada Reader", email=email, profile_image=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_book(db, title="Atomic Habits", google_books_id="gb-1"):
    book = Book(
        google_books_id=google_books_id,
        title=title,
        authors=["James Clear"],
        categories=["Self Help"],
        page_count=320,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def test_create_user(db_session):
    user = make_user(db_session)
    assert user.id is not None
    assert user.role.value == "user"
    assert user.created_at is not None


def test_user_email_must_be_unique(db_session):
    make_user(db_session, google_id="g-1", email="dup@example.com")
    with pytest.raises(IntegrityError):
        make_user(db_session, google_id="g-2", email="dup@example.com")


def test_user_preference_relationship(db_session):
    user = make_user(db_session, google_id="g-3", email="prefs@example.com")
    pref = UserPreference(
        user_id=user.id,
        favorite_genres=["Fantasy", "Sci-Fi"],
        favorite_authors=["Brandon Sanderson"],
        reading_frequency=ReadingFrequency.weekly,
        preferred_length=PreferredLength.medium,
        onboarding_completed=True,
    )
    db_session.add(pref)
    db_session.commit()
    db_session.refresh(user)

    assert user.preferences.favorite_genres == ["Fantasy", "Sci-Fi"]
    assert user.preferences.onboarding_completed is True


def test_wishlist_prevents_duplicate_book_per_user(db_session):
    user = make_user(db_session, google_id="g-4", email="wishlist@example.com")
    book = make_book(db_session)

    db_session.add(Wishlist(user_id=user.id, book_id=book.id))
    db_session.commit()

    db_session.add(Wishlist(user_id=user.id, book_id=book.id))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_reading_history_status_transitions(db_session):
    user = make_user(db_session, google_id="g-5", email="reading@example.com")
    book = make_book(db_session, title="Deep Work", google_books_id="gb-2")

    entry = ReadingHistory(user_id=user.id, book_id=book.id, status=ReadingStatus.want_to_read)
    db_session.add(entry)
    db_session.commit()

    entry.status = ReadingStatus.reading
    db_session.commit()
    db_session.refresh(entry)
    assert entry.status == ReadingStatus.reading
