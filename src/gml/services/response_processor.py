"""
Response Processing Service

Processes LLM responses:
- Extract memories from LLM response
- Identify action items
- Generate follow-up memory items
- Update memory relevance scores
- Create conversation summary
- Return structured response

Usage:
    >>> from src.gml.services.response_processor import get_response_processor
    >>> 
    >>> processor = await get_response_processor()
    >>> processed = await processor.process_response(
    ...     response="...",
    ...     agent_id="agent-123"
    ... )
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """
    Processes LLM responses for memory extraction and action items.
    
    Analyzes responses to extract useful information and create memories.
    """

    def __init__(self) -> None:
        """Initialize response processor."""
        logger.info("ResponseProcessor initialized")

    def process_response(
        self,
        response: str,
        agent_id: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process LLM response.

        Args:
            response: LLM response text
            agent_id: Agent ID
            conversation_id: Conversation ID

        Returns:
            Dictionary with:
            - response: Original response
            - extracted_memories: List of extracted memory texts
            - action_items: List of action items
            - summary: Response summary
        """
        try:
            # Extract memories (simple pattern matching)
            extracted_memories = self._extract_memories(response)

            # Identify action items
            action_items = self._identify_action_items(response)

            # Generate summary
            summary = self._generate_summary(response)

            return {
                "response": response,
                "extracted_memories": extracted_memories,
                "action_items": action_items,
                "summary": summary,
            }

        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return {
                "response": response,
                "extracted_memories": [],
                "action_items": [],
                "summary": response[:200] + "..." if len(response) > 200 else response,
            }

    def _extract_memories(self, response: str) -> List[str]:
        """
        Extract potential memories from response.

        Uses simple pattern matching to find factual statements.
        """
        memories = []

        # Look for statements that might be worth remembering
        # Simple heuristics: sentences with "I learned", "Remember that", etc.
        patterns = [
            r"(?:I learned|Remember that|Note that|Keep in mind)[^.!?]*[.!?]",
            r"(?:The user|You) (?:prefers?|likes?|wants?|needs?)[^.!?]*[.!?]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            memories.extend(matches)

        return memories[:5]  # Limit to 5

    def _identify_action_items(self, response: str) -> List[str]:
        """
        Identify action items from response.

        Looks for tasks, todos, or action-oriented statements.
        """
        action_items = []

        # Look for action-oriented phrases
        patterns = [
            r"(?:I will|I'll|We should|You should|Let's|I need to)[^.!?]*[.!?]",
            r"(?:TODO|Action|Task)[:][^.!?]*[.!?]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            action_items.extend(matches)

        return action_items[:5]  # Limit to 5

    def _generate_summary(self, response: str) -> str:
        """Generate summary of response."""
        if len(response) <= 200:
            return response

        # Simple summary: first sentence + last sentence
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) == 1:
            return response[:200] + "..." if len(response) > 200 else response

        summary = sentences[0]
        if len(sentences) > 1:
            summary += ". " + sentences[-1]

        return summary[:200] + "..." if len(summary) > 200 else summary


# Singleton instance
_response_processor: Optional[ResponseProcessor] = None


async def get_response_processor() -> ResponseProcessor:
    """Get or create the singleton response processor instance."""
    global _response_processor

    if _response_processor is None:
        _response_processor = ResponseProcessor()
        logger.info("Response processor singleton created")

    return _response_processor


__all__ = ["ResponseProcessor", "get_response_processor"]

