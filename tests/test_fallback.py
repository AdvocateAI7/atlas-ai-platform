from unittest.mock import MagicMock, patch

from app.providers.factory import FallbackProvider
from app.providers.mock import MockProvider


def test_fallback_on_primary_failure():
    primary = MagicMock()
    primary.name = "failing"
    primary.complete.side_effect = RuntimeError("provider down")

    fallback = MockProvider()
    provider = FallbackProvider(primary, fallback)

    result = provider.complete("hello", temperature=0.2)
    assert "mock" in result.lower()


def test_primary_used_when_healthy():
    primary = MagicMock()
    primary.name = "primary"
    primary.complete.return_value = "primary reply"

    provider = FallbackProvider(primary, MockProvider())
    assert provider.complete("hello") == "primary reply"


def test_fallback_endpoint_returns_200_on_primary_failure(client):
    with patch("app.providers.factory._primary_provider") as mock_primary:
        failing = MagicMock()
        failing.name = "failing"
        failing.complete.side_effect = RuntimeError("provider down")
        mock_primary.return_value = failing

        resp = client.post("/chat", json={"message": "fallback test"})
    assert resp.status_code == 200
    assert resp.json()["reply"] is not None
