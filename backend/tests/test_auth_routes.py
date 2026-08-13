from app.models.user import User
from app.routes import auth as auth_routes
from app.services.google_auth import GoogleUserInfo


def mock_google_user(**overrides) -> GoogleUserInfo:
    base = GoogleUserInfo(
        google_id="google-sub-123",
        email="reader@example.com",
        name="Ada Reader",
        picture="https://example.com/pic.jpg",
    )
    base.update(overrides)
    return base


def test_google_login_creates_new_user(client, db_session, monkeypatch):
    monkeypatch.setattr(auth_routes, "verify_google_token", lambda token: mock_google_user())

    resp = client.post("/api/auth/google", json={"id_token": "fake-token"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "reader@example.com"
    assert body["user"]["name"] == "Ada Reader"

    user = db_session.query(User).filter(User.google_id == "google-sub-123").first()
    assert user is not None
    assert user.email == "reader@example.com"


def test_google_login_reuses_existing_user_no_duplicate(client, db_session, monkeypatch):
    monkeypatch.setattr(auth_routes, "verify_google_token", lambda token: mock_google_user())

    first = client.post("/api/auth/google", json={"id_token": "fake-token"})
    second = client.post("/api/auth/google", json={"id_token": "fake-token-again"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["user"]["id"] == second.json()["user"]["id"]

    count = db_session.query(User).filter(User.google_id == "google-sub-123").count()
    assert count == 1


def test_google_login_updates_stale_profile_info(client, db_session, monkeypatch):
    monkeypatch.setattr(auth_routes, "verify_google_token", lambda token: mock_google_user())
    client.post("/api/auth/google", json={"id_token": "fake-token"})

    monkeypatch.setattr(
        auth_routes, "verify_google_token", lambda token: mock_google_user(name="Ada R. Bookworm")
    )
    resp = client.post("/api/auth/google", json={"id_token": "fake-token-2"})

    assert resp.status_code == 200
    assert resp.json()["user"]["name"] == "Ada R. Bookworm"


def test_google_login_invalid_token_rejected(client, monkeypatch):
    def raise_invalid(token):
        from app.services.google_auth import InvalidGoogleTokenError

        raise InvalidGoogleTokenError("Invalid Google ID token: bad signature")

    monkeypatch.setattr(auth_routes, "verify_google_token", raise_invalid)

    resp = client.post("/api/auth/google", json={"id_token": "garbage"})
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_rejects_garbage_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_me_returns_current_user_with_valid_token(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "verify_google_token", lambda token: mock_google_user())
    login_resp = client.post("/api/auth/google", json={"id_token": "fake-token"})
    token = login_resp.json()["access_token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert resp.json()["email"] == "reader@example.com"


def test_logout_requires_authentication(client):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 401


def test_logout_with_valid_token(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "verify_google_token", lambda token: mock_google_user())
    login_resp = client.post("/api/auth/google", json={"id_token": "fake-token"})
    token = login_resp.json()["access_token"]

    resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"
