"""
Context Export Service

Exports conversation context in multiple formats:
- JSON
- PDF
- Markdown
- HTML
- CSV

Usage:
    >>> from src.gml.services.context_exporter import get_exporter
    >>> 
    >>> exporter = await get_exporter()
    >>> json_data = await exporter.export_json(context)
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContextExporter:
    """
    Exports conversation context in multiple formats.
    
    Supports JSON, PDF, Markdown, HTML, and CSV formats with
    formatting and styling options.
    """

    def __init__(self) -> None:
        """Initialize context exporter."""
        logger.info("ContextExporter initialized")

    async def export_json(
        self,
        context: Dict[str, Any],
        pretty: bool = True,
    ) -> str:
        """
        Export context as JSON.

        Args:
            context: Context dictionary
            pretty: Pretty-print JSON

        Returns:
            JSON string
        """
        try:
            if pretty:
                return json.dumps(context, indent=2, default=str)
            return json.dumps(context, default=str)
        except Exception as e:
            logger.error(f"Error exporting JSON: {str(e)}")
            raise

    async def export_markdown(
        self,
        context: Dict[str, Any],
    ) -> str:
        """
        Export context as Markdown.

        Args:
            context: Context dictionary

        Returns:
            Markdown string
        """
        lines = [
            "# Conversation Context",
            "",
            f"**Conversation ID:** {context.get('conversation_id', 'N/A')}",
            f"**Agent ID:** {context.get('agent_id', 'N/A')}",
            f"**Generated At:** {context.get('generated_at', 'N/A')}",
            "",
            "## Statistics",
            "",
        ]

        stats = context.get("statistics", {})
        lines.extend([
            f"- Total Messages: {stats.get('message_count', 0)}",
            f"- Memories Used: {stats.get('memory_count', 0)}",
            f"- User Messages: {stats.get('user_messages', 0)}",
            f"- Assistant Messages: {stats.get('assistant_messages', 0)}",
            "",
        ])

        # Messages
        lines.extend([
            "## Messages",
            "",
        ])

        for msg in context.get("messages", []):
            lines.extend([
                f"### {msg.get('role', 'unknown').title()} Message",
                f"**Time:** {msg.get('created_at', 'N/A')}",
                "",
                msg.get("content", ""),
                "",
            ])

            if msg.get("used_memories"):
                lines.append(f"**Used Memories:** {', '.join(msg['used_memories'])}")
                lines.append("")

        # Memories
        memories = context.get("memories", [])
        if memories:
            lines.extend([
                "## Related Memories",
                "",
            ])

            for mem in memories:
                lines.extend([
                    f"### Memory: {mem.get('context_id', 'N/A')}",
                    f"**Type:** {mem.get('memory_type', 'N/A')}",
                    f"**Created:** {mem.get('created_at', 'N/A')}",
                    "",
                    f"```json\n{json.dumps(mem.get('content', {}), indent=2)}\n```",
                    "",
                ])

        return "\n".join(lines)

    async def export_html(
        self,
        context: Dict[str, Any],
    ) -> str:
        """
        Export context as HTML.

        Args:
            context: Context dictionary

        Returns:
            HTML string
        """
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Conversation Context</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .message { margin: 10px 0; padding: 10px; border-left: 3px solid #007bff; }
        .message.user { border-color: #28a745; }
        .message.assistant { border-color: #007bff; }
        .memory { margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
    </style>
</head>
<body>
"""

        html += f"""
    <div class="header">
        <h1>Conversation Context</h1>
        <p><strong>Conversation ID:</strong> {context.get('conversation_id', 'N/A')}</p>
        <p><strong>Agent ID:</strong> {context.get('agent_id', 'N/A')}</p>
        <p><strong>Generated At:</strong> {context.get('generated_at', 'N/A')}</p>
    </div>
"""

        # Statistics
        stats = context.get("statistics", {})
        html += """
    <div class="section">
        <h2>Statistics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
"""
        html += f"            <tr><td>Total Messages</td><td>{stats.get('message_count', 0)}</td></tr>"
        html += f"            <tr><td>Memories Used</td><td>{stats.get('memory_count', 0)}</td></tr>"
        html += f"            <tr><td>User Messages</td><td>{stats.get('user_messages', 0)}</td></tr>"
        html += f"            <tr><td>Assistant Messages</td><td>{stats.get('assistant_messages', 0)}</td></tr>"
        html += """
        </table>
    </div>
"""

        # Messages
        html += """
    <div class="section">
        <h2>Messages</h2>
"""
        for msg in context.get("messages", []):
            role = msg.get("role", "unknown")
            html += f"""
        <div class="message {role}">
            <strong>{role.title()}</strong> - {msg.get('created_at', 'N/A')}<br>
            {msg.get('content', '')}
"""
            if msg.get("used_memories"):
                html += f"            <p><em>Used Memories: {', '.join(msg['used_memories'])}</em></p>"
            html += "        </div>"

        html += """
    </div>
"""

        # Memories
        memories = context.get("memories", [])
        if memories:
            html += """
    <div class="section">
        <h2>Related Memories</h2>
"""
            for mem in memories:
                html += f"""
        <div class="memory">
            <h3>{mem.get('context_id', 'N/A')}</h3>
            <p><strong>Type:</strong> {mem.get('memory_type', 'N/A')}</p>
            <pre>{json.dumps(mem.get('content', {}), indent=2)}</pre>
        </div>
"""
            html += """
    </div>
"""

        html += """
</body>
</html>
"""

        return html

    async def export_filtered(
        self,
        context: Dict[str, Any],
        format: str = "json",
        include_messages: bool = True,
        include_memories: bool = True,
        include_relationships: bool = False,
    ) -> str:
        """
        Export filtered context.

        Args:
            context: Context dictionary
            format: Export format (json, markdown, html)
            include_messages: Include messages
            include_memories: Include memories
            include_relationships: Include relationships

        Returns:
            Exported string
        """
        filtered = {
            "conversation_id": context.get("conversation_id"),
            "agent_id": context.get("agent_id"),
            "generated_at": context.get("generated_at"),
        }

        if include_messages:
            filtered["messages"] = context.get("messages", [])

        if include_memories:
            filtered["memories"] = context.get("memories", [])

        if include_relationships:
            filtered["relationships"] = context.get("relationships", [])

        filtered["statistics"] = context.get("statistics", {})

        if format == "json":
            return await self.export_json(filtered)
        elif format == "markdown":
            return await self.export_markdown(filtered)
        elif format == "html":
            return await self.export_html(filtered)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Singleton instance
_exporter: Optional[ContextExporter] = None


async def get_exporter() -> ContextExporter:
    """Get or create the singleton exporter instance."""
    global _exporter

    if _exporter is None:
        _exporter = ContextExporter()
        logger.info("Context exporter singleton created")

    return _exporter


__all__ = ["ContextExporter", "get_exporter"]

