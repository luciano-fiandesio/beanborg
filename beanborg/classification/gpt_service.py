"""OpenAI GPT service for transaction categorization.

This module provides functionality to categorize financial transactions
using OpenAI's GPT models through natural language processing.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from openai import AuthenticationError, OpenAI
from openai.types.chat import ChatCompletion
from rich import print as rprint


class GPTError(Exception):
    """Base exception for GPT service errors."""
    pass


class GPTInitError(GPTError):
    """Raised when GPT service initialization fails."""
    pass


class GPTQueryError(GPTError):
    """Raised when GPT query fails."""
    pass


class ModelType(Enum):
    """Supported GPT model types."""
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"


@dataclass
class GPTConfig:
    """Configuration for GPT service.

    Attributes:
        model: GPT model to use
        temperature: Randomness in model responses (0-1)
        top_p: Nucleus sampling parameter (0-1)
        system_prompt: System message for model context
    """
    model: ModelType = ModelType.GPT4
    temperature: float = 0.7
    top_p: float = 1.0
    system_prompt: str = (
        "You are 'TransactionBud' a helpful and concise utility designed to "
        "categorize bank transactions efficiently. Your primary function is "
        "to assign a category to each transaction presented to you"
    )


class GPTService:
    """Service for categorizing transactions using OpenAI's GPT models.

    This service handles communication with OpenAI's API for transaction
    categorization, including initialization, error handling, and querying.

    Attributes:
        client: OpenAI client instance
        config: GPT configuration settings
    """

    def __init__(
        self,
        use_llm: bool,
        config: Optional[GPTConfig] = None
    ) -> None:
        """Initialize the GPT service.

        Args:
            use_llm: Whether to enable GPT functionality
            config: Optional GPT configuration settings

        Raises:
            GPTInitError: If initialization fails with LLM enabled
        """
        self.client: Optional[OpenAI] = None
        self.config = config or GPTConfig()

        if use_llm:
            try:
                self.client = OpenAI()
                # Validate API key with a simple request
                self.client.models.list()
            except AuthenticationError as e:
                raise GPTInitError("OpenAI API key is invalid or not set") from e
            except Exception as e:
                raise GPTInitError(f"Failed to initialize OpenAI client: {e}") from e

    def query_gpt_for_label(
        self,
        description: str,
        labels: List[str]
    ) -> str:
        """Query GPT model to categorize a transaction.

        Args:
            description: Transaction description to categorize
            labels: List of valid category labels

        Returns:
            Predicted category label

        Raises:
            GPTQueryError: If query fails
            ValueError: If inputs are invalid
        """
        if not self.client:
            return "OpenAI not available"

        if not description or not labels:
            raise ValueError("Description and labels must not be empty")

        try:
            response: ChatCompletion = self.client.chat.completions.create(
                model=self.config.model.value,
                messages=[
                    {
                        "role": "system",
                        "content": self.config.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Given the description '{description}', what would be "
                            f"the most appropriate category among the following: "
                            f"{', '.join(labels)}? Only output the category name "
                            f"without any additional text."
                        ),
                    },
                ],
                temperature=self.config.temperature,
                top_p=self.config.top_p,
            )

            if not response.choices:
                raise GPTQueryError("No response choices received")

            return response.choices[0].message.content.strip()

        except Exception as e:
            rprint(f"[red]Failed to query GPT: {e}[/red]")
            return "OpenAI not available"

    def is_available(self) -> bool:
        """Check if GPT service is available.

        Returns:
            bool: True if service is initialized and ready
        """
        return self.client is not None
