"""
LLM Integration for LangGraph Agents.

Provides Ollama integration that works with LangGraph.
Can be extended to support other LLM providers.
"""

import logging
from functools import lru_cache

import httpx
import requests
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class LLMSettings(BaseSettings):
    """LLM configuration settings."""

    ollama_url: str = "http://host.docker.internal:11434"
    ollama_default_model: str = "qwen2.5:14b"
    ollama_timeout: int = 120
    ollama_temperature: float = 0.7
    ollama_max_tokens: int = 2048
    ollama_num_ctx: int = 4096

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_llm_settings() -> LLMSettings:
    """Get cached LLM settings."""
    return LLMSettings()


class OllamaLLM:
    """
    Simple Ollama LLM wrapper for LangGraph agents.

    This provides a clean interface for calling Ollama without
    heavy LangChain abstractions.
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
    ) -> None:
        """
        Initialize OllamaLLM.

        Args:
            model: Ollama model name.
            base_url: Ollama API base URL.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds.
        """
        settings = get_llm_settings()
        self.model = model or settings.ollama_default_model
        self.base_url = base_url or settings.ollama_url
        self.temperature = temperature if temperature is not None else settings.ollama_temperature
        self.max_tokens = max_tokens or settings.ollama_max_tokens
        self.timeout = timeout or settings.ollama_timeout
        self.num_ctx = settings.ollama_num_ctx

    def invoke(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> str:
        """
        Invoke the LLM with a prompt (synchronous).

        Args:
            prompt: The input prompt.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.

        Returns:
            The LLM response text.

        Raises:
            Exception: If the LLM call fails.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature if temperature is not None else self.temperature,
                    "num_predict": max_tokens if max_tokens is not None else self.max_tokens,
                    "num_ctx": self.num_ctx,
                },
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            return data.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"Failed to call LLM: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling LLM: {e}")
            raise

    async def ainvoke(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> str:
        """
        Async invoke using httpx for true non-blocking async.

        Args:
            prompt: The input prompt.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.

        Returns:
            The LLM response text.

        Raises:
            Exception: If the LLM call fails.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature if temperature is not None else self.temperature,
                    "num_predict": max_tokens if max_tokens is not None else self.max_tokens,
                    "num_ctx": self.num_ctx,
                },
            }

            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                return data.get("response", "").strip()

        except httpx.TimeoutException as e:
            logger.error(f"Ollama API timeout: {e}")
            raise Exception(f"LLM request timed out after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API HTTP error: {e}")
            raise Exception(f"Failed to call LLM: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error calling LLM async: {e}")
            raise

    def __repr__(self) -> str:
        return f"OllamaLLM(model={self.model}, temperature={self.temperature})"


def get_llm(
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> OllamaLLM:
    """
    Factory function to get an LLM instance.

    Args:
        model: The Ollama model to use.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.

    Returns:
        Configured OllamaLLM instance.
    """
    return OllamaLLM(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
