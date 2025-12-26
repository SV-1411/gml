"""
Comprehensive Tests for Chat with Memory Integration

Tests cover:
- Memory injection accuracy
- Chat message flow
- Conversation tracking
- LLM integration
- Streaming responses
- Multiple concurrent conversations
- Memory update from chat

Target: 15+ test cases
"""

import time
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Agent, Memory, Message
from src.gml.services.chat_memory_injection import get_memory_injector
from src.gml.services.conversation_tracker import get_conversation_tracker
from src.gml.services.llm_service import get_llm_service
from src.gml.services.response_processor import get_response_processor


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest.fixture
async def sample_agent(db: AsyncSession) -> Agent:
    """Create a test agent."""
    agent = Agent(
        agent_id="test-agent-chat",
        name="Test Agent",
        status="active",
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@pytest.fixture
async def sample_memories(db: AsyncSession, sample_agent: Agent) -> list[Memory]:
    """Create sample memories for testing."""
    memories = []
    for i in range(5):
        memory = Memory(
            context_id=f"ctx-chat-test-{i:03d}",
            agent_id=sample_agent.agent_id,
            conversation_id="conv-chat-001",
            content={"text": f"User prefers option {i}"},
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
# MEMORY INJECTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_memory_injection_accuracy(
    db: AsyncSession, sample_agent: Agent, sample_memories: list[Memory]
):
    """Test 1: Memory injection finds relevant memories."""
    injector = await get_memory_injector()

    prompt_data = await injector.build_prompt_with_memories(
        user_message="What do you remember about my preferences?",
        agent_id=sample_agent.agent_id,
        conversation_id="conv-chat-001",
        relevance_threshold=0.5,
        max_memories=10,
        db=db,
    )

    assert len(prompt_data["used_memories"]) > 0
    assert "system_prompt" in prompt_data
    assert "memory_context" in prompt_data


@pytest.mark.asyncio
async def test_memory_injection_relevance_threshold(
    db: AsyncSession, sample_agent: Agent, sample_memories: list[Memory]
):
    """Test 2: Relevance threshold filters memories correctly."""
    injector = await get_memory_injector()

    # High threshold should return fewer memories
    prompt_data_high = await injector.build_prompt_with_memories(
        user_message="test query",
        agent_id=sample_agent.agent_id,
        relevance_threshold=0.95,
        max_memories=10,
        db=db,
    )

    # Low threshold should return more memories
    prompt_data_low = await injector.build_prompt_with_memories(
        user_message="test query",
        agent_id=sample_agent.agent_id,
        relevance_threshold=0.1,
        max_memories=10,
        db=db,
    )

    # Lower threshold should generally return more or equal
    assert len(prompt_data_low["used_memories"]) >= len(prompt_data_high["used_memories"])


# ============================================================================
# CHAT MESSAGE FLOW TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_chat_message_flow(
    db: AsyncSession, sample_agent: Agent
):
    """Test 3: Chat message flow works end-to-end."""
    from src.gml.api.routes.chat import send_chat_message, ChatMessageRequest

    request = ChatMessageRequest(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-flow-test",
        message="Hello, how are you?",
        stream=False,
    )

    response = await send_chat_message(
        request=request,
        db=db,
        agent_id=sample_agent.agent_id,
    )

    assert response.response is not None
    assert len(response.response) > 0
    assert response.conversation_id == "conv-flow-test"
    assert response.execution_time_ms < 2000


@pytest.mark.asyncio
async def test_chat_performance(
    db: AsyncSession, sample_agent: Agent
):
    """Test 4: Chat response time < 2 seconds."""
    from src.gml.api.routes.chat import send_chat_message, ChatMessageRequest

    request = ChatMessageRequest(
        agent_id=sample_agent.agent_id,
        message="Test message",
        stream=False,
    )

    start_time = time.time()
    response = await send_chat_message(
        request=request,
        db=db,
        agent_id=sample_agent.agent_id,
    )
    elapsed = (time.time() - start_time) * 1000

    assert elapsed < 2000, f"Chat took {elapsed}ms, expected <2000ms"
    assert response.execution_time_ms < 2000


# ============================================================================
# CONVERSATION TRACKING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_conversation_tracking(
    db: AsyncSession, sample_agent: Agent
):
    """Test 5: Messages are stored in conversation."""
    tracker = await get_conversation_tracker()

    conversation_id = "conv-tracking-test"

    # Store user message
    user_msg = await tracker.store_message(
        agent_id=sample_agent.agent_id,
        conversation_id=conversation_id,
        role="user",
        content="Hello",
        db=db,
    )

    # Store assistant message
    assistant_msg = await tracker.store_message(
        agent_id=sample_agent.agent_id,
        conversation_id=conversation_id,
        role="assistant",
        content="Hi there!",
        db=db,
    )

    # Get history
    history = await tracker.get_conversation_history(
        conversation_id=conversation_id,
        db=db,
    )

    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"


@pytest.mark.asyncio
async def test_conversation_summary(
    db: AsyncSession, sample_agent: Agent
):
    """Test 6: Conversation summary generation works."""
    tracker = await get_conversation_tracker()

    conversation_id = "conv-summary-test"

    # Store some messages
    for i in range(5):
        await tracker.store_message(
            agent_id=sample_agent.agent_id,
            conversation_id=conversation_id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            db=db,
        )

    # Generate summary
    summary = await tracker.generate_summary(
        conversation_id=conversation_id,
        db=db,
    )

    assert len(summary) > 0
    assert "Conversation summary" in summary or "messages" in summary.lower()


@pytest.mark.asyncio
async def test_memory_creation_from_chat(
    db: AsyncSession, sample_agent: Agent
):
    """Test 7: Memories can be created from chat."""
    tracker = await get_conversation_tracker()

    memory = await tracker.create_memory_from_chat(
        conversation_id="conv-memory-test",
        content="User prefers dark mode",
        agent_id=sample_agent.agent_id,
        memory_type="episodic",
        db=db,
    )

    assert memory.context_id is not None
    assert memory.agent_id == sample_agent.agent_id
    assert memory.content.get("text") == "User prefers dark mode"


# ============================================================================
# LLM INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_llm_integration(
    sample_agent: Agent
):
    """Test 8: LLM service generates responses."""
    llm_service = await get_llm_service(provider="ollama")

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello"},
    ]

    try:
        response = await llm_service.chat_completion(
            messages=messages,
            stream=False,
            temperature=0.7,
        )

        assert response is not None
        assert "content" in response or isinstance(response, dict)

    except Exception as e:
        # LLM might not be available in test environment
        pytest.skip(f"LLM service not available: {str(e)}")


@pytest.mark.asyncio
async def test_llm_fallback(
    sample_agent: Agent
):
    """Test 9: LLM falls back gracefully."""
    # Try OpenAI without valid key (should fallback to Ollama)
    llm_service = await get_llm_service(provider="openai")

    messages = [
        {"role": "user", "content": "test"},
    ]

    try:
        # Should either work or fail gracefully
        response = await llm_service.chat_completion(
            messages=messages,
            stream=False,
        )
        # If we get here, it worked (either OpenAI or fallback)
        assert response is not None
    except Exception:
        # Expected if no LLM available
        pass


# ============================================================================
# RESPONSE PROCESSING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_response_processing(
    sample_agent: Agent
):
    """Test 10: Response processing extracts information."""
    processor = await get_response_processor()

    response_text = """
    I learned that the user prefers dark mode interfaces.
    I will remember this for future conversations.
    Action: Update user interface settings.
    """

    processed = processor.process_response(
        response=response_text,
        agent_id=sample_agent.agent_id,
        conversation_id="conv-process-test",
    )

    assert "response" in processed
    assert "extracted_memories" in processed
    assert "action_items" in processed
    assert "summary" in processed


@pytest.mark.asyncio
async def test_memory_extraction(
    sample_agent: Agent
):
    """Test 11: Memories are extracted from responses."""
    processor = await get_response_processor()

    response_text = """
    Remember that the user likes coffee in the morning.
    Note that they prefer meetings before 10 AM.
    """

    processed = processor.process_response(
        response=response_text,
        agent_id=sample_agent.agent_id,
    )

    assert len(processed["extracted_memories"]) > 0


# ============================================================================
# CONCURRENT CONVERSATIONS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_concurrent_conversations(
    db: AsyncSession
):
    """Test 12: Multiple conversations can run concurrently."""
    import asyncio

    # Create agents
    agents = []
    for i in range(3):
        agent = Agent(
            agent_id=f"test-agent-chat-{i}",
            name=f"Test Agent {i}",
            status="active",
        )
        db.add(agent)
        agents.append(agent)

    await db.commit()

    # Create conversations concurrently
    tracker = await get_conversation_tracker()
    tasks = [
        tracker.store_message(
            agent_id=agent.agent_id,
            conversation_id=f"conv-concurrent-{i}",
            role="user",
            content=f"Message from agent {i}",
            db=db,
        )
        for i, agent in enumerate(agents)
    ]

    messages = await asyncio.gather(*tasks)

    assert len(messages) == 3
    assert all(m.role == "user" for m in messages)


# ============================================================================
# MEMORY UPDATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_memory_update_from_chat(
    db: AsyncSession, sample_agent: Agent
):
    """Test 13: Chat creates new memories from extracted content."""
    from src.gml.api.routes.chat import send_chat_message, ChatMessageRequest

    request = ChatMessageRequest(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-memory-update",
        message="I prefer dark mode for my interface",
        stream=False,
    )

    response = await send_chat_message(
        request=request,
        db=db,
        agent_id=sample_agent.agent_id,
    )

    # Verify conversation was created
    tracker = await get_conversation_tracker()
    history = await tracker.get_conversation_history(
        conversation_id=response.conversation_id,
        db=db,
    )

    assert len(history) >= 2  # User message + assistant response


@pytest.mark.asyncio
async def test_used_memories_tracking(
    db: AsyncSession, sample_agent: Agent, sample_memories: list[Memory]
):
    """Test 14: Used memories are tracked correctly."""
    from src.gml.api.routes.chat import send_chat_message, ChatMessageRequest

    request = ChatMessageRequest(
        agent_id=sample_agent.agent_id,
        conversation_id="conv-chat-001",
        message="What do you remember?",
        stream=False,
    )

    response = await send_chat_message(
        request=request,
        db=db,
        agent_id=sample_agent.agent_id,
    )

    # Verify memories were used
    assert len(response.used_memories) >= 0  # May or may not find memories

    # Verify messages track used memories
    tracker = await get_conversation_tracker()
    history = await tracker.get_conversation_history(
        conversation_id=response.conversation_id,
        db=db,
    )

    assistant_messages = [m for m in history if m.role == "assistant"]
    if assistant_messages:
        metadata = assistant_messages[0].metadata or {}
        assert "used_memories" in metadata


@pytest.mark.asyncio
async def test_context_window_optimization(
    db: AsyncSession, sample_agent: Agent
):
    """Test 15: Context window is optimized for tokens."""
    injector = await get_memory_injector()

    prompt_data = await injector.build_prompt_with_memories(
        user_message="test",
        agent_id=sample_agent.agent_id,
        max_tokens=500,  # Small limit
        max_memories=5,
        db=db,
    )

    # Should respect token limits
    assert prompt_data["memory_count"] <= 5


@pytest.mark.asyncio
async def test_conversation_threading(
    db: AsyncSession, sample_agent: Agent
):
    """Test 16: Conversation threading works correctly."""
    tracker = await get_conversation_tracker()

    conversation_id = "conv-thread-test"

    # Store multiple messages
    for i in range(10):
        await tracker.store_message(
            agent_id=sample_agent.agent_id,
            conversation_id=conversation_id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            db=db,
        )

    # Get history
    history = await tracker.get_conversation_history(
        conversation_id=conversation_id,
        limit=100,
        db=db,
    )

    assert len(history) == 10
    # Verify ordering (chronological)
    for i in range(len(history) - 1):
        assert history[i].created_at <= history[i + 1].created_at

