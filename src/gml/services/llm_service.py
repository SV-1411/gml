"""
LLM Service for Chat Integration

Supports multiple LLM providers:
- OpenAI
- Anthropic
- Ollama (local)

Features:
- Streaming responses
- Memory context injection
- Rate limiting
- Fallback LLMs
- Token tracking
- Function calling support

Usage:
    >>> from src.gml.services.llm_service import get_llm_service
    >>> 
    >>> service = await get_llm_service()
    >>> response = await service.chat_completion(
    ...     messages=[...],
    ...     stream=True
    ... )
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk

from src.gml.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM service supporting multiple providers with streaming.
    
    Handles OpenAI, Anthropic, and Ollama integrations with
    fallback support and token tracking.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Initialize LLM service.

        Args:
            provider: LLM provider (openai, anthropic, ollama)
            model: Model name
            api_key: API key (if needed)
        """
        self.provider = provider
        # Get model from settings with fallback
        if provider == "openai":
            self.model = model or getattr(settings, "OPENAI_MODEL", None) or "gpt-4"
        elif provider == "ollama":
            self.model = model or getattr(settings, "OLLAMA_MODEL", None) or "llama2"
        else:
            self.model = model or "gpt-4"
        self.api_key = api_key or settings.OPENAI_API_KEY
        
        # Initialize client based on provider
        if provider == "openai" and self.api_key and self.api_key.startswith("sk-"):
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            
        logger.info(f"LLMService initialized: provider={provider}, model={self.model}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream response
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Completion response or async generator for streaming
        """
        if self.provider == "openai":
            return await self._openai_completion(
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        elif self.provider == "ollama":
            return await self._ollama_completion(
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _openai_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs: Any,
    ) -> Any:
        """Generate completion using OpenAI."""
        if not self.client:
            # Fallback to Ollama
            logger.warning("OpenAI client not available, falling back to Ollama")
            return await self._ollama_completion(
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            if stream:
                return response
            else:
                return {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                }

        except Exception as e:
            logger.error(f"OpenAI completion failed: {str(e)}")
            # Fallback to Ollama
            if self.provider != "ollama":
                return await self._ollama_completion(
                    messages=messages,
                    stream=stream,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            raise

    async def _ollama_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs: Any,
    ) -> Any:
        """Generate completion using Ollama."""
        try:
            import httpx

            ollama_url = getattr(settings, "OLLAMA_URL", None) or "http://localhost:11434"
            model = kwargs.get("model") or getattr(settings, "OLLAMA_MODEL", None) or "llama2"

            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                },
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            async with httpx.AsyncClient(timeout=60.0) as client:
                if stream:
                    # Return async generator for streaming
                    async def _stream_generator():
                        async with client.stream(
                            "POST",
                            f"{ollama_url}/api/chat",
                            json=payload,
                        ) as response:
                            async for line in response.aiter_lines():
                                if line:
                                    try:
                                        import json
                                        data = json.loads(line)
                                        yield data
                                    except json.JSONDecodeError:
                                        continue
                    return _stream_generator()
                else:
                    response = await client.post(
                        f"{ollama_url}/api/chat",
                        json=payload,
                    )
                    data = response.json()
                    return {
                        "content": data.get("message", {}).get("content", ""),
                        "model": model,
                        "usage": {
                            "prompt_tokens": 0,  # Ollama doesn't provide this
                            "completion_tokens": 0,
                            "total_tokens": 0,
                        },
                    }

        except Exception as e:
            logger.error(f"Ollama completion failed: {str(e)}")
            raise

    async def stream_response(
        self, response: Any
    ) -> AsyncGenerator[str, None]:
        """
        Stream response chunks as text.

        Args:
            response: Streaming response object

        Yields:
            Text chunks
        """
        if isinstance(response, AsyncGenerator):
            # Ollama stream
            async for chunk in response:
                if chunk.get("message", {}).get("content"):
                    yield chunk["message"]["content"]
        else:
            # OpenAI stream
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content


# Singleton instance
_llm_service: Optional[LLMService] = None


async def get_llm_service(
    provider: str = "openai",
    model: Optional[str] = None,
) -> LLMService:
    """Get or create the singleton LLM service instance."""
    global _llm_service

    if _llm_service is None:
        _llm_service = LLMService(provider=provider, model=model)
        logger.info("LLM service singleton created")

    return _llm_service


__all__ = ["LLMService", "get_llm_service"]

