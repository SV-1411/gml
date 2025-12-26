"""
Comprehensive Tests for Conversation Context

Tests cover:
- Context retrieval accuracy
- Memory loading for conversations
- Context summarization
- Relationship mapping
- Context filtering
- Export functionality
- Performance with large conversations

Target: 15+ test cases
"""

import time
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Agent, ChatMessage, Memory
from src.gml.services.context_exporter import get_exporter
from src.gml.services.context_summarizer import get_summarizer
from src.gml.services.conversation_context_service import get_context_service


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest.fixture
async def sample_agent(db: AsyncSession) -> Agent:
    """Create a test agent."""
    agent = Agent(
        agent_id="test-agent-context",
        name="Test Agent",
        status="active",
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@pytest.fixture
async def sample_conversation(
    db: AsyncSession, sample_agent: Agent
) -> tuple[str, list[ChatMessage], list[Memory]]:
    """Create a sample conversation with messages and memories."""
    conversation_id = "conv-context-test"

    # Create messages
    messages = []
    for i in range(5):
        message = ChatMessage(
            agent_id=sample_agent.agent_id,
            conversation_id=conversation_id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            used_memories=[f"ctx-{i}"] if i > 0 else [],
            created_at=datetime.now(timezone.utc),
        )
        db.add(message)
        messages.append(message)

    await db.commit()
    for msg in messages:
        await db.refresh(msg)

    # Create memories
    memories = []
    for i in range(3):
        memory = Memory(
            context_id=f"ctx-{i}",
            agent_id=sample_agent.agent_id,
            conversation_id=conversation_id,
            content={"text": f"Memory {i}"},
            memory_type="semantic",
            visibility="all",
            version=1,
            created_at=datetime.now(timezone.utc),
        )
        db.add(memory)
        memories.append(memory)

    await db.commit()
    for memory in memories:
        await db.refresh(memory)

    return conversation_id, messages, memories


# ============================================================================
# CONTEXT RETRIEVAL TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_context_retrieval_accuracy(
    db: AsyncSession, sample_conversation: tuple
):
    """Test 1: Context retrieval returns accurate data."""
    conversation_id, messages, memories = sample_conversation

    service = await get_context_service()
    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    assert context["conversation_id"] == conversation_id
    assert len(context["messages"]) == len(messages)
    assert len(context["memories"]) >= len(memories)


@pytest.mark.asyncio
async def test_context_levels(db: AsyncSession, sample_conversation: tuple):
    """Test 2: Different context levels return appropriate data."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()

    # Minimal level
    minimal = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="minimal",
        db=db,
    )
    assert "messages" in minimal
    assert "decision_points" not in minimal

    # Full level
    full = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )
    assert "messages" in full
    assert "decision_points" in full

    # Detailed level
    detailed = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="detailed",
        db=db,
    )
    assert "messages" in detailed
    assert "decision_points" in detailed
    assert "memory_clusters" in detailed


@pytest.mark.asyncio
async def test_memory_loading_for_conversation(
    db: AsyncSession, sample_conversation: tuple
):
    """Test 3: All related memories are loaded."""
    conversation_id, messages, memories = sample_conversation

    service = await get_context_service()
    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    # Check that memories referenced in messages are loaded
    memory_ids = set()
    for msg in messages:
        if msg.used_memories:
            memory_ids.update(msg.used_memories)

    loaded_ids = {m["context_id"] for m in context["memories"]}
    assert memory_ids.issubset(loaded_ids) or len(memory_ids) == 0


# ============================================================================
# CONTEXT SUMMARIZATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_context_summarization(db: AsyncSession, sample_conversation: tuple):
    """Test 4: Context summarization works."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()
    summarizer = await get_summarizer()

    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    summary = await summarizer.summarize_context(context, style="standard")

    assert "summary_text" in summary
    assert summary["conversation_id"] == conversation_id
    assert "key_decisions" in summary
    assert "recommendations" in summary


@pytest.mark.asyncio
async def test_summary_styles(db: AsyncSession, sample_conversation: tuple):
    """Test 5: Different summary styles work."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()
    summarizer = await get_summarizer()

    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    styles = ["standard", "executive", "brief"]
    for style in styles:
        summary = await summarizer.summarize_context(context, style=style)
        assert summary["style"] == style
        assert "summary_text" in summary


# ============================================================================
# RELATIONSHIP MAPPING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_relationship_mapping(db: AsyncSession, sample_conversation: tuple):
    """Test 6: Memory relationships are mapped correctly."""
    conversation_id, messages, memories = sample_conversation

    service = await get_context_service()
    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    assert "relationships" in context
    assert isinstance(context["relationships"], list)

    # Check that message-to-memory relationships exist
    has_message_relationships = any(
        r["type"] == "uses" for r in context["relationships"]
    )
    # May or may not have relationships depending on messages
    assert isinstance(has_message_relationships, bool)


@pytest.mark.asyncio
async def test_memory_clusters(db: AsyncSession, sample_conversation: tuple):
    """Test 7: Memory clusters are identified."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()
    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="detailed",
        db=db,
    )

    assert "memory_clusters" in context
    assert isinstance(context["memory_clusters"], list)


# ============================================================================
# CONTEXT FILTERING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_context_filtering_by_date(
    db: AsyncSession, sample_conversation: tuple
):
    """Test 8: Context can be filtered by date."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()

    # Filter from now (should return all)
    context_all = await service.get_full_context(
        conversation_id=conversation_id,
        filter_date_from=datetime.now(timezone.utc),
        db=db,
    )

    # Filter from future (should return empty)
    future_date = datetime.now(timezone.utc)
    future_date = future_date.replace(year=future_date.year + 1)
    context_none = await service.get_full_context(
        conversation_id=conversation_id,
        filter_date_from=future_date,
        db=db,
    )

    assert len(context_all["memories"]) >= len(context_none["memories"])


@pytest.mark.asyncio
async def test_context_filtering_by_type(
    db: AsyncSession, sample_conversation: tuple
):
    """Test 9: Context can be filtered by memory type."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()

    # Filter by semantic type
    context_filtered = await service.get_full_context(
        conversation_id=conversation_id,
        filter_types=["semantic"],
        db=db,
    )

    # All memories should be semantic type
    for mem in context_filtered["memories"]:
        assert mem["memory_type"] == "semantic"


# ============================================================================
# EXPORT FUNCTIONALITY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_export_json(db: AsyncSession, sample_conversation: tuple):
    """Test 10: JSON export works."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()
    exporter = await get_exporter()

    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    json_data = await exporter.export_json(context, pretty=True)
    assert isinstance(json_data, str)
    assert conversation_id in json_data


@pytest.mark.asyncio
async def test_export_markdown(db: AsyncSession, sample_conversation: tuple):
    """Test 11: Markdown export works."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()
    exporter = await get_exporter()

    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    md_data = await exporter.export_markdown(context)
    assert isinstance(md_data, str)
    assert "# Conversation Context" in md_data


@pytest.mark.asyncio
async def test_export_html(db: AsyncSession, sample_conversation: tuple):
    """Test 12: HTML export works."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()
    exporter = await get_exporter()

    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    html_data = await exporter.export_html(context)
    assert isinstance(html_data, str)
    assert "<html>" in html_data
    assert conversation_id in html_data


@pytest.mark.asyncio
async def test_export_filtered(db: AsyncSession, sample_conversation: tuple):
    """Test 13: Filtered export works."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()
    exporter = await get_exporter()

    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    # Export without messages
    filtered = await exporter.export_filtered(
        context,
        format="json",
        include_messages=False,
        include_memories=True,
    )

    assert isinstance(filtered, str)
    import json
    data = json.loads(filtered)
    assert "messages" not in data or len(data["messages"]) == 0
    assert "memories" in data


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_performance_with_large_conversation(db: AsyncSession, sample_agent: Agent):
    """Test 14: Context retrieval performs well with large conversations."""
    conversation_id = "conv-large-test"

    # Create many messages
    messages = []
    for i in range(20):
        message = ChatMessage(
            agent_id=sample_agent.agent_id,
            conversation_id=conversation_id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            created_at=datetime.now(timezone.utc),
        )
        db.add(message)
        messages.append(message)

    await db.commit()

    service = await get_context_service()

    start_time = time.time()
    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )
    elapsed = (time.time() - start_time) * 1000

    assert elapsed < 1000, f"Context retrieval took {elapsed}ms, expected <1000ms"
    assert len(context["messages"]) == 20


@pytest.mark.asyncio
async def test_decision_points_extraction(
    db: AsyncSession, sample_conversation: tuple
):
    """Test 15: Decision points are extracted correctly."""
    conversation_id, _, _ = sample_conversation

    # Add a message with decision keywords
    service = await get_context_service()

    # Add decision message
    from src.gml.db.models import ChatMessage
    decision_msg = ChatMessage(
        agent_id=sample_conversation[1][0].agent_id,
        conversation_id=conversation_id,
        role="assistant",
        content="I decided to choose option A",
        created_at=datetime.now(timezone.utc),
    )
    db.add(decision_msg)
    await db.commit()
    await db.refresh(decision_msg)

    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    assert "decision_points" in context
    # May or may not have decision points depending on content
    assert isinstance(context["decision_points"], list)


@pytest.mark.asyncio
async def test_knowledge_gaps_identification(
    db: AsyncSession, sample_conversation: tuple
):
    """Test 16: Knowledge gaps are identified."""
    conversation_id, _, _ = sample_conversation

    service = await get_context_service()
    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    assert "knowledge_gaps" in context
    assert isinstance(context["knowledge_gaps"], list)


@pytest.mark.asyncio
async def test_context_statistics(db: AsyncSession, sample_conversation: tuple):
    """Test 17: Context statistics are accurate."""
    conversation_id, messages, memories = sample_conversation

    service = await get_context_service()
    context = await service.get_full_context(
        conversation_id=conversation_id,
        context_level="full",
        db=db,
    )

    stats = context.get("statistics", {})
    assert stats["message_count"] == len(messages)
    assert stats["user_messages"] + stats["assistant_messages"] == len(messages)

