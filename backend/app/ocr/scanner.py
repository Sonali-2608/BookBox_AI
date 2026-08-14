"""
Orchestrates the bookshelf scanner: OpenCV preprocessing -> EasyOCR ->
dedupe/filter candidate titles -> search Google Books (falling back to
Open Library) for each -> score the match with text similarity ->
upsert confident matches into the local catalog (same caching as
Phase 5 search) -> embed them (Phase 6) so they're immediately
available for similarity search and recommendations.

Handles imperfect OCR gracefully: every detected fragment is returned
whether or not it found a confident match, so the frontend can offer
manual correction instead of silently dropping anything.
"""

from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy.orm import Session

from app.models.book import Book
from app.ocr.easyocr_pipeline import detect_text
from app.ocr.preprocessing import InvalidImageError, preprocess_image
from app.recommendation.embedding_pipeline import ensure_books_embedded
from app.services.book_search import upsert_book
from app.services.google_books import BookSearchError, search_google_books
from app.services.open_library import OpenLibraryError, search_open_library

MATCH_CONFIDENCE_THRESHOLD = 0.55
MAX_CANDIDATES = 15  # caps how many OCR fragments we bother searching for


class ScanError(Exception):
    """Raised for invalid/undecodable images."""


def _dedupe_candidates(detections: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for d in sorted(detections, key=lambda x: -x["confidence"]):
        key = d["text"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(d)
    return deduped[:MAX_CANDIDATES]


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _best_book_match(query_text: str) -> tuple[Optional[dict], float]:
    """Searches for query_text and returns (best_matching_book_data,
    similarity) — or (None, 0.0) if nothing came back at all."""
    results: list[dict] = []
    try:
        results = search_google_books(query_text, "keyword", max_results=3)
    except BookSearchError:
        results = []

    if not results:
        try:
            results = search_open_library(query_text, "keyword", max_results=3)
        except OpenLibraryError:
            results = []

    if not results:
        return None, 0.0

    best = max(results, key=lambda r: _text_similarity(query_text, r["title"]))
    return best, _text_similarity(query_text, best["title"])


def scan_bookshelf(db: Session, image_bytes: bytes) -> dict:
    try:
        image = preprocess_image(image_bytes)
    except InvalidImageError as exc:
        raise ScanError(str(exc)) from exc

    detections = detect_text(image)
    candidates = _dedupe_candidates(detections)

    matched = []
    unmatched = []

    for candidate in candidates:
        book_data, similarity = _best_book_match(candidate["text"])
        if book_data and similarity >= MATCH_CONFIDENCE_THRESHOLD:
            book = upsert_book(db, book_data)
            matched.append(
                {
                    "ocr_text": candidate["text"],
                    "ocr_confidence": candidate["confidence"],
                    "match_confidence": round(similarity, 3),
                    "book": book,
                }
            )
        else:
            unmatched.append(candidate["text"])

    if matched:
        ensure_books_embedded(db, [m["book"] for m in matched])

    return {
        "detected_texts": [
            {"text": c["text"], "confidence": c["confidence"]} for c in candidates
        ],
        "matched": matched,
        "unmatched": unmatched,
    }
