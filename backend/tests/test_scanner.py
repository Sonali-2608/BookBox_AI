import numpy as np

from app.models.book import Book
from app.ocr import scanner


def sample_book_data(**overrides):
    base = {
        "google_books_id": "gb-1",
        "isbn": "9780735211292",
        "title": "Atomic Habits",
        "authors": ["James Clear"],
        "cover_url": None,
        "description": None,
        "categories": ["Self-Help"],
        "rating": None,
        "page_count": None,
        "published_date": None,
        "publisher": None,
        "language": None,
    }
    base.update(overrides)
    return base


def test_dedupe_removes_case_insensitive_duplicates():
    detections = [
        {"text": "Atomic Habits", "confidence": 0.9},
        {"text": "ATOMIC HABITS", "confidence": 0.7},
        {"text": "Deep Work", "confidence": 0.8},
    ]
    result = scanner._dedupe_candidates(detections)
    assert len(result) == 2
    assert result[0]["text"] == "Atomic Habits"  # higher confidence kept


def test_dedupe_caps_at_max_candidates():
    detections = [{"text": f"Book {i}", "confidence": 0.9} for i in range(30)]
    result = scanner._dedupe_candidates(detections)
    assert len(result) == scanner.MAX_CANDIDATES


def test_text_similarity_identical_is_one():
    assert scanner._text_similarity("Atomic Habits", "Atomic Habits") == 1.0


def test_text_similarity_case_insensitive():
    assert scanner._text_similarity("atomic habits", "ATOMIC HABITS") == 1.0


def test_text_similarity_completely_different_is_low():
    assert scanner._text_similarity("Atomic Habits", "xyz123") < 0.3


def test_scan_bookshelf_matches_confident_detection(db_session, clean_faiss_index, monkeypatch):
    monkeypatch.setattr(scanner, "preprocess_image", lambda image_bytes: "fake-image-array")
    monkeypatch.setattr(
        scanner, "detect_text", lambda image: [{"text": "Atomic Habits", "confidence": 0.9}]
    )
    monkeypatch.setattr(scanner, "search_google_books", lambda *a, **k: [sample_book_data()])
    monkeypatch.setattr(scanner, "search_open_library", lambda *a, **k: [])
    monkeypatch.setattr(
        scanner,
        "ensure_books_embedded",
        lambda db, books: None,
    )

    result = scanner.scan_bookshelf(db_session, b"fake-bytes")

    assert len(result["matched"]) == 1
    assert result["matched"][0]["ocr_text"] == "Atomic Habits"
    assert result["matched"][0]["book"].title == "Atomic Habits"
    assert result["unmatched"] == []
    assert db_session.query(Book).count() == 1


def test_scan_bookshelf_leaves_low_similarity_as_unmatched(
    db_session, clean_faiss_index, monkeypatch
):
    monkeypatch.setattr(scanner, "preprocess_image", lambda image_bytes: "fake-image-array")
    monkeypatch.setattr(
        scanner, "detect_text", lambda image: [{"text": "asdkjaslkdj", "confidence": 0.9}]
    )
    # Google Books returns something, but it doesn't textually resemble
    # the OCR fragment at all — should NOT be treated as a match.
    monkeypatch.setattr(
        scanner,
        "search_google_books",
        lambda *a, **k: [sample_book_data(title="Completely Unrelated Title")],
    )
    monkeypatch.setattr(scanner, "search_open_library", lambda *a, **k: [])

    result = scanner.scan_bookshelf(db_session, b"fake-bytes")

    assert result["matched"] == []
    assert result["unmatched"] == ["asdkjaslkdj"]
    assert db_session.query(Book).count() == 0  # never upserted a bad match


def test_scan_bookshelf_handles_no_search_results_gracefully(
    db_session, clean_faiss_index, monkeypatch
):
    monkeypatch.setattr(scanner, "preprocess_image", lambda image_bytes: "fake-image-array")
    monkeypatch.setattr(
        scanner, "detect_text", lambda image: [{"text": "Some Title", "confidence": 0.9}]
    )
    monkeypatch.setattr(scanner, "search_google_books", lambda *a, **k: [])
    monkeypatch.setattr(scanner, "search_open_library", lambda *a, **k: [])

    result = scanner.scan_bookshelf(db_session, b"fake-bytes")

    assert result["matched"] == []
    assert result["unmatched"] == ["Some Title"]


def test_scan_bookshelf_raises_scan_error_for_invalid_image(db_session, clean_faiss_index):
    result_or_error = None
    try:
        scanner.scan_bookshelf(db_session, b"not a real image")
        result_or_error = "no error raised"
    except scanner.ScanError:
        result_or_error = "raised"
    assert result_or_error == "raised"


def test_scan_bookshelf_embeds_matched_books(db_session, clean_faiss_index, monkeypatch):
    monkeypatch.setattr(scanner, "preprocess_image", lambda image_bytes: "fake-image-array")
    monkeypatch.setattr(
        scanner, "detect_text", lambda image: [{"text": "Atomic Habits", "confidence": 0.9}]
    )
    monkeypatch.setattr(scanner, "search_google_books", lambda *a, **k: [sample_book_data()])
    monkeypatch.setattr(scanner, "search_open_library", lambda *a, **k: [])

    def fake_embed_texts(texts):
        rng = np.random.default_rng(0)
        return rng.random((len(texts), 384)).astype("float32")

    monkeypatch.setattr("app.recommendation.embedding_pipeline.embed_texts", fake_embed_texts)

    result = scanner.scan_bookshelf(db_session, b"fake-bytes")

    book = result["matched"][0]["book"]
    db_session.refresh(book)
    assert book.embedding_generated == 1
