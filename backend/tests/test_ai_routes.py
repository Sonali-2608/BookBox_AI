import numpy as np

from app.models.book import Book
from app.routes import ai as ai_routes


def make_book(db, **overrides):
    defaults = dict(
        title="Atomic Habits",
        authors=["James Clear"],
        categories=["Self-Help"],
        description="A guide to good habits.",
    )
    defaults.update(overrides)
    book = Book(**defaults)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def auth_headers_for(client, monkeypatch):
    from app.routes import auth as auth_routes
    from app.services.google_auth import GoogleUserInfo

    monkeypatch.setattr(
        auth_routes,
        "verify_google_token",
        lambda token: GoogleUserInfo(
            google_id="g-1", email="reader@example.com", name="Ada Reader", picture=None
        ),
    )
    resp = client.post("/api/auth/google", json={"id_token": "fake"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def unit_vector(dim, seed):
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype("float32")
    return v / np.linalg.norm(v)


# --- /api/ai/chat ---


def test_chat_requires_authentication(client):
    resp = client.post("/api/ai/chat", json={"message": "hello"})
    assert resp.status_code == 401


def test_chat_rejects_empty_message(client, monkeypatch, db_session):
    headers = auth_headers_for(client, monkeypatch)
    resp = client.post("/api/ai/chat", json={"message": "   "}, headers=headers)
    assert resp.status_code == 400


def test_chat_returns_reply_and_books(client, monkeypatch, db_session, clean_faiss_index):
    headers = auth_headers_for(client, monkeypatch)
    book = make_book(db_session, google_books_id="gb-1")

    v = unit_vector(384, 1)
    clean_faiss_index.add_vectors([book.id], v.reshape(1, -1))

    monkeypatch.setattr(ai_routes, "send_chat_message", lambda db, user, msg: ("Try this!", [book]))

    resp = client.post("/api/ai/chat", json={"message": "habit books"}, headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "Try this!"
    assert body["books"][0]["title"] == "Atomic Habits"


# --- /api/ai/chat/history ---


def test_chat_history_requires_authentication(client):
    resp = client.get("/api/ai/chat/history")
    assert resp.status_code == 401


def test_chat_history_returns_empty_for_new_user(client, monkeypatch, db_session):
    headers = auth_headers_for(client, monkeypatch)
    resp = client.get("/api/ai/chat/history", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"messages": []}


# --- /api/ai/summary/{id} ---


def test_summary_404_for_missing_book(client):
    resp = client.get("/api/ai/summary/999999")
    assert resp.status_code == 404


def test_summary_does_not_require_authentication(client, db_session, monkeypatch):
    book = make_book(db_session, google_books_id="gb-1")
    monkeypatch.setattr(
        ai_routes,
        "get_or_generate_summary",
        lambda db, b: {"summary": "x", "key_takeaways": [], "target_audience": "y"},
    )
    resp = client.get(f"/api/ai/summary/{book.id}")
    assert resp.status_code == 200
    assert resp.json()["summary"] == "x"


# --- /api/ai/why/{id} ---


def test_why_requires_authentication(client, db_session):
    book = make_book(db_session, google_books_id="gb-1")
    resp = client.get(f"/api/ai/why/{book.id}")
    assert resp.status_code == 401


def test_why_404_for_missing_book(client, monkeypatch, db_session):
    headers = auth_headers_for(client, monkeypatch)
    resp = client.get("/api/ai/why/999999", headers=headers)
    assert resp.status_code == 404


def test_why_returns_explanation(client, monkeypatch, db_session):
    headers = auth_headers_for(client, monkeypatch)
    book = make_book(db_session, google_books_id="gb-1")
    monkeypatch.setattr(ai_routes, "get_personalized_explanation", lambda db, user, b: "Because!")

    resp = client.get(f"/api/ai/why/{book.id}", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["explanation"] == "Because!"
