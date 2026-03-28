from abc import ABC, abstractmethod
from openai import OpenAI


class BaseAgent(ABC):
    def __init__(self, client: OpenAI, model: str = "gpt-4o"):
        self.client = client
        self.model = model

    @abstractmethod
    def research(self, query: str, **kwargs) -> dict:
        pass

    def _get_text(self, response) -> str:
        return response.choices[0].message.content or ""
