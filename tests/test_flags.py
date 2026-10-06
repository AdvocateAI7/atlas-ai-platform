def test_strict_mode_rejects_long_message(client, monkeypatch):
    monkeypatch.setenv("STRICT_MODE", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()
    resp = client.post("/chat", json={"message": "x" * 4001})
    assert resp.status_code == 413


def test_strict_mode_off_allows_long_message(client, monkeypatch):
    monkeypatch.setenv("STRICT_MODE", "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    resp = client.post("/chat", json={"message": "x" * 4001})
    assert resp.status_code == 200


def test_strict_mode_rejects_large_document(client, monkeypatch):
    monkeypatch.setenv("STRICT_MODE", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()
    resp = client.post("/documents", json={"text": "y" * 20_001})
    assert resp.status_code == 413


def test_cache_flag_disabled(client, monkeypatch):
    monkeypatch.setenv("ENABLE_RESPONSE_CACHE", "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    r1 = client.post("/chat", json={"message": "cache flag test"})
    r2 = client.post("/chat", json={"message": "cache flag test"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    # With cache disabled both requests go to the provider; neither shows cached=True
    assert r1.json()["cached"] is False
    assert r2.json()["cached"] is False
