"""
Comprehensive Tests for Agent Initialization

Tests cover:
- Agent initialization performance (< 500ms)
- Memory loading accuracy
- Context building
- Cache functionality
- Multiple agents concurrently
- Context window optimization
- State persistence

Target: 15+ test cases
"""

import time
from datetime import datetime, timezone
from typing import List

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Agent, Memory
from src.gml.services.agent_state_manager import get_state_manager
from src.gml.services.context_formatter import get_context_formatter
from src.gml.services.memory_cache_manager import get_cache_manager
from src.gml.services.memory_context_builder import get_context_builder


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest.fixture
async def sample_agent(db: AsyncSession) -> Agent:
    """Create a test agent."""
    agent = Agent(
        agent_id="test-agent-init",
        name="Test Agent",
        status="active",
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@pytest.fixture
async def sample_memories(db: AsyncSession, sample_agent: Agent) -> List[Memory]:
    """Create sample memories for testing."""
    memories = []
    for i in range(10):
        memory = Memory(
            context_id=f"ctx-init-test-{i:03d}",
            agent_id=sample_agent.agent_id,
            conversation_id="conv-init-001",
            content={"text": f"Test memory {i} for initialization"},
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

    return memories


# ============================================================================
# INITIALIZATION PERFORMANCE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_agent_init_performance(
    db: AsyncSession, sample_agent: Agent, sample_memories: List[Memory]
):
    """Test 1: Agent initialization completes in < 500ms."""
    from src.gml.services.memory_context_builder import get_context_builder

    builder = await get_context_builder()

    start_time = time.time()
    context = await builder.build_context(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-init-001",
        query="test",
        max_tokens=4000,
        strategy="hybrid",
        db=db,
    )
    elapsed_ms = (time.time() - start_time) * 1000

    assert elapsed_ms < 500, f"Initialization took {elapsed_ms}ms, expected <500ms"
    assert context["memories"] is not None


@pytest.mark.asyncio
async def test_memory_loading_accuracy(
    db: AsyncSession, sample_agent: Agent, sample_memories: List[Memory]
):
    """Test 2: Memory loading returns correct memories."""
    builder = await get_context_builder()

    context = await builder.build_context(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-init-001",
        query="test",
        max_tokens=4000,
        strategy="keyword",
        db=db,
    )

    assert len(context["memories"]) > 0
    # Verify memory context_ids match expected pattern
    assert all("context_id" in m for m in context["memories"])


@pytest.mark.asyncio
async def test_context_building(
    db: AsyncSession, sample_agent: Agent, sample_memories: List[Memory]
):
    """Test 3: Context building works correctly."""
    builder = await get_context_builder()

    context = await builder.build_context(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-init-001",
        query="test",
        max_tokens=4000,
        strategy="hybrid",
        db=db,
    )

    assert "formatted_context" in context
    assert "token_count" in context
    assert context["token_count"] > 0
    assert len(context["formatted_context"]) > 0


# ============================================================================
# CACHE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_cache_functionality(
    db: AsyncSession, sample_agent: Agent, sample_memories: List[Memory]
):
    """Test 4: Cache stores and retrieves contexts correctly."""
    cache_manager = await get_cache_manager()

    context = {
        "memories": [{"context_id": "ctx-1", "content": {"text": "test"}}],
        "formatted_context": "test context",
        "token_count": 100,
    }

    # Cache context
    cached = await cache_manager.cache_context(
        agent_id=sample_agent.agent_id,
        context=context,
        conversation_id="conv-001",
    )
    assert cached is True

    # Retrieve cached context
    retrieved = await cache_manager.get_cached_context(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-001",
    )
    assert retrieved is not None
    assert retrieved["formatted_context"] == context["formatted_context"]


@pytest.mark.asyncio
async def test_cache_invalidation(
    db: AsyncSession, sample_agent: Agent
):
    """Test 5: Cache invalidation works."""
    cache_manager = await get_cache_manager()

    context = {"memories": [], "formatted_context": "test"}

    # Cache context
    await cache_manager.cache_context(
        agent_id=sample_agent.agent_id,
        context=context,
        conversation_id="conv-001",
    )

    # Invalidate
    invalidated = await cache_manager.invalidate_context(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-001",
    )
    assert invalidated is True

    # Should not be retrievable
    retrieved = await cache_manager.get_cached_context(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-001",
    )
    assert retrieved is None


@pytest.mark.asyncio
async def test_cache_hit_rate(
    db: AsyncSession, sample_agent: Agent
):
    """Test 6: Cache hit rate improves with multiple requests."""
    cache_manager = await get_cache_manager()

    context = {"memories": [], "formatted_context": "test"}

    # Cache context
    await cache_manager.cache_context(
        agent_id=sample_agent.agent_id,
        context=context,
        conversation_id="conv-001",
    )

    # Multiple retrievals
    for _ in range(5):
        await cache_manager.get_cached_context(
            agent_id=sample_agent.agent_id,
            conversation_id="conv-001",
        )

    stats = cache_manager.get_cache_stats()
    assert stats["hits"] >= 5
    assert stats["hit_rate"] > 80


# ============================================================================
# CONTEXT FORMATTER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_context_formatter_narrative(
    sample_memories: List[Memory]
):
    """Test 7: Narrative format works correctly."""
    formatter = await get_context_formatter()

    formatted = formatter.format(
        memories=sample_memories[:3],
        format_type="narrative",
        include_metadata=True,
    )

    assert "Agent Memory Context" in formatted
    assert len(formatted) > 0


@pytest.mark.asyncio
async def test_context_formatter_qa(
    sample_memories: List[Memory]
):
    """Test 8: Q&A format works correctly."""
    formatter = await get_context_formatter()

    formatted = formatter.format(
        memories=sample_memories[:3],
        format_type="qa",
        include_metadata=True,
    )

    assert "Q&A Format" in formatted
    assert "Q1:" in formatted
    assert "A1:" in formatted


@pytest.mark.asyncio
async def test_context_formatter_structured(
    sample_memories: List[Memory]
):
    """Test 9: Structured format works correctly."""
    formatter = await get_context_formatter()

    formatted = formatter.format(
        memories=sample_memories[:3],
        format_type="structured",
        include_metadata=True,
    )

    assert "Structured" in formatted
    assert "context_id" in formatted


# ============================================================================
# STATE MANAGEMENT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_state_persistence(
    db: AsyncSession, sample_agent: Agent, sample_memories: List[Memory]
):
    """Test 10: Agent state persists correctly."""
    state_manager = await get_state_manager()
    builder = await get_context_builder()

    context = await builder.build_context(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-init-001",
        query="test",
        max_tokens=4000,
        strategy="hybrid",
        db=db,
    )

    state = await state_manager.initialize_agent(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-init-001",
        context=context,
        db=db,
    )

    assert state["agent_id"] == sample_agent.agent_id
    assert state["memories_loaded"] > 0

    # Retrieve state
    retrieved = await state_manager.get_state(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-init-001",
    )
    assert retrieved is not None
    assert retrieved["agent_id"] == sample_agent.agent_id


@pytest.mark.asyncio
async def test_state_update(
    db: AsyncSession, sample_agent: Agent
):
    """Test 11: State updates work correctly."""
    state_manager = await get_state_manager()

    # Initialize state
    state = await state_manager.initialize_agent(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-001",
        context={"memories": [], "token_count": 0, "sources": []},
        db=db,
    )

    # Update state
    updated = await state_manager.update_state(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-001",
        updates={"custom_field": "test"},
    )
    assert updated is True

    # Verify update
    retrieved = await state_manager.get_state(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-001",
    )
    assert retrieved["custom_field"] == "test"


@pytest.mark.asyncio
async def test_state_cleanup(
    db: AsyncSession, sample_agent: Agent
):
    """Test 12: State cleanup works correctly."""
    state_manager = await get_state_manager()

    # Initialize state
    await state_manager.initialize_agent(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-001",
        context={"memories": [], "token_count": 0, "sources": []},
        db=db,
    )

    # Cleanup
    cleaned = await state_manager.cleanup_agent(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-001",
        db=db,
    )
    assert cleaned is True

    # Should not be retrievable
    retrieved = await state_manager.get_state(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-001",
    )
    assert retrieved is None


# ============================================================================
# MULTIPLE AGENTS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_agents_concurrently(
    db: AsyncSession
):
    """Test 13: Multiple agents can be initialized concurrently."""
    import asyncio

    # Create multiple agents
    agents = []
    for i in range(3):
        agent = Agent(
            agent_id=f"test-agent-{i}",
            name=f"Test Agent {i}",
            status="active",
        )
        db.add(agent)
        agents.append(agent)

    await db.commit()
    for agent in agents:
        await db.refresh(agent)

    # Create memories for each
    for agent in agents:
        for j in range(5):
            memory = Memory(
                context_id=f"ctx-{agent.agent_id}-{j}",
                agent_id=agent.agent_id,
                conversation_id="conv-001",
                content={"text": f"Memory {j}"},
                memory_type="semantic",
                visibility="all",
                version=1,
                created_at=datetime.now(timezone.utc),
            )
            db.add(memory)

    await db.commit()

    # Initialize concurrently
    builder = await get_context_builder()
    tasks = [
        builder.build_context(
            agent_id=agent.agent_id,
            conversation_id="conv-001",
            query="test",
            max_tokens=1000,
            strategy="keyword",
            db=db,
        )
        for agent in agents
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 3
    assert all(r["memories"] for r in results)


# ============================================================================
# CONTEXT OPTIMIZATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_context_window_optimization(
    db: AsyncSession, sample_agent: Agent, sample_memories: List[Memory]
):
    """Test 14: Context window optimization works."""
    builder = await get_context_builder()

    # Request small context window
    context = await builder.build_context(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-init-001",
        query="test",
        max_tokens=500,  # Small limit
        strategy="hybrid",
        db=db,
    )

    # Should fit within limit
    assert context["token_count"] <= 500


@pytest.mark.asyncio
async def test_deduplication_across_strategies(
    db: AsyncSession, sample_agent: Agent, sample_memories: List[Memory]
):
    """Test 15: Memories are deduplicated across strategies."""
    builder = await get_context_builder()

    context = await builder.build_context(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-init-001",
        query="test",
        max_tokens=4000,
        strategy="all",  # Use all strategies
        db=db,
    )

    # Check for duplicates
    context_ids = [m["context_id"] for m in context["memories"]]
    assert len(context_ids) == len(set(context_ids)), "Found duplicate memories"


@pytest.mark.asyncio
async def test_no_memory_leaks(
    db: AsyncSession, sample_agent: Agent
):
    """Test 16: No memory leaks from state management."""
    state_manager = await get_state_manager()

    # Initialize and cleanup multiple times
    for i in range(10):
        await state_manager.initialize_agent(
            agent_id=sample_agent.agent_id,
            conversation_id=f"conv-{i}",
            context={"memories": [], "token_count": 0, "sources": []},
            db=db,
        )
        await state_manager.cleanup_agent(
            agent_id=sample_agent.agent_id,
            conversation_id=f"conv-{i}",
            db=db,
        )

    # Verify all cleaned up
    for i in range(10):
        state = await state_manager.get_state(
            agent_id=sample_agent.agent_id,
            conversation_id=f"conv-{i}",
        )
        assert state is None, f"State not cleaned up for conv-{i}"

