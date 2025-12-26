"""
Context Formatter Service

Formats memories for LLM consumption with multiple formats:
- Template-based formatting
- Q&A format
- Narrative format
- Structured format
- Summary generation for long memories
- Optimal token usage

Usage:
    >>> from src.gml.services.context_formatter import get_context_formatter
    >>> 
    >>> formatter = await get_context_formatter()
    >>> formatted = formatter.format(
    ...     memories=memories,
    ...     format_type="narrative"
    ... )
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.gml.db.models import Memory

logger = logging.getLogger(__name__)


class ContextFormatter:
    """
    Formats memories for LLM consumption.
    
    Supports multiple formats optimized for different use cases
    and token efficiency.
    """

    def __init__(self) -> None:
        """Initialize context formatter."""
        logger.info("ContextFormatter initialized")

    def format(
        self,
        memories: List[Memory],
        format_type: str = "narrative",
        include_metadata: bool = True,
        max_length: Optional[int] = None,
    ) -> str:
        """
        Format memories into context string.

        Args:
            memories: List of Memory objects
            format_type: Format type (narrative, qa, structured)
            include_metadata: Whether to include metadata
            max_length: Maximum character length (None = no limit)

        Returns:
            Formatted context string
        """
        if not memories:
            return "No memories available."

        if format_type == "qa":
            return self._format_qa(memories, include_metadata, max_length)
        elif format_type == "structured":
            return self._format_structured(memories, include_metadata, max_length)
        else:  # narrative
            return self._format_narrative(memories, include_metadata, max_length)

    def _format_narrative(
        self,
        memories: List[Memory],
        include_metadata: bool,
        max_length: Optional[int],
    ) -> str:
        """Format as narrative text."""
        lines = ["Agent Memory Context:\n"]

        for i, memory in enumerate(memories, 1):
            content = memory.content
            text = content.get("text", str(content)) if isinstance(content, dict) else str(content)

            if include_metadata:
                lines.append(f"Memory {i} ({memory.memory_type})")
                lines.append(f"Created: {memory.created_at.strftime('%Y-%m-%d %H:%M')}")
                if memory.conversation_id:
                    lines.append(f"Conversation: {memory.conversation_id[:16]}...")
                lines.append("")

            # Truncate if needed
            if max_length:
                remaining = max_length - len("\n".join(lines))
                if len(text) > remaining:
                    text = text[:remaining - 3] + "..."

            lines.append(text)
            lines.append("\n")

        result = "\n".join(lines)
        if max_length and len(result) > max_length:
            result = result[:max_length - 3] + "..."
        return result

    def _format_qa(
        self,
        memories: List[Memory],
        include_metadata: bool,
        max_length: Optional[int],
    ) -> str:
        """Format as Q&A pairs."""
        lines = ["Agent Memory Context (Q&A Format):\n"]

        for i, memory in enumerate(memories, 1):
            content = memory.content
            text = content.get("text", str(content)) if isinstance(content, dict) else str(content)

            lines.append(f"Q{i}: What information is available about this memory?")
            if include_metadata:
                lines.append(f"  Type: {memory.memory_type}")
                lines.append(f"  Date: {memory.created_at.strftime('%Y-%m-%d')}")
            lines.append(f"A{i}: {text}")
            lines.append("")

        result = "\n".join(lines)
        if max_length and len(result) > max_length:
            result = result[:max_length - 3] + "..."
        return result

    def _format_structured(
        self,
        memories: List[Memory],
        include_metadata: bool,
        max_length: Optional[int],
    ) -> str:
        """Format as structured data."""
        lines = ["Agent Memory Context (Structured):\n"]

        for i, memory in enumerate(memories, 1):
            content = memory.content
            text = content.get("text", str(content)) if isinstance(content, dict) else str(content)

            lines.append(f"{{")
            lines.append(f'  "id": {i},')
            lines.append(f'  "context_id": "{memory.context_id}",')
            if include_metadata:
                lines.append(f'  "type": "{memory.memory_type}",')
                lines.append(f'  "created_at": "{memory.created_at.isoformat()}",')
                if memory.conversation_id:
                    lines.append(f'  "conversation_id": "{memory.conversation_id}",')
            lines.append(f'  "content": "{text[:200]}{"..." if len(text) > 200 else ""}"')
            lines.append(f"}},")

        result = "\n".join(lines)
        if max_length and len(result) > max_length:
            result = result[:max_length - 3] + "..."
        return result

    def generate_summary(self, memories: List[Memory], max_tokens: int = 200) -> str:
        """
        Generate summary of memories.

        Args:
            memories: List of Memory objects
            max_tokens: Maximum tokens for summary

        Returns:
            Summary string
        """
        if not memories:
            return "No memories to summarize."

        # Simple summary: count and types
        types = {}
        for mem in memories:
            types[mem.memory_type] = types.get(mem.memory_type, 0) + 1

        summary_parts = [f"Summary: {len(memories)} memories"]
        if types:
            type_str = ", ".join(f"{count} {typ}" for typ, count in types.items())
            summary_parts.append(f"Types: {type_str}")
        summary_parts.append(f"Date range: {memories[0].created_at.strftime('%Y-%m-%d')} to {memories[-1].created_at.strftime('%Y-%m-%d')}")

        return ". ".join(summary_parts) + "."


# Singleton instance
_context_formatter: Optional[ContextFormatter] = None


async def get_context_formatter() -> ContextFormatter:
    """Get or create the singleton context formatter instance."""
    global _context_formatter

    if _context_formatter is None:
        _context_formatter = ContextFormatter()
        logger.info("Context formatter singleton created")

    return _context_formatter


__all__ = ["ContextFormatter", "get_context_formatter"]

