"""
Context Summarization Service

Generates AI summaries of conversations:
- Extract key decisions and actions
- Identify open questions
- Highlight important memories
- Generate recommendations
- Create follow-up questions

Usage:
    >>> from src.gml.services.context_summarizer import get_summarizer
    >>> 
    >>> summarizer = await get_summarizer()
    >>> summary = await summarizer.summarize_context(context)
"""

import logging
from typing import Any, Dict, List, Optional

from src.gml.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class ContextSummarizer:
    """
    Generates comprehensive summaries of conversation context.
    
    Uses LLM to extract key information, decisions, and generate
    actionable insights from conversation context.
    """

    def __init__(self) -> None:
        """Initialize context summarizer."""
        logger.info("ContextSummarizer initialized")

    async def summarize_context(
        self,
        context: Dict[str, Any],
        style: str = "standard",
    ) -> Dict[str, Any]:
        """
        Generate summary of conversation context.

        Args:
            context: Full context dictionary
            style: Summary style (standard, executive, detailed, brief)

        Returns:
            Summary dictionary with key information
        """
        try:
            # Build summary prompt
            prompt = self._build_summary_prompt(context, style)

            # Get LLM service
            llm_service = await get_llm_service(provider="ollama")

            # Generate summary
            messages = [
                {"role": "system", "content": "You are an expert at summarizing conversations and extracting key insights."},
                {"role": "user", "content": prompt},
            ]

            response = await llm_service.chat_completion(
                messages=messages,
                stream=False,
                temperature=0.3,
                max_tokens=1000,
            )

            summary_text = response.get("content", "") if isinstance(response, dict) else str(response)

            # Extract structured information
            summary = {
                "conversation_id": context.get("conversation_id"),
                "style": style,
                "summary_text": summary_text,
                "key_decisions": self._extract_key_decisions(context),
                "actions": self._extract_actions(context),
                "open_questions": self._extract_open_questions(context),
                "important_memories": self._get_important_memories(context),
                "recommendations": self._generate_recommendations(context),
                "follow_up_questions": self._generate_follow_ups(context),
                "statistics": context.get("statistics", {}),
            }

            return summary

        except Exception as e:
            logger.error(f"Error summarizing context: {str(e)}")
            # Fallback to basic summary
            return self._generate_basic_summary(context, style)

    def _build_summary_prompt(self, context: Dict[str, Any], style: str) -> str:
        """Build prompt for LLM summarization."""
        messages = context.get("messages", [])
        memories = context.get("memories", [])

        prompt_parts = [
            f"Summarize the following conversation in {style} style:",
            "",
            "CONVERSATION:",
        ]

        # Add conversation
        for msg in messages:
            prompt_parts.append(f"{msg['role'].upper()}: {msg['content'][:500]}")

        if memories:
            prompt_parts.append("")
            prompt_parts.append("RELATED MEMORIES:")
            for mem in memories[:10]:  # Limit to 10 memories
                content = str(mem.get("content", ""))[:200]
                prompt_parts.append(f"- {content}")

        prompt_parts.extend([
            "",
            "Please provide:",
            "1. A concise summary of the conversation",
            "2. Key decisions made",
            "3. Important actions taken",
            "4. Open questions or unresolved issues",
        ])

        return "\n".join(prompt_parts)

    def _extract_key_decisions(self, context: Dict[str, Any]) -> List[str]:
        """Extract key decisions from context."""
        decisions = []

        decision_points = context.get("decision_points", [])
        for dp in decision_points:
            decisions.append(dp.get("content", "")[:200])

        # Also look in messages
        for msg in context.get("messages", []):
            content = msg.get("content", "").lower()
            if any(word in content for word in ["decided", "chose", "selected", "will"]):
                if msg.get("role") == "assistant":
                    decisions.append(msg.get("content", "")[:200])

        return decisions[:5]  # Limit to 5

    def _extract_actions(self, context: Dict[str, Any]) -> List[str]:
        """Extract actions from context."""
        actions = []

        for msg in context.get("messages", []):
            content = msg.get("content", "").lower()
            if any(word in content for word in ["action", "todo", "will do", "going to"]):
                actions.append(msg.get("content", "")[:200])

        return actions[:5]

    def _extract_open_questions(self, context: Dict[str, Any]) -> List[str]:
        """Extract open questions."""
        questions = []

        gaps = context.get("knowledge_gaps", [])
        for gap in gaps:
            questions.append(gap.get("question", ""))

        # Also extract questions from messages
        for msg in context.get("messages", []):
            if msg.get("role") == "user" and "?" in msg.get("content", ""):
                questions.append(msg.get("content", "")[:200])

        return questions[:5]

    def _get_important_memories(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get most important memories."""
        memories = context.get("memories", [])
        messages = context.get("messages", [])

        # Count how often each memory is used
        usage_count = {}
        for msg in messages:
            for mem_id in msg.get("used_memories", []):
                usage_count[mem_id] = usage_count.get(mem_id, 0) + 1

        # Sort by usage
        memory_dict = {m["context_id"]: m for m in memories}
        important = sorted(
            [
                {
                    "context_id": mem_id,
                    "content": memory_dict[mem_id]["content"],
                    "usage_count": count,
                }
                for mem_id, count in usage_count.items()
                if mem_id in memory_dict
            ],
            key=lambda x: x["usage_count"],
            reverse=True,
        )

        return important[:5]

    def _generate_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on context."""
        recommendations = []

        # Simple recommendations based on gaps
        gaps = context.get("knowledge_gaps", [])
        if gaps:
            recommendations.append("Address unanswered questions from the conversation")

        # Recommendations based on decisions
        decisions = context.get("decision_points", [])
        if decisions:
            recommendations.append("Follow up on decisions made during the conversation")

        return recommendations

    def _generate_follow_ups(self, context: Dict[str, Any]) -> List[str]:
        """Generate follow-up questions."""
        follow_ups = []

        # Generate based on conversation end
        messages = context.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "assistant":
                follow_ups.append("Would you like to continue this conversation?")
                follow_ups.append("Are there any related topics you'd like to discuss?")

        return follow_ups

    def _generate_basic_summary(
        self,
        context: Dict[str, Any],
        style: str,
    ) -> Dict[str, Any]:
        """Generate basic summary without LLM."""
        stats = context.get("statistics", {})

        summary_text = f"""Conversation Summary ({style} style):
        
This conversation contains {stats.get('message_count', 0)} messages between the user and assistant.
{stats.get('memory_count', 0)} related memories were accessed during the conversation.
The conversation covered {stats.get('user_messages', 0)} user queries and {stats.get('assistant_messages', 0)} assistant responses.
"""

        return {
            "conversation_id": context.get("conversation_id"),
            "style": style,
            "summary_text": summary_text,
            "key_decisions": [],
            "actions": [],
            "open_questions": [],
            "important_memories": [],
            "recommendations": [],
            "follow_up_questions": [],
            "statistics": stats,
        }


# Singleton instance
_summarizer: Optional[ContextSummarizer] = None


async def get_summarizer() -> ContextSummarizer:
    """Get or create the singleton summarizer instance."""
    global _summarizer

    if _summarizer is None:
        _summarizer = ContextSummarizer()
        logger.info("Context summarizer singleton created")

    return _summarizer


__all__ = ["ContextSummarizer", "get_summarizer"]

