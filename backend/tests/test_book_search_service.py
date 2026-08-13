import pytest

from app.models.book import Book
from app.services import book_search
from app.services.google_books import BookSearchError
from app.services.open_library import OpenLibraryError


@pytest.fixture(autouse=True)
def no_real_embedding(monkeypatch):
    """perform_book_search now embeds newly-upserted books; these tests
    care about search/upsert behavior, not embedding, so replace it with
    a no-op rather than hitting the real (network-dependent) model."""
    monkeypatch.setattr(book_search, "ensure_books_embedded", lambda db, books: None)


def sample_data(**overrides):
    base = {
        "google_books_id": "gb-1",
        "isbn": "9780735211292",
        "title": "Atomic Habits",
        "authors": ["James Clear"],
        "cover_url": "https://example.com/cover.jpg",
        "description": "Good habits, explained.",
        "categories": ["Self-Help"],
        "rating": 4.5,
        "page_count": 320,
        "published_date": "2018-10-16",
        "publisher": "Avery",
        "language": "en",
    }
    base.update(overrides)
    return base


def test_upsert_creates_new_book(db_session):
    book = book_search.upsert_book(db_session, sample_data())
    assert book.id is not None
    assert book.title == "Atomic Habits"
    assert db_session.query(Book).count() == 1


def test_upsert_matches_existing_by_google_books_id(db_session):
    first = book_search.upsert_book(db_session, sample_data())
    second = book_search.upsert_book(db_session, sample_data(rating=4.8))

    assert first.id == second.id
    assert db_session.query(Book).count() == 1
    assert second.rating == 4.8


def test_upsert_matches_existing_by_isbn_when_no_google_id(db_session):
    first = book_search.upsert_book(db_session, sample_data(google_books_id=None))
    # A later hit (e.g. from Open Library) with the same ISBN but no
    # google_books_id should update the same row, not create a duplicate.
    second = book_search.upsert_book(
        db_session, sample_data(google_books_id=None, page_count=325)
    )

    assert first.id == second.id
    assert db_session.query(Book).count() == 1
    assert second.page_count == 325


def test_upsert_does_not_overwrite_fields_with_empty_values(db_session):
    book_search.upsert_book(db_session, sample_data())
    updated = book_search.upsert_book(
        db_session, sample_data(description=None, categories=[])
    )

    assert updated.description == "Good habits, explained."
    assert updated.categories == ["Self-Help"]


def test_perform_search_uses_google_books_when_available(monkeypatch, db_session):
    monkeypatch.setattr(
        book_search, "search_google_books", lambda *a, **k: [sample_data()]
    )
    monkeypatch.setattr(book_search, "search_open_library", lambda *a, **k: [])

    books, source = book_search.perform_book_search(db_session, "atomic habits", "title", 10)

    assert source == "google_books"
    assert len(books) == 1
    assert books[0].title == "Atomic Habits"


def test_perform_search_falls_back_to_open_library_on_error(monkeypatch, db_session):
    def raise_error(*a, **k):
        raise BookSearchError("down")

    monkeypatch.setattr(book_search, "search_google_books", raise_error)
    monkeypatch.setattr(
        book_search,
        "search_open_library",
        lambda *a, **k: [sample_data(google_books_id=None, title="Deep Work")],
    )

    books, source = book_search.perform_book_search(db_session, "deep work", "title", 10)

    assert source == "open_library"
    assert books[0].title == "Deep Work"


def test_perform_search_falls_back_when_google_returns_empty(monkeypatch, db_session):
    monkeypatch.setattr(book_search, "search_google_books", lambda *a, **k: [])
    monkeypatch.setattr(
        book_search, "search_open_library", lambda *a, **k: [sample_data(google_books_id=None)]
    )

    books, source = book_search.perform_book_search(db_session, "atomic habits", "title", 10)
    assert source == "open_library"
    assert len(books) == 1


def test_perform_search_returns_empty_gracefully_when_both_fail(monkeypatch, db_session):
    def raise_book_error(*a, **k):
        raise BookSearchError("down")

    def raise_ol_error(*a, **k):
        raise OpenLibraryError("also down")

    monkeypatch.setattr(book_search, "search_google_books", raise_book_error)
    monkeypatch.setattr(book_search, "search_open_library", raise_ol_error)

    books, source = book_search.perform_book_search(db_session, "atomic habits", "title", 10)
    assert books == []
    assert source == "none"
