"""
Ollama API Routes

FastAPI router for Ollama LLM endpoints.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.gml.services.ollama_service import get_ollama_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ollama", tags=["ollama"])


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat completion request"""
    messages: List[ChatMessage] = Field(..., description="List of messages")
    model: Optional[str] = Field(None, description="Model name (defaults to gpt-oss:20b)")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    system_message: Optional[str] = Field(None, description="System message (optional)")


class ChatResponse(BaseModel):
    """Chat completion response"""
    model: str
    content: str
    finish_reason: str


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Ollama model",
    description="Send a chat message to Ollama (GPT-OSS 20B or other models)",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat with Ollama model.

    Args:
        request: Chat request with messages and parameters

    Returns:
        Chat response with model output

    Example:
        POST /api/v1/ollama/chat
        {
            "messages": [
                {"role": "user", "content": "Hello!"}
            ],
            "model": "gpt-oss:20b",
            "temperature": 0.7
        }
    """
    try:
        service = await get_ollama_service()
        
        # Convert messages to dict format
        messages = []
        if request.system_message:
            messages.append({"role": "system", "content": request.system_message})
        
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Call Ollama
        response = await service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        return ChatResponse(
            model=response.model,
            content=response.choices[0].message.content,
            finish_reason=response.choices[0].finish_reason or "stop",
        )
        
    except Exception as e:
        logger.error(f"Ollama chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get response from Ollama: {str(e)}",
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check Ollama health",
    description="Check if Ollama service is available and healthy",
)
async def ollama_health() -> dict:
    """
    Check Ollama service health.

    Returns:
        Health status
    """
    try:
        service = await get_ollama_service()
        healthy, message = await service.health_check()
        
        return {
            "status": "healthy" if healthy else "unhealthy",
            "message": message,
            "base_url": service.base_url,
            "model": service.model,
        }
    except Exception as e:
        logger.error(f"Ollama health check error: {e}")
        return {
            "status": "unhealthy",
            "message": str(e),
        }


@router.get(
    "/models",
    status_code=status.HTTP_200_OK,
    summary="List available Ollama models",
    description="Get list of available Ollama models",
)
async def list_models() -> dict:
    """
    List available Ollama models.

    Returns:
        List of model names
    """
    try:
        service = await get_ollama_service()
        models = await service.list_models()
        
        return {
            "models": models,
            "count": len(models),
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}",
        )


@router.post(
    "/simple",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Simple chat",
    description="Simple chat interface for quick interactions",
)
async def simple_chat(
    message: str,
    system_message: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """
    Simple chat interface.

    Args:
        message: User message
        system_message: Optional system message
        model: Model name (optional)

    Returns:
        Response with assistant's message
    """
    try:
        service = await get_ollama_service()
        response = await service.simple_chat(
            user_message=message,
            system_message=system_message,
            model=model,
        )
        
        return {
            "response": response,
            "model": model or service.model,
        }
    except Exception as e:
        logger.error(f"Simple chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get response: {str(e)}",
        )

