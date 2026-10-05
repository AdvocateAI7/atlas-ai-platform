import time

from app.services.cache import ResponseCache


def test_cache_miss():
    cache = ResponseCache()
    assert cache.get("key") is None
    assert cache.misses == 1


def test_cache_hit():
    cache = ResponseCache()
    cache.set("key", "value", ttl_seconds=60)
    assert cache.get("key") == "value"
    assert cache.hits == 1


def test_cache_ttl_expiry():
    cache = ResponseCache()
    cache.set("key", "value", ttl_seconds=0)
    time.sleep(0.01)
    assert cache.get("key") is None


def test_cache_flush():
    cache = ResponseCache()
    cache.set("a", "1", ttl_seconds=60)
    cache.set("b", "2", ttl_seconds=60)
    removed = cache.flush()
    assert removed == 2
    assert cache.size() == 0


def test_chat_different_temperatures_not_cached(client, monkeypatch):
    # ISS-2 regression: same message, different temperature must not share cache entry
    monkeypatch.setenv("ENABLE_RESPONSE_CACHE", "true")
    from app.core.config import get_settings
    get_settings.cache_clear()

    r1 = client.post("/chat", json={"message": "cache test msg", "temperature": 0.1})
    r2 = client.post("/chat", json={"message": "cache test msg", "temperature": 0.9})
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Replies must differ because temperature is embedded in mock output
    assert r1.json()["reply"] != r2.json()["reply"]
    assert r2.json()["cached"] is False
