"""
Fallback book search using the Open Library API — used automatically
when Google Books has no API key configured, errors, or returns zero
results (see app/services/book_search.py for the orchestration).

Note: Open Library's search endpoint doesn't return book descriptions,
so results from this source will have description=None. That's an
acceptable gap for a fallback provider rather than the primary one.
"""

import requests

OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_COVER = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
REQUEST_TIMEOUT = 8


class OpenLibraryError(Exception):
    """Raised when the Open Library API can't be reached or errors."""


def _build_params(query: str, search_type: str) -> dict:
    query = query.strip()
    if search_type == "isbn":
        return {"isbn": query}
    if search_type == "author":
        return {"author": query}
    if search_type == "title":
        return {"title": query}
    # genre / keyword: Open Library's general search doesn't have a
    # subject-only mode that composes with free text, so both map to `q`.
    return {"q": query}


def search_open_library(query: str, search_type: str = "keyword", max_results: int = 20) -> list[dict]:
    params = _build_params(query, search_type)
    params["limit"] = max(1, min(max_results, 40))

    try:
        resp = requests.get(OPEN_LIBRARY_SEARCH, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise OpenLibraryError(f"Open Library request failed: {exc}") from exc

    docs = resp.json().get("docs", [])
    return [_normalize_doc(doc) for doc in docs]


def _normalize_doc(doc: dict) -> dict:
    isbn_list = doc.get("isbn") or []
    cover_id = doc.get("cover_i")
    cover_url = OPEN_LIBRARY_COVER.format(cover_id=cover_id) if cover_id else None
    publishers = doc.get("publisher") or []
    languages = doc.get("language") or []

    return {
        "google_books_id": None,
        "isbn": isbn_list[0] if isbn_list else None,
        "title": doc.get("title") or "Untitled",
        "authors": doc.get("author_name", []) or [],
        "cover_url": cover_url,
        "description": None,
        "categories": (doc.get("subject") or [])[:5],
        "rating": None,
        "page_count": doc.get("number_of_pages_median"),
        "published_date": str(doc["first_publish_year"]) if doc.get("first_publish_year") else None,
        "publisher": publishers[0] if publishers else None,
        "language": languages[0] if languages else None,
    }
