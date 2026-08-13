"""
Thin client for the Google Books API. Normalizes results into the same
shape as our Book model so callers don't care which provider a result
came from (see also app/services/open_library.py, the fallback).
"""

from typing import Optional

import requests

from app.config import settings

GOOGLE_BOOKS_BASE = "https://www.googleapis.com/books/v1/volumes"
REQUEST_TIMEOUT = 8


class BookSearchError(Exception):
    """Raised when the Google Books API can't be reached or errors."""


def _build_query(query: str, search_type: str) -> str:
    query = query.strip()
    if search_type == "isbn":
        return f"isbn:{query}"
    if search_type == "author":
        return f"inauthor:{query}"
    if search_type == "genre":
        return f"subject:{query}"
    if search_type == "title":
        return f"intitle:{query}"
    return query  # keyword / free-text


def search_google_books(query: str, search_type: str = "keyword", max_results: int = 20) -> list[dict]:
    """Returns [] (rather than raising) if no API key is configured, so
    callers can fall back to Open Library without special-casing this."""
    if not settings.GOOGLE_BOOKS_API_KEY:
        return []

    params = {
        "q": _build_query(query, search_type),
        "maxResults": max(1, min(max_results, 40)),
        "key": settings.GOOGLE_BOOKS_API_KEY,
    }
    try:
        resp = requests.get(GOOGLE_BOOKS_BASE, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise BookSearchError(f"Google Books request failed: {exc}") from exc

    items = resp.json().get("items", [])
    return [_normalize_item(item) for item in items]


def get_google_book_by_volume_id(volume_id: str) -> Optional[dict]:
    if not settings.GOOGLE_BOOKS_API_KEY:
        return None

    url = f"{GOOGLE_BOOKS_BASE}/{volume_id}"
    try:
        resp = requests.get(url, params={"key": settings.GOOGLE_BOOKS_API_KEY}, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise BookSearchError(f"Google Books request failed: {exc}") from exc

    return _normalize_item(resp.json())


def _normalize_item(item: dict) -> dict:
    info = item.get("volumeInfo", {}) or {}

    isbn = None
    for identifier in info.get("industryIdentifiers", []) or []:
        if identifier.get("type") == "ISBN_13":
            isbn = identifier.get("identifier")
            break
        if identifier.get("type") == "ISBN_10" and isbn is None:
            isbn = identifier.get("identifier")

    image_links = info.get("imageLinks", {}) or {}
    cover_url = image_links.get("thumbnail") or image_links.get("smallThumbnail")
    # Google serves cover URLs over http by default; force https so the
    # frontend never triggers mixed-content blocking.
    if cover_url and cover_url.startswith("http://"):
        cover_url = "https://" + cover_url[len("http://"):]

    return {
        "google_books_id": item.get("id"),
        "isbn": isbn,
        "title": info.get("title") or "Untitled",
        "authors": info.get("authors", []) or [],
        "cover_url": cover_url,
        "description": info.get("description"),
        "categories": info.get("categories", []) or [],
        "rating": info.get("averageRating"),
        "page_count": info.get("pageCount"),
        "published_date": info.get("publishedDate"),
        "publisher": info.get("publisher"),
        "language": info.get("language"),
    }
