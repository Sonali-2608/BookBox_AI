import requests

from app.services import google_books


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


GOOGLE_ITEM = {
    "id": "abc123",
    "volumeInfo": {
        "title": "Atomic Habits",
        "authors": ["James Clear"],
        "publisher": "Avery",
        "publishedDate": "2018-10-16",
        "description": "A guide to building good habits.",
        "industryIdentifiers": [
            {"type": "ISBN_10", "identifier": "0735211299"},
            {"type": "ISBN_13", "identifier": "9780735211292"},
        ],
        "pageCount": 320,
        "categories": ["Self-Help"],
        "averageRating": 4.5,
        "imageLinks": {"thumbnail": "http://books.google.com/cover.jpg"},
        "language": "en",
    },
}


def test_search_returns_empty_without_api_key(monkeypatch):
    monkeypatch.setattr(google_books.settings, "GOOGLE_BOOKS_API_KEY", None)
    assert google_books.search_google_books("atomic habits") == []


def test_search_normalizes_results(monkeypatch):
    monkeypatch.setattr(google_books.settings, "GOOGLE_BOOKS_API_KEY", "fake-key")
    monkeypatch.setattr(
        google_books.requests, "get", lambda *a, **k: FakeResponse({"items": [GOOGLE_ITEM]})
    )

    results = google_books.search_google_books("atomic habits", "title")

    assert len(results) == 1
    book = results[0]
    assert book["google_books_id"] == "abc123"
    assert book["title"] == "Atomic Habits"
    assert book["authors"] == ["James Clear"]
    assert book["isbn"] == "9780735211292"  # prefers ISBN_13
    assert book["cover_url"] == "https://books.google.com/cover.jpg"  # forced https
    assert book["page_count"] == 320
    assert book["rating"] == 4.5


def test_search_handles_missing_fields_gracefully(monkeypatch):
    monkeypatch.setattr(google_books.settings, "GOOGLE_BOOKS_API_KEY", "fake-key")
    sparse_item = {"id": "xyz", "volumeInfo": {}}
    monkeypatch.setattr(
        google_books.requests, "get", lambda *a, **k: FakeResponse({"items": [sparse_item]})
    )

    results = google_books.search_google_books("mystery")
    assert results[0]["title"] == "Untitled"
    assert results[0]["authors"] == []
    assert results[0]["isbn"] is None


def test_search_raises_book_search_error_on_network_failure(monkeypatch):
    monkeypatch.setattr(google_books.settings, "GOOGLE_BOOKS_API_KEY", "fake-key")

    def raise_connection_error(*a, **k):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(google_books.requests, "get", raise_connection_error)

    try:
        google_books.search_google_books("atomic habits")
        assert False, "expected BookSearchError"
    except google_books.BookSearchError:
        pass


def test_search_raises_on_http_error_status(monkeypatch):
    monkeypatch.setattr(google_books.settings, "GOOGLE_BOOKS_API_KEY", "fake-key")
    monkeypatch.setattr(
        google_books.requests, "get", lambda *a, **k: FakeResponse({}, status_code=500)
    )

    try:
        google_books.search_google_books("atomic habits")
        assert False, "expected BookSearchError"
    except google_books.BookSearchError:
        pass


def test_get_by_volume_id_returns_none_for_404(monkeypatch):
    monkeypatch.setattr(google_books.settings, "GOOGLE_BOOKS_API_KEY", "fake-key")
    monkeypatch.setattr(
        google_books.requests, "get", lambda *a, **k: FakeResponse({}, status_code=404)
    )

    assert google_books.get_google_book_by_volume_id("nonexistent") is None


def test_isbn_query_uses_isbn_prefix():
    assert google_books._build_query("9780735211292", "isbn") == "isbn:9780735211292"


def test_author_query_uses_inauthor_prefix():
    assert google_books._build_query("James Clear", "author") == "inauthor:James Clear"


def test_keyword_query_is_passed_through():
    assert google_books._build_query("habits", "keyword") == "habits"
