"""
Ollama Service

Service for interacting with local Ollama models (GPT-OSS, etc.)
Provides OpenAI-compatible interface for local LLM inference.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from openai import AsyncOpenAI, OpenAIError

from src.gml.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Ollama Configuration
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OLLAMA_API_KEY = "ollama"  # Dummy key for Ollama
DEFAULT_OLLAMA_MODEL = "gpt-oss:20b"
DEFAULT_TIMEOUT = 120.0  # Longer timeout for local models
DEFAULT_MAX_RETRIES = 3


class OllamaService:
    """
    Service for interacting with Ollama models via OpenAI-compatible API.
    
    Supports:
    - Chat completions
    - Function calling (tools)
    - Streaming responses
    - Local model inference
    """

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        api_key: str = DEFAULT_OLLAMA_API_KEY,
        model: str = DEFAULT_OLLAMA_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """
        Initialize Ollama service.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434/v1)
            api_key: API key (dummy "ollama" for local)
            model: Model name (e.g., "gpt-oss:20b")
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # Create OpenAI-compatible client pointing to Ollama
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=httpx.Timeout(timeout),
            max_retries=max_retries,
        )

        logger.info(
            f"OllamaService initialized: model={model}, base_url={base_url}"
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
    ) -> Any:
        """
        Create a chat completion using Ollama.

        Args:
            messages: List of message dicts with "role" and "content"
            model: Model name (defaults to instance model)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            tools: List of function tools for function calling
            stream: Whether to stream the response

        Returns:
            Chat completion response

        Example:
            >>> service = OllamaService()
            >>> response = await service.chat_completion([
            ...     {"role": "user", "content": "Hello!"}
            ... ])
            >>> print(response.choices[0].message.content)
        """
        model = model or self.model

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                stream=stream,
            )
            return response
        except OpenAIError as e:
            logger.error(f"Ollama API error: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def simple_chat(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Simple chat interface for quick interactions.

        Args:
            user_message: User's message
            system_message: Optional system message
            model: Model name (defaults to instance model)

        Returns:
            Assistant's response text

        Example:
            >>> service = OllamaService()
            >>> response = await service.simple_chat("What is AI?")
            >>> print(response)
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})

        response = await self.chat_completion(messages, model=model)
        return response.choices[0].message.content

    async def chat_with_tools(
        self,
        user_message: str,
        tools: List[Dict[str, Any]],
        system_message: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Any:
        """
        Chat with function calling support.

        Args:
            user_message: User's message
            tools: List of function tools
            system_message: Optional system message
            model: Model name (defaults to instance model)

        Returns:
            Chat completion response (may include tool calls)

        Example:
            >>> tools = [{
            ...     "type": "function",
            ...     "function": {
            ...         "name": "get_weather",
            ...         "description": "Get weather for a city",
            ...         "parameters": {
            ...             "type": "object",
            ...             "properties": {"city": {"type": "string"}},
            ...             "required": ["city"]
            ...         }
            ...     }
            ... }]
            >>> response = await service.chat_with_tools(
            ...     "What's the weather in Berlin?",
            ...     tools
            ... )
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})

        response = await self.chat_completion(
            messages=messages,
            model=model,
            tools=tools,
        )
        return response

    async def health_check(self) -> tuple[bool, str]:
        """
        Check if Ollama service is available.

        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            # Try to list models as a health check
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url.replace('/v1', '')}/api/tags")
                if response.status_code == 200:
                    return True, "Ollama is healthy"
                return False, f"Ollama returned status {response.status_code}"
        except httpx.TimeoutException:
            return False, "Ollama health check timed out"
        except httpx.RequestError as e:
            return False, f"Ollama connection error: {str(e)}"
        except Exception as e:
            return False, f"Ollama health check error: {str(e)}"

    async def list_models(self) -> List[str]:
        """
        List available Ollama models.

        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url.replace('/v1', '')}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    return models
                return []
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []


# Singleton instance
_ollama_service: Optional[OllamaService] = None


async def get_ollama_service() -> OllamaService:
    """
    Get the singleton OllamaService instance.

    Returns:
        OllamaService instance
    """
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
        logger.info("Ollama service singleton created")
    return _ollama_service


__all__ = [
    "OllamaService",
    "get_ollama_service",
    "DEFAULT_OLLAMA_BASE_URL",
    "DEFAULT_OLLAMA_MODEL",
]

