import requests

from app.services import open_library


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


OL_DOC = {
    "title": "Deep Work",
    "author_name": ["Cal Newport"],
    "isbn": ["9781455586691"],
    "cover_i": 12345,
    "subject": ["Self-improvement", "Productivity"],
    "number_of_pages_median": 296,
    "first_publish_year": 2016,
    "publisher": ["Grand Central Publishing"],
    "language": ["eng"],
}


def test_search_normalizes_open_library_doc(monkeypatch):
    monkeypatch.setattr(
        open_library.requests, "get", lambda *a, **k: FakeResponse({"docs": [OL_DOC]})
    )

    results = open_library.search_open_library("deep work", "title")

    assert len(results) == 1
    book = results[0]
    assert book["title"] == "Deep Work"
    assert book["authors"] == ["Cal Newport"]
    assert book["isbn"] == "9781455586691"
    assert book["cover_url"] == "https://covers.openlibrary.org/b/id/12345-L.jpg"
    assert book["description"] is None  # OL search doesn't return descriptions
    assert book["google_books_id"] is None
    assert book["published_date"] == "2016"


def test_search_handles_sparse_doc(monkeypatch):
    monkeypatch.setattr(
        open_library.requests, "get", lambda *a, **k: FakeResponse({"docs": [{}]})
    )

    results = open_library.search_open_library("something")
    assert results[0]["title"] == "Untitled"
    assert results[0]["cover_url"] is None
    assert results[0]["isbn"] is None


def test_search_raises_open_library_error_on_failure(monkeypatch):
    def raise_error(*a, **k):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(open_library.requests, "get", raise_error)

    try:
        open_library.search_open_library("deep work")
        assert False, "expected OpenLibraryError"
    except open_library.OpenLibraryError:
        pass


def test_isbn_search_uses_isbn_param():
    assert open_library._build_params("9781455586691", "isbn") == {"isbn": "9781455586691"}


def test_author_search_uses_author_param():
    assert open_library._build_params("Cal Newport", "author") == {"author": "Cal Newport"}
