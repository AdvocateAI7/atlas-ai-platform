from app.providers.base import LLMProvider


class MockProvider(LLMProvider):
    name = "mock"

    def complete(self, prompt: str, temperature: float = 0.2) -> str:
        excerpt = prompt.strip().replace("\n", " ")[:180]
        return (
            f"[mock t={temperature:.2f}] I received your request and generated a "
            f"local reply without calling an external model. Prompt excerpt: {excerpt}"
        )
