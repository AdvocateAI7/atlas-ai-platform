def test_stats_without_token_returns_503(client):
    # No INTERNAL_ADMIN_TOKEN configured → 503 (misconfiguration guard)
    resp = client.get("/internal/stats")
    assert resp.status_code == 503


def test_stats_with_wrong_token_returns_401(client, monkeypatch):
    monkeypatch.setenv("INTERNAL_ADMIN_TOKEN", "secret")
    from app.core.config import get_settings

    get_settings.cache_clear()
    resp = client.get("/internal/stats", headers={"X-Internal-Token": "wrong"})
    assert resp.status_code == 401


def test_stats_with_correct_token(client, monkeypatch):
    monkeypatch.setenv("INTERNAL_ADMIN_TOKEN", "secret")
    from app.core.config import get_settings

    get_settings.cache_clear()
    resp = client.get("/internal/stats", headers={"X-Internal-Token": "secret"})
    assert resp.status_code == 200
    body = resp.json()
    assert "documents" in body
    assert "cache_hits" in body


def test_cache_flush_requires_auth(client):
    resp = client.post("/internal/cache/flush")
    assert resp.status_code == 503


def test_cache_flush_works_with_token(client, monkeypatch):
    monkeypatch.setenv("INTERNAL_ADMIN_TOKEN", "secret")
    from app.core.config import get_settings

    get_settings.cache_clear()
    resp = client.post("/internal/cache/flush", headers={"X-Internal-Token": "secret"})
    assert resp.status_code == 200
    assert "flushed" in resp.json()
