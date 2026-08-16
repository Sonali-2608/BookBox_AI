from app.models.book import Book
from app.models.reading_history import ReadingHistory, ReadingStatus
from app.models.wishlist import Wishlist


def make_book(db, **overrides):
    defaults = dict(title="Atomic Habits", authors=["James Clear"], categories=["Self-Help"])
    defaults.update(overrides)
    book = Book(**defaults)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def auth_headers(client, monkeypatch, email="reader@example.com", google_id="g-1"):
    from app.routes import auth as auth_routes
    from app.services.google_auth import GoogleUserInfo

    monkeypatch.setattr(
        auth_routes,
        "verify_google_token",
        lambda token: GoogleUserInfo(
            google_id=google_id, email=email, name="Ada Reader", picture=None
        ),
    )
    resp = client.post("/api/auth/google", json={"id_token": "fake"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# --- Wishlist ---


def test_wishlist_requires_authentication(client):
    assert client.get("/api/books/wishlist").status_code == 401
    assert client.post("/api/books/wishlist", json={"book_id": 1}).status_code == 401
    assert client.delete("/api/books/wishlist/1").status_code == 401


def test_add_to_wishlist_404_for_missing_book(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    resp = client.post("/api/books/wishlist", json={"book_id": 999999}, headers=headers)
    assert resp.status_code == 404


def test_add_and_view_wishlist(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)

    add_resp = client.post("/api/books/wishlist", json={"book_id": book.id}, headers=headers)
    assert add_resp.status_code == 201
    assert add_resp.json()["book"]["title"] == "Atomic Habits"

    list_resp = client.get("/api/books/wishlist", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["count"] == 1


def test_add_to_wishlist_is_idempotent(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)

    client.post("/api/books/wishlist", json={"book_id": book.id}, headers=headers)
    client.post("/api/books/wishlist", json={"book_id": book.id}, headers=headers)

    assert db_session.query(Wishlist).count() == 1


def test_remove_from_wishlist(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)
    client.post("/api/books/wishlist", json={"book_id": book.id}, headers=headers)

    resp = client.delete(f"/api/books/wishlist/{book.id}", headers=headers)
    assert resp.status_code == 204
    assert db_session.query(Wishlist).count() == 0


def test_remove_from_wishlist_404_when_not_present(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)
    resp = client.delete(f"/api/books/wishlist/{book.id}", headers=headers)
    assert resp.status_code == 404


def test_wishlist_is_scoped_per_user(client, monkeypatch, db_session):
    headers_a = auth_headers(client, monkeypatch, email="a@example.com", google_id="g-a")
    book = make_book(db_session)
    client.post("/api/books/wishlist", json={"book_id": book.id}, headers=headers_a)

    headers_b = auth_headers(client, monkeypatch, email="b@example.com", google_id="g-b")
    resp = client.get("/api/books/wishlist", headers=headers_b)
    assert resp.json()["count"] == 0


# --- Reading status ---


def test_reading_status_requires_authentication(client):
    assert client.get("/api/books/reading-status").status_code == 401
    assert client.put("/api/books/reading-status", json={"book_id": 1, "status": "reading"}).status_code == 401


def test_set_reading_status_rejects_invalid_status(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)
    resp = client.put(
        "/api/books/reading-status",
        json={"book_id": book.id, "status": "bogus"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_set_reading_status_404_for_missing_book(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    resp = client.put(
        "/api/books/reading-status",
        json={"book_id": 999999, "status": "reading"},
        headers=headers,
    )
    assert resp.status_code == 404


def test_set_reading_status_to_reading_sets_started_at(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)

    resp = client.put(
        "/api/books/reading-status",
        json={"book_id": book.id, "status": "reading"},
        headers=headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "reading"
    assert body["started_at"] is not None
    assert body["completed_at"] is None


def test_set_reading_status_to_completed_sets_completed_at(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)

    resp = client.put(
        "/api/books/reading-status",
        json={"book_id": book.id, "status": "completed"},
        headers=headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["completed_at"] is not None


def test_moving_to_reading_removes_wishlist_entry(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)
    client.post("/api/books/wishlist", json={"book_id": book.id}, headers=headers)
    assert db_session.query(Wishlist).count() == 1

    client.put(
        "/api/books/reading-status",
        json={"book_id": book.id, "status": "reading"},
        headers=headers,
    )

    assert db_session.query(Wishlist).count() == 0
    entry = db_session.query(ReadingHistory).filter(ReadingHistory.book_id == book.id).first()
    assert entry.status == ReadingStatus.reading


def test_moving_back_to_want_to_read_clears_completed_at(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)
    client.put(
        "/api/books/reading-status",
        json={"book_id": book.id, "status": "completed"},
        headers=headers,
    )

    resp = client.put(
        "/api/books/reading-status",
        json={"book_id": book.id, "status": "want_to_read"},
        headers=headers,
    )

    assert resp.json()["completed_at"] is None


def test_get_reading_history_filters_by_status(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    b1 = make_book(db_session, google_books_id="gb-1")
    b2 = make_book(db_session, google_books_id="gb-2")
    client.put(
        "/api/books/reading-status", json={"book_id": b1.id, "status": "reading"}, headers=headers
    )
    client.put(
        "/api/books/reading-status",
        json={"book_id": b2.id, "status": "completed"},
        headers=headers,
    )

    resp = client.get("/api/books/reading-status?status=completed", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 1
    assert resp.json()["items"][0]["book"]["id"] == b2.id


def test_get_reading_history_rejects_invalid_status_filter(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    resp = client.get("/api/books/reading-status?status=bogus", headers=headers)
    assert resp.status_code == 400


def test_remove_reading_status(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)
    client.put(
        "/api/books/reading-status", json={"book_id": book.id, "status": "reading"}, headers=headers
    )

    resp = client.delete(f"/api/books/reading-status/{book.id}", headers=headers)
    assert resp.status_code == 204
    assert db_session.query(ReadingHistory).count() == 0


def test_remove_reading_status_404_when_not_tracked(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    book = make_book(db_session)
    resp = client.delete(f"/api/books/reading-status/{book.id}", headers=headers)
    assert resp.status_code == 404
