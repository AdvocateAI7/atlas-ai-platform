from app.services.rate_limit import RateLimiter


def test_allow_under_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        assert limiter.allow("client1") is True


def test_block_at_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.allow("client1")
    assert limiter.allow("client1") is False


def test_per_client_isolation():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.allow("client1")
    assert limiter.allow("client1") is False
    assert limiter.allow("client2") is True  # separate bucket


def test_rate_limit_endpoint(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    from app.core.config import get_settings
    from app.services import rate_limit as rl_module

    get_settings.cache_clear()
    rl_module._limiter = None  # force re-creation with new settings

    headers = {"X-Client-Id": "test-rate-client"}
    r1 = client.post("/chat", json={"message": "hi"}, headers=headers)
    r2 = client.post("/chat", json={"message": "hi2"}, headers=headers)
    r3 = client.post("/chat", json={"message": "hi3"}, headers=headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429

    # cleanup
    rl_module._limiter = None
