import pytest

from app.services import google_auth


def make_idinfo(**overrides):
    base = {
        "iss": "accounts.google.com",
        "sub": "google-sub-123",
        "email": "reader@example.com",
        "email_verified": True,
        "name": "Ada Reader",
        "picture": "https://example.com/pic.jpg",
    }
    base.update(overrides)
    return base


def test_verify_google_token_success(monkeypatch):
    monkeypatch.setattr(google_auth.settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(
        google_auth.google_id_token, "verify_oauth2_token", lambda *a, **k: make_idinfo()
    )

    info = google_auth.verify_google_token("fake-token")

    assert info["google_id"] == "google-sub-123"
    assert info["email"] == "reader@example.com"
    assert info["name"] == "Ada Reader"
    assert info["picture"] == "https://example.com/pic.jpg"


def test_verify_google_token_missing_client_id(monkeypatch):
    monkeypatch.setattr(google_auth.settings, "GOOGLE_CLIENT_ID", None)

    with pytest.raises(google_auth.InvalidGoogleTokenError, match="not configured"):
        google_auth.verify_google_token("fake-token")


def test_verify_google_token_invalid_signature(monkeypatch):
    monkeypatch.setattr(google_auth.settings, "GOOGLE_CLIENT_ID", "test-client-id")

    def raise_value_error(*a, **k):
        raise ValueError("Token used too early")

    monkeypatch.setattr(google_auth.google_id_token, "verify_oauth2_token", raise_value_error)

    with pytest.raises(google_auth.InvalidGoogleTokenError, match="Invalid Google ID token"):
        google_auth.verify_google_token("bad-token")


def test_verify_google_token_wrong_issuer(monkeypatch):
    monkeypatch.setattr(google_auth.settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(
        google_auth.google_id_token,
        "verify_oauth2_token",
        lambda *a, **k: make_idinfo(iss="evil.com"),
    )

    with pytest.raises(google_auth.InvalidGoogleTokenError, match="issuer"):
        google_auth.verify_google_token("fake-token")


def test_verify_google_token_unverified_email(monkeypatch):
    monkeypatch.setattr(google_auth.settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(
        google_auth.google_id_token,
        "verify_oauth2_token",
        lambda *a, **k: make_idinfo(email_verified=False),
    )

    with pytest.raises(google_auth.InvalidGoogleTokenError, match="not verified"):
        google_auth.verify_google_token("fake-token")


def test_verify_google_token_falls_back_to_email_local_part_for_name(monkeypatch):
    monkeypatch.setattr(google_auth.settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(
        google_auth.google_id_token,
        "verify_oauth2_token",
        lambda *a, **k: make_idinfo(name=None, email="noname@example.com"),
    )

    info = google_auth.verify_google_token("fake-token")
    assert info["name"] == "noname"
