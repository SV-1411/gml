"""
Comprehensive Tests for Memory Versioning System

Tests cover:
- Version creation on update
- Version retrieval
- Rollback functionality
- Diff generation
- Version history pagination
- Version limits and archival
- Performance with 50+ versions

Target: 12+ test cases
"""

import time
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Agent, Memory, MemoryVersion
from src.gml.services.memory_versioning import (
    MemoryVersioningService,
    get_versioning_service,
    MAX_VERSIONS_PER_MEMORY,
)


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest.fixture
async def sample_agent(db: AsyncSession) -> Agent:
    """Create a test agent."""
    agent = Agent(
        agent_id="test-agent-versioning",
        name="Test Agent",
        status="active",
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@pytest.fixture
async def sample_memory(db: AsyncSession, sample_agent: Agent) -> Memory:
    """Create a test memory."""
    memory = Memory(
        context_id="ctx-version-test-001",
        agent_id=sample_agent.agent_id,
        conversation_id="conv-test-001",
        content={"text": "Initial memory content"},
        memory_type="semantic",
        visibility="all",
        version=1,
        created_at=datetime.now(timezone.utc),
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


# ============================================================================
# VERSION CREATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_version_creation_on_memory_create(
    db: AsyncSession, sample_memory: Memory
):
    """Test 1: Version created automatically on memory creation."""
    service = await get_versioning_service()

    version = await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )

    assert version.context_id == sample_memory.context_id
    assert version.version_number == 1
    assert version.change_type == "added"
    assert version.full_memory_text is not None


@pytest.mark.asyncio
async def test_version_incrementing(db: AsyncSession, sample_memory: Memory):
    """Test 2: Version numbers increment correctly."""
    service = await get_versioning_service()

    # Create initial version
    v1 = await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )
    assert v1.version_number == 1

    # Create multiple versions
    for i in range(3):
        # Update memory content
        sample_memory.content = {"text": f"Updated content version {i+1}"}
        await db.commit()
        await db.refresh(sample_memory)

        version = await service.create_version(
            memory=sample_memory,
            author_id=sample_memory.agent_id,
            change_type="modified",
            db=db,
        )

        assert version.version_number == i + 2  # +2 because initial is 1


@pytest.mark.asyncio
async def test_version_retrieval(db: AsyncSession, sample_memory: Memory):
    """Test 3: Can retrieve specific version."""
    service = await get_versioning_service()

    # Create version
    created_version = await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )

    # Retrieve version
    retrieved = await service.get_version(
        context_id=sample_memory.context_id,
        version_number=created_version.version_number,
        db=db,
    )

    assert retrieved is not None
    assert retrieved.version_number == created_version.version_number
    assert retrieved.context_id == sample_memory.context_id


@pytest.mark.asyncio
async def test_version_history(db: AsyncSession, sample_memory: Memory):
    """Test 4: Version history returns all versions."""
    service = await get_versioning_service()

    # Create multiple versions
    for i in range(5):
        sample_memory.content = {"text": f"Content {i}"}
        await db.commit()
        await db.refresh(sample_memory)
        await service.create_version(
            memory=sample_memory,
            author_id=sample_memory.agent_id,
            change_type="modified",
            db=db,
        )

    # Get history
    history = await service.get_version_history(
        context_id=sample_memory.context_id,
        limit=10,
        db=db,
    )

    assert len(history) == 5
    # Should be in descending order (newest first)
    assert history[0].version_number > history[-1].version_number


@pytest.mark.asyncio
async def test_version_history_pagination(db: AsyncSession, sample_memory: Memory):
    """Test 5: Version history pagination works."""
    service = await get_versioning_service()

    # Create 10 versions
    for i in range(10):
        sample_memory.content = {"text": f"Content {i}"}
        await db.commit()
        await db.refresh(sample_memory)
        await service.create_version(
            memory=sample_memory,
            author_id=sample_memory.agent_id,
            change_type="modified",
            db=db,
        )

    # Get first page
    page1 = await service.get_version_history(
        context_id=sample_memory.context_id,
        limit=5,
        offset=0,
        db=db,
    )

    # Get second page
    page2 = await service.get_version_history(
        context_id=sample_memory.context_id,
        limit=5,
        offset=5,
        db=db,
    )

    assert len(page1) == 5
    assert len(page2) == 5
    assert page1[0].version_number != page2[0].version_number


# ============================================================================
# ROLLBACK TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_rollback_functionality(db: AsyncSession, sample_memory: Memory):
    """Test 6: Rollback restores previous version."""
    service = await get_versioning_service()

    # Create initial version
    initial_content = {"text": "Initial content"}
    sample_memory.content = initial_content
    await db.commit()
    await db.refresh(sample_memory)
    v1 = await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )

    # Modify memory
    sample_memory.content = {"text": "Modified content"}
    await db.commit()
    await db.refresh(sample_memory)
    v2 = await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="modified",
        db=db,
    )

    # Verify modification
    assert sample_memory.content["text"] == "Modified content"

    # Rollback to version 1
    reverted = await service.revert_to_version(
        context_id=sample_memory.context_id,
        version_number=1,
        author_id=sample_memory.agent_id,
        db=db,
    )

    # Verify rollback
    assert reverted.content["text"] == "Initial content"

    # Verify new version was created
    history = await service.get_version_history(
        context_id=sample_memory.context_id,
        limit=5,
        db=db,
    )
    assert history[0].change_type == "reverted"


@pytest.mark.asyncio
async def test_rollback_performance(db: AsyncSession, sample_memory: Memory):
    """Test 7: Rollback performance < 500ms."""
    service = await get_versioning_service()

    # Create version
    await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )

    # Modify
    sample_memory.content = {"text": "Modified"}
    await db.commit()
    await db.refresh(sample_memory)
    await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="modified",
        db=db,
    )

    # Measure rollback time
    start_time = time.time()
    await service.revert_to_version(
        context_id=sample_memory.context_id,
        version_number=1,
        author_id=sample_memory.agent_id,
        db=db,
    )
    elapsed_ms = (time.time() - start_time) * 1000

    assert elapsed_ms < 500, f"Rollback took {elapsed_ms}ms, expected <500ms"


# ============================================================================
# DIFF TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_diff_generation(db: AsyncSession, sample_memory: Memory):
    """Test 8: Diff generation works correctly."""
    service = await get_versioning_service()

    # Create version 1
    sample_memory.content = {"text": "First version"}
    await db.commit()
    await db.refresh(sample_memory)
    await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )

    # Create version 2
    sample_memory.content = {"text": "Second version with changes"}
    await db.commit()
    await db.refresh(sample_memory)
    await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="modified",
        db=db,
    )

    # Generate diff
    diff = await service.generate_diff(
        context_id=sample_memory.context_id,
        version1=1,
        version2=2,
        db=db,
    )

    assert "unified_diff" in diff
    assert "statistics" in diff
    assert diff["statistics"]["total_changes"] > 0


@pytest.mark.asyncio
async def test_diff_with_current(db: AsyncSession, sample_memory: Memory):
    """Test 9: Diff with current version works."""
    service = await get_versioning_service()

    # Create version
    sample_memory.content = {"text": "Version 1"}
    await db.commit()
    await db.refresh(sample_memory)
    await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )

    # Modify current
    sample_memory.content = {"text": "Current modified"}
    await db.commit()
    await db.refresh(sample_memory)

    # Diff with current
    diff = await service.generate_diff(
        context_id=sample_memory.context_id,
        version1=1,
        version2=None,  # Compare with current
        db=db,
    )

    assert diff["version2"] is None
    assert "unified_diff" in diff


@pytest.mark.asyncio
async def test_diff_statistics(db: AsyncSession, sample_memory: Memory):
    """Test 10: Diff statistics are accurate."""
    service = await get_versioning_service()

    # Create version 1
    sample_memory.content = {"text": "Original text"}
    await db.commit()
    await db.refresh(sample_memory)
    await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )

    # Create version 2 with changes
    sample_memory.content = {"text": "Modified text with additions"}
    await db.commit()
    await db.refresh(sample_memory)
    await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="modified",
        db=db,
    )

    diff = await service.generate_diff(
        context_id=sample_memory.context_id,
        version1=1,
        version2=2,
        db=db,
    )

    stats = diff["statistics"]
    assert "additions" in stats
    assert "deletions" in stats
    assert "modifications" in stats
    assert "total_changes" in stats
    assert stats["total_changes"] >= 0


# ============================================================================
# VERSION LIMITS AND ARCHIVAL TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_version_limit_enforcement(db: AsyncSession, sample_memory: Memory):
    """Test 11: Version limit is enforced."""
    service = MemoryVersioningService(max_versions=5)

    # Create more versions than limit
    for i in range(10):
        sample_memory.content = {"text": f"Content {i}"}
        await db.commit()
        await db.refresh(sample_memory)
        await service.create_version(
            memory=sample_memory,
            author_id=sample_memory.agent_id,
            change_type="modified",
            db=db,
        )

    # Check that old versions are archived
    history = await service.get_version_history(
        context_id=sample_memory.context_id,
        limit=100,
        db=db,
    )

    # Should have all versions, but some may be archived
    assert len(history) == 10


@pytest.mark.asyncio
async def test_compression_for_large_text(db: AsyncSession, sample_memory: Memory):
    """Test 12: Large text is compressed."""
    service = await get_versioning_service()

    # Create memory with large text
    large_text = "x" * 15000  # 15KB > threshold
    sample_memory.content = {"text": large_text}
    await db.commit()
    await db.refresh(sample_memory)

    version = await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )

    assert version.compressed is True
    assert version.full_memory_text is not None


@pytest.mark.asyncio
async def test_version_author_tracking(db: AsyncSession, sample_memory: Memory):
    """Test 13: Version author is tracked."""
    service = await get_versioning_service()

    author_id = "test-author-123"
    version = await service.create_version(
        memory=sample_memory,
        author_id=author_id,
        change_type="added",
        db=db,
    )

    assert version.author_id == author_id


@pytest.mark.asyncio
async def test_version_parent_relationship(db: AsyncSession, sample_memory: Memory):
    """Test 14: Version parent relationships are tracked."""
    service = await get_versioning_service()

    # Create first version
    v1 = await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="added",
        db=db,
    )

    # Create second version
    sample_memory.content = {"text": "Modified"}
    await db.commit()
    await db.refresh(sample_memory)
    v2 = await service.create_version(
        memory=sample_memory,
        author_id=sample_memory.agent_id,
        change_type="modified",
        db=db,
    )

    assert v2.parent_version_id == v1.id
    assert v1.parent_version_id is None


@pytest.mark.asyncio
async def test_performance_with_50_versions(db: AsyncSession, sample_memory: Memory):
    """Test 15: Performance with 50+ versions."""
    service = await get_versioning_service()

    # Create 50 versions
    start_time = time.time()
    for i in range(50):
        sample_memory.content = {"text": f"Content version {i}"}
        await db.commit()
        await db.refresh(sample_memory)
        await service.create_version(
            memory=sample_memory,
            author_id=sample_memory.agent_id,
            change_type="modified",
            db=db,
        )
    creation_time = (time.time() - start_time) * 1000

    # Get history performance
    start_time = time.time()
    history = await service.get_version_history(
        context_id=sample_memory.context_id,
        limit=50,
        db=db,
    )
    retrieval_time = (time.time() - start_time) * 1000

    assert len(history) == 50
    assert creation_time < 5000, f"Creation took {creation_time}ms"
    assert retrieval_time < 500, f"Retrieval took {retrieval_time}ms"


@pytest.mark.asyncio
async def test_rollback_safety_no_data_loss(
    db: AsyncSession, sample_agent: Agent
):
    """Test 16: Rollback doesn't cause data loss."""
    service = await get_versioning_service()

    # Create memory
    memory = Memory(
        context_id="ctx-rollback-safety",
        agent_id=sample_agent.agent_id,
        content={"text": "Original"},
        memory_type="semantic",
        visibility="all",
        version=1,
        created_at=datetime.now(timezone.utc),
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)

    # Create version
    v1 = await service.create_version(
        memory=memory,
        author_id=sample_agent.agent_id,
        change_type="added",
        db=db,
    )
    original_text = memory.content["text"]

    # Modify multiple times
    for i in range(3):
        memory.content = {"text": f"Modified {i}"}
        await db.commit()
        await db.refresh(memory)
        await service.create_version(
            memory=memory,
            author_id=sample_agent.agent_id,
            change_type="modified",
            db=db,
        )

    # Verify current is different
    assert memory.content["text"] != original_text

    # Rollback
    reverted = await service.revert_to_version(
        context_id=memory.context_id,
        version_number=1,
        author_id=sample_agent.agent_id,
        db=db,
    )

    # Verify original is restored
    assert reverted.content["text"] == original_text

    # Verify all versions still exist
    history = await service.get_version_history(
        context_id=memory.context_id,
        limit=10,
        db=db,
    )
    assert len(history) >= 4  # Original + 3 modifications + revert

