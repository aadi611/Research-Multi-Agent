
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletion


class BaseAgent(ABC):
    """
    Abstract base class for all research agents.

    Provides shared OpenAI client configuration,
    response handling, and research interfaces.
    """

    DEFAULT_MODEL = "gpt-4o"

    def __init__(
        self,
        client: OpenAI,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> None:

        if client is None:
            raise ValueError("An OpenAI client is required.")

        if not model or not model.strip():
            raise ValueError("Model name cannot be empty.")

        if not 0 <= temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2.")

        self.client = client
        self.model = model.strip()
        self.temperature = temperature
        self.max_tokens = max_tokens

    # ---------------------------------------------------------
    # Abstract Interface
    # ---------------------------------------------------------

    @abstractmethod
    def research(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute the agent's research workflow.

        Args:
            query: Research topic or question.
            **kwargs: Agent-specific configuration.

        Returns:
            Structured research results.
        """
        raise NotImplementedError

    # ---------------------------------------------------------
    # OpenAI Response Handling
    # ---------------------------------------------------------

    @staticmethod
    def _get_text(response: ChatCompletion) -> str:
        """
        Extract textual content from an OpenAI response.
        """

        if not response.choices:
            return ""

        message = response.choices[0].message

        return message.content or ""

    # ---------------------------------------------------------
    # Query Validation
    # ---------------------------------------------------------

    @staticmethod
    def _validate_query(query: str) -> str:
        """
        Validate and normalize research queries.
        """

        if not isinstance(query, str):
            raise TypeError("Research query must be a string.")

        query = query.strip()

        if not query:
            raise ValueError("Research query cannot be empty.")

        return query

    # ---------------------------------------------------------
    # Shared LLM Configuration
    # ---------------------------------------------------------

    def _get_completion(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ChatCompletion:
        """
        Generate a standard chat completion.

        Allows individual agents to reuse consistent
        model configuration.
        """

        parameters = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        if self.max_tokens is not None:
            parameters["max_tokens"] = self.max_tokens

        parameters.update(kwargs)

        return self.client.chat.completions.create(
            **parameters
        )

    # ---------------------------------------------------------
    # Standard Agent Metadata
    # ---------------------------------------------------------

    def _get_metadata(self) -> dict[str, Any]:
        """
        Return common agent metadata.
        """

        return {
            "agent": self.__class__.__name__,
            "model": self.model,
        }
