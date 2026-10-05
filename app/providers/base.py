from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def complete(self, prompt: str, temperature: float = 0.2) -> str:
        raise NotImplementedError
