def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "lexora-backend"


def test_health_db(client):
    resp = client.get("/api/health/db")
    assert resp.status_code == 200
    assert resp.json()["database"] == "connected"
