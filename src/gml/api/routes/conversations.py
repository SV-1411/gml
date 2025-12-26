"""
Conversation Context API Routes

Provides endpoints for retrieving complete conversation context:
- GET /api/v1/conversations/{id}/context - Get full context
- POST /api/v1/conversations/{id}/summary - Generate summary
- GET /api/v1/conversations/{id}/export - Export context

Usage:
    GET /api/v1/conversations/conv-123/context?context_level=full
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.database import get_db
from src.gml.services.context_exporter import get_exporter
from src.gml.services.context_summarizer import get_summarizer
from src.gml.services.conversation_context_service import get_context_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ConversationSummaryResponse(BaseModel):
    """Response model for conversation summary."""

    conversation_id: str
    summary: dict


# ============================================================================
# CONVERSATION ENDPOINTS
# ============================================================================


@router.get(
    "/{conversation_id}/context",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get conversation context",
    description="Retrieve complete conversation context with all related memories",
)
async def get_conversation_context(
    conversation_id: str,
    context_level: str = Query("full", description="Context level (minimal, full, detailed)"),
    agent_id: Optional[str] = Query(None, description="Agent ID filter"),
    filter_date_from: Optional[str] = Query(None, description="Filter memories from date (ISO format)"),
    filter_date_to: Optional[str] = Query(None, description="Filter memories to date (ISO format)"),
    filter_types: Optional[str] = Query(None, description="Comma-separated memory types to filter"),
    min_relevance: float = Query(0.0, ge=0.0, le=1.0, description="Minimum relevance score"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get complete conversation context.

    Retrieves full conversation history with all related memories,
    agent state, relationships, and decision points.

    Args:
        conversation_id: Conversation ID
        context_level: Context detail level
        agent_id: Optional agent ID filter
        filter_date_from: Filter memories from date
        filter_date_to: Filter memories to date
        filter_types: Filter by memory types
        min_relevance: Minimum relevance score
        db: Database session

    Returns:
        Complete context dictionary

    Raises:
        HTTPException 404: If conversation not found
        HTTPException 500: For server errors
    """
    try:
        context_service = await get_context_service()

        # Parse filters
        date_from = datetime.fromisoformat(filter_date_from) if filter_date_from else None
        date_to = datetime.fromisoformat(filter_date_to) if filter_date_to else None
        types_list = filter_types.split(",") if filter_types else None

        context = await context_service.get_full_context(
            conversation_id=conversation_id,
            context_level=context_level,
            agent_id=agent_id,
            filter_date_from=date_from,
            filter_date_to=date_to,
            filter_types=types_list,
            min_relevance=min_relevance,
            db=db,
        )

        if "error" in context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=context["error"],
            )

        return context

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation context: {str(e)}",
        )


@router.post(
    "/{conversation_id}/summary",
    response_model=ConversationSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate conversation summary",
    description="Generate AI summary of conversation context",
)
async def generate_summary(
    conversation_id: str,
    style: str = Query("standard", description="Summary style (standard, executive, detailed, brief)"),
    context_level: str = Query("full", description="Context level for summary"),
    db: AsyncSession = Depends(get_db),
) -> ConversationSummaryResponse:
    """
    Generate conversation summary.

    Creates AI-powered summary with key decisions, actions,
    open questions, and recommendations.

    Args:
        conversation_id: Conversation ID
        style: Summary style
        context_level: Context level to use
        db: Database session

    Returns:
        Summary response

    Raises:
        HTTPException 404: If conversation not found
        HTTPException 500: For server errors
    """
    try:
        context_service = await get_context_service()
        summarizer = await get_summarizer()

        # Get context first
        context = await context_service.get_full_context(
            conversation_id=conversation_id,
            context_level=context_level,
            db=db,
        )

        if "error" in context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=context["error"],
            )

        # Generate summary
        summary = await summarizer.summarize_context(context, style=style)

        return ConversationSummaryResponse(
            conversation_id=conversation_id,
            summary=summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}",
        )


@router.get(
    "/{conversation_id}/export",
    summary="Export conversation context",
    description="Export conversation context in various formats",
)
async def export_context(
    conversation_id: str,
    format: str = Query("json", description="Export format (json, markdown, html)"),
    context_level: str = Query("full", description="Context level"),
    include_messages: bool = Query(True, description="Include messages"),
    include_memories: bool = Query(True, description="Include memories"),
    include_relationships: bool = Query(False, description="Include relationships"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Export conversation context.

    Exports context in specified format (JSON, Markdown, HTML).

    Args:
        conversation_id: Conversation ID
        format: Export format
        context_level: Context level
        include_messages: Include messages in export
        include_memories: Include memories in export
        include_relationships: Include relationships in export
        db: Database session

    Returns:
        Exported content as Response

    Raises:
        HTTPException 404: If conversation not found
        HTTPException 500: For server errors
    """
    try:
        context_service = await get_context_service()
        exporter = await get_exporter()

        # Get context
        context = await context_service.get_full_context(
            conversation_id=conversation_id,
            context_level=context_level,
            db=db,
        )

        if "error" in context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=context["error"],
            )

        # Export
        exported = await exporter.export_filtered(
            context=context,
            format=format,
            include_messages=include_messages,
            include_memories=include_memories,
            include_relationships=include_relationships,
        )

        # Set content type
        content_types = {
            "json": "application/json",
            "markdown": "text/markdown",
            "html": "text/html",
        }
        content_type = content_types.get(format, "text/plain")

        return Response(
            content=exported,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="conversation-{conversation_id}.{format}"',
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export context: {str(e)}",
        )


__all__ = ["router"]

