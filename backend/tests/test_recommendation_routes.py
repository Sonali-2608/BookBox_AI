import numpy as np

from app.models.book import Book
from app.models.recommendation import Recommendation
from app.models.user import User
from app.routes import books as books_routes


def make_book(db, **overrides):
    defaults = dict(title="Book", authors=["Author"], categories=["Fiction"], rating=4.0)
    defaults.update(overrides)
    book = Book(**defaults)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def make_user(db, google_id="g-1", email="reader@example.com"):
    user = User(google_id=google_id, name="Ada Reader", email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers_for(client, monkeypatch, db_session):
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
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def unit_vector(dim, seed):
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype("float32")
    return v / np.linalg.norm(v)


def test_similar_books_404_for_missing_book(client):
    resp = client.get("/api/books/similar/999999")
    assert resp.status_code == 404


def test_similar_books_returns_empty_when_alone_in_index(
    client, db_session, clean_faiss_index, monkeypatch
):
    monkeypatch.setattr(books_routes, "ensure_book_embedded", lambda db, book: None)
    book = make_book(db_session, google_books_id="gb-1")

    # Book was never actually embedded (mocked out above), so reconstruct
    # will find nothing.
    resp = client.get(f"/api/books/similar/{book.id}")

    assert resp.status_code == 200
    assert resp.json()["results"] == []


def test_similar_books_returns_ranked_matches(client, db_session, clean_faiss_index, monkeypatch):
    monkeypatch.setattr(books_routes, "ensure_book_embedded", lambda db, book: None)

    target = make_book(db_session, google_books_id="gb-1", title="Target")
    close = make_book(db_session, google_books_id="gb-2", title="Close Match")
    far = make_book(db_session, google_books_id="gb-3", title="Far Match")

    v_target = unit_vector(384, 1)
    v_close = v_target + np.random.default_rng(2).normal(0, 0.01, 384).astype("float32")
    v_close = v_close / np.linalg.norm(v_close)
    v_far = unit_vector(384, 999)

    clean_faiss_index.add_vectors(
        [target.id, close.id, far.id], np.stack([v_target, v_close, v_far])
    )

    resp = client.get(f"/api/books/similar/{target.id}")

    assert resp.status_code == 200
    body = resp.json()
    result_ids = [r["id"] for r in body["results"]]
    assert target.id not in result_ids  # never recommends itself
    assert result_ids[0] == close.id  # closest match ranked first


def test_recommendations_requires_authentication(client):
    resp = client.get("/api/books/recommendations")
    assert resp.status_code == 401


def test_recommendations_returns_empty_for_cold_start_user(client, db_session, monkeypatch):
    headers = auth_headers_for(client, monkeypatch, db_session)

    resp = client.get("/api/books/recommendations", headers=headers)

    assert resp.status_code == 200
    assert resp.json() == {"count": 0, "results": []}


def test_recommendations_persists_rows_and_replaces_stale_ones(
    client, db_session, monkeypatch, clean_faiss_index
):
    from app.models.preference import UserPreference

    headers = auth_headers_for(client, monkeypatch, db_session)
    user = db_session.query(User).filter(User.email == "reader@example.com").first()

    db_session.add(UserPreference(user_id=user.id, favorite_genres=["Fantasy"], favorite_authors=[]))
    make_book(db_session, google_books_id="gb-1", categories=["Fantasy"])
    db_session.commit()

    # A stale row from a previous computation that should get replaced.
    stale_book = make_book(db_session, google_books_id="gb-stale", categories=["Nonfiction"])
    db_session.add(Recommendation(user_id=user.id, book_id=stale_book.id, score=0.1, reason="old"))
    db_session.commit()

    resp = client.get("/api/books/recommendations", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["count"] == 1

    rows = db_session.query(Recommendation).filter(Recommendation.user_id == user.id).all()
    assert len(rows) == 1
    assert rows[0].book_id != stale_book.id
