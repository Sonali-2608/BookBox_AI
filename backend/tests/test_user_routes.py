from app.models.preference import UserPreference


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


# --- Preferences ---


def test_preferences_requires_authentication(client):
    assert client.get("/api/user/preferences").status_code == 401
    assert client.put("/api/user/preferences", json={}).status_code == 401


def test_get_preferences_returns_defaults_when_unset(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    resp = client.get("/api/user/preferences", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["favorite_genres"] == []
    assert body["onboarding_completed"] is False


def test_update_preferences_creates_row(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    resp = client.put(
        "/api/user/preferences",
        json={
            "favorite_genres": ["Fantasy", "Sci-Fi"],
            "favorite_authors": ["Brandon Sanderson"],
            "reading_frequency": "weekly",
            "preferred_length": "medium",
        },
        headers=headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["favorite_genres"] == ["Fantasy", "Sci-Fi"]
    assert body["onboarding_completed"] is True
    assert db_session.query(UserPreference).count() == 1


def test_update_preferences_upserts_existing_row(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    client.put(
        "/api/user/preferences",
        json={"favorite_genres": ["Fantasy"], "favorite_authors": []},
        headers=headers,
    )
    client.put(
        "/api/user/preferences",
        json={"favorite_genres": ["Mystery"], "favorite_authors": []},
        headers=headers,
    )

    assert db_session.query(UserPreference).count() == 1
    resp = client.get("/api/user/preferences", headers=headers)
    assert resp.json()["favorite_genres"] == ["Mystery"]


def test_update_preferences_rejects_invalid_reading_frequency(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    resp = client.put(
        "/api/user/preferences",
        json={"favorite_genres": [], "favorite_authors": [], "reading_frequency": "constantly"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_update_preferences_rejects_invalid_preferred_length(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    resp = client.put(
        "/api/user/preferences",
        json={"favorite_genres": [], "favorite_authors": [], "preferred_length": "epic"},
        headers=headers,
    )
    assert resp.status_code == 400


# --- Analytics ---


def test_analytics_requires_authentication(client):
    assert client.get("/api/user/analytics").status_code == 401


def test_analytics_returns_zeroed_response_for_new_user(client, monkeypatch, db_session):
    headers = auth_headers(client, monkeypatch)
    resp = client.get("/api/user/analytics", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["books_completed"] == 0
    assert body["reading_streak_days"] == 0
