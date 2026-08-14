import io

from app.models.book import Book
from app.routes import scanner as scanner_routes


def make_book(**overrides):
    defaults = dict(
        id=1,
        google_books_id="gb-1",
        isbn="9780735211292",
        title="Atomic Habits",
        authors=["James Clear"],
        cover_url=None,
        description=None,
        categories=["Self-Help"],
        rating=None,
        page_count=None,
        published_date=None,
        publisher=None,
        language=None,
    )
    defaults.update(overrides)
    return Book(**defaults)


def test_upload_rejects_unsupported_content_type(client):
    files = {"file": ("book.txt", io.BytesIO(b"not an image"), "text/plain")}
    resp = client.post("/api/scanner/upload", files=files)
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


def test_upload_rejects_empty_file(client):
    files = {"file": ("book.jpg", io.BytesIO(b""), "image/jpeg")}
    resp = client.post("/api/scanner/upload", files=files)
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_upload_rejects_oversized_file(client, monkeypatch):
    monkeypatch.setattr(scanner_routes, "MAX_UPLOAD_BYTES", 10)  # tiny limit for the test
    files = {"file": ("book.jpg", io.BytesIO(b"x" * 100), "image/jpeg")}
    resp = client.post("/api/scanner/upload", files=files)
    assert resp.status_code == 400
    assert "too large" in resp.json()["detail"].lower()


def test_upload_rejects_invalid_image_bytes(client):
    files = {"file": ("book.jpg", io.BytesIO(b"totally not a jpeg"), "image/jpeg")}
    resp = client.post("/api/scanner/upload", files=files)
    assert resp.status_code == 400


def test_upload_returns_scan_results_on_success(client, monkeypatch, db_session):
    book = make_book()

    def fake_scan(db, image_bytes):
        return {
            "detected_texts": [{"text": "Atomic Habits", "confidence": 0.9}],
            "matched": [
                {
                    "ocr_text": "Atomic Habits",
                    "ocr_confidence": 0.9,
                    "match_confidence": 0.95,
                    "book": book,
                }
            ],
            "unmatched": [],
        }

    monkeypatch.setattr(scanner_routes, "scan_bookshelf", fake_scan)

    files = {"file": ("shelf.jpg", io.BytesIO(b"fake-jpeg-bytes"), "image/jpeg")}
    resp = client.post("/api/scanner/upload", files=files)

    assert resp.status_code == 200
    body = resp.json()
    assert body["matched"][0]["book"]["title"] == "Atomic Habits"
    assert body["matched"][0]["match_confidence"] == 0.95
    assert body["unmatched"] == []


def test_upload_returns_unmatched_for_low_confidence_scan(client, monkeypatch):
    def fake_scan(db, image_bytes):
        return {
            "detected_texts": [{"text": "blurry text", "confidence": 0.4}],
            "matched": [],
            "unmatched": ["blurry text"],
        }

    monkeypatch.setattr(scanner_routes, "scan_bookshelf", fake_scan)

    files = {"file": ("shelf.jpg", io.BytesIO(b"fake-jpeg-bytes"), "image/jpeg")}
    resp = client.post("/api/scanner/upload", files=files)

    assert resp.status_code == 200
    body = resp.json()
    assert body["matched"] == []
    assert body["unmatched"] == ["blurry text"]


def test_upload_accepts_png_and_webp_content_types(client, monkeypatch):
    monkeypatch.setattr(
        scanner_routes,
        "scan_bookshelf",
        lambda db, image_bytes: {"detected_texts": [], "matched": [], "unmatched": []},
    )
    for content_type, name in [("image/png", "a.png"), ("image/webp", "a.webp")]:
        files = {"file": (name, io.BytesIO(b"fake-bytes"), content_type)}
        resp = client.post("/api/scanner/upload", files=files)
        assert resp.status_code == 200
