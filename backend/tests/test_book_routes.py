from app.models.book import Book
from app.routes import books as books_routes


def sample_book_row(db_session, **overrides):
    defaults = dict(
        google_books_id="gb-1",
        isbn="9780735211292",
        title="Atomic Habits",
        authors=["James Clear"],
        cover_url="https://example.com/cover.jpg",
        description="Good habits, explained.",
        categories=["Self-Help"],
        rating=4.5,
        page_count=320,
        published_date="2018-10-16",
        publisher="Avery",
        language="en",
    )
    defaults.update(overrides)
    book = Book(**defaults)
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


def test_search_rejects_invalid_search_type(client):
    resp = client.get("/api/books/search", params={"q": "habits", "search_type": "bogus"})
    assert resp.status_code == 400


def test_search_requires_query_param(client):
    resp = client.get("/api/books/search")
    assert resp.status_code == 422


def test_search_returns_results_from_google_books(client, monkeypatch):
    fake_book_data = {
        "google_books_id": "gb-42",
        "isbn": "111",
        "title": "Deep Work",
        "authors": ["Cal Newport"],
        "cover_url": None,
        "description": None,
        "categories": [],
        "rating": None,
        "page_count": None,
        "published_date": None,
        "publisher": None,
        "language": None,
    }
    monkeypatch.setattr(
        books_routes,
        "perform_book_search",
        lambda db, q, t, limit: (
            [Book(id=1, **fake_book_data)],
            "google_books",
        ),
    )

    resp = client.get("/api/books/search", params={"q": "deep work", "search_type": "title"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "google_books"
    assert body["count"] == 1
    assert body["results"][0]["title"] == "Deep Work"


def test_search_returns_empty_gracefully(client, monkeypatch):
    monkeypatch.setattr(books_routes, "perform_book_search", lambda db, q, t, limit: ([], "none"))

    resp = client.get("/api/books/search", params={"q": "asdkjaskldjaslkd", "search_type": "keyword"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["results"] == []
    assert body["source"] == "none"


def test_get_book_by_id_returns_book(client, db_session):
    book = sample_book_row(db_session)

    resp = client.get(f"/api/books/{book.id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Atomic Habits"
    assert body["authors"] == ["James Clear"]


def test_get_book_by_id_404_when_missing(client):
    resp = client.get("/api/books/999999")
    assert resp.status_code == 404
