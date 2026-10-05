import logging

from app.core.config import Settings, get_settings
from app.providers.base import LLMProvider
from app.providers.mock import MockProvider

logger = logging.getLogger(__name__)


def _primary_provider(settings: Settings) -> LLMProvider:
    name = settings.llm_provider.strip().lower()
    if name == "openai":
        from app.providers.openai import OpenAIProvider

        return OpenAIProvider(settings)
    if name == "anthropic":
        from app.providers.anthropic import AnthropicProvider

        return AnthropicProvider(settings)
    return MockProvider()


class FallbackProvider(LLMProvider):
    name = "fallback"

    def __init__(self, primary: LLMProvider, fallback: LLMProvider) -> None:
        self.primary = primary
        self.fallback = fallback

    def complete(self, prompt: str, temperature: float = 0.2) -> str:
        try:
            return self.primary.complete(prompt, temperature=temperature)
        except Exception:
            logger.warning(
                "primary provider %s failed; using %s",
                self.primary.name,
                self.fallback.name,
                exc_info=True,
            )
            return self.fallback.complete(prompt, temperature=temperature)


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    primary = _primary_provider(settings)
    if isinstance(primary, MockProvider):
        return primary
    return FallbackProvider(primary, MockProvider())
