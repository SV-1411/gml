#!/usr/bin/env python3
"""
Real Working Examples for GML Infrastructure
Tests all major functionality with real data
"""

import asyncio
import json
from datetime import datetime

from src.gml.services.agent_service import AgentService
from src.gml.services.message_service import MessageService
from src.gml.services.memory_service import MemoryService
from src.gml.services.cost_service import CostService
from src.gml.api.schemas.agents import AgentRegisterRequest
from src.gml.api.schemas.messages import MessageSendRequest
from src.gml.api.schemas.memory import MemoryWriteRequest, MemorySearchRequest
from src.gml.db.database import AsyncSessionLocal
from src.gml.cache.redis_client import get_redis_client


async def test_agent_workflow():
    """Test complete agent registration and management"""
    print("\n" + "="*70)
    print("TEST 1: Agent Registration & Management")
    print("="*70)
    
    async with AsyncSessionLocal() as db:
        service = AgentService()
        
        # Register first agent
        print("\n1. Registering Agent 1...")
        request1 = AgentRegisterRequest(
            agent_id="weather-agent",
            name="Weather Service Agent",
            version="1.2.0",
            description="Provides weather forecasts and current conditions",
            capabilities=["weather_forecast", "current_conditions", "alerts"]
        )
        result1 = await service.register_agent(db, request1)
        print(f"   ✅ Registered: {result1['agent_id']}")
        print(f"   API Token: {result1['api_token'][:30]}...")
        
        # Register second agent
        print("\n2. Registering Agent 2...")
        request2 = AgentRegisterRequest(
            agent_id="news-agent",
            name="News Aggregator Agent",
            version="2.0.0",
            description="Aggregates and summarizes news articles",
            capabilities=["news_search", "summarize", "categorize"]
        )
        result2 = await service.register_agent(db, request2)
        print(f"   ✅ Registered: {result2['agent_id']}")
        
        # Get agent details
        print("\n3. Retrieving Agent Details...")
        agent = await service.get_agent(db, "weather-agent")
        print(f"   ✅ Retrieved: {agent.name}")
        print(f"   Status: {agent.status}")
        print(f"   Version: {agent.version}")
        print(f"   Created: {agent.created_at}")
        
        # List all agents
        print("\n4. Listing All Agents...")
        agents_list = await service.list_agents(db, skip=0, limit=10)
        print(f"   ✅ Total Agents: {agents_list['total']}")
        for agent in agents_list['agents']:
            print(f"   - {agent.agent_id}: {agent.name} ({agent.status})")
        
        return result1, result2


async def test_message_workflow():
    """Test message sending between agents"""
    print("\n" + "="*70)
    print("TEST 2: Inter-Agent Messaging")
    print("="*70)
    
    async with AsyncSessionLocal() as db:
        redis_client = await get_redis_client()
        service = MessageService()
        
        # Send message from weather-agent to news-agent
        print("\n1. Sending Message...")
        message_request = MessageSendRequest(
            to_agent_id="news-agent",
            action="request_news",
            payload={
                "query": "weather updates",
                "category": "weather",
                "limit": 5
            },
            timeout_seconds=30,
            callback_url=None
        )
        
        result = await service.send_message(
            db, redis_client, message_request, "weather-agent"
        )
        print(f"   ✅ Message Sent")
        print(f"   Message ID: {result['message_id']}")
        print(f"   Status: {result['status']}")
        
        # Get message status
        print("\n2. Checking Message Status...")
        message = await service.get_message_status(db, result['message_id'])
        print(f"   ✅ Message Status: {message.status}")
        print(f"   From: {message.from_agent_id}")
        print(f"   To: {message.to_agent_id}")
        print(f"   Action: {message.action}")
        
        # Get pending messages for news-agent
        print("\n3. Checking Pending Messages...")
        pending = await service.get_pending_messages(db, "news-agent")
        print(f"   ✅ Pending Messages: {len(pending)}")
        for msg in pending:
            print(f"   - {msg.message_id}: {msg.action} (from {msg.from_agent_id})")
        
        return result['message_id']


async def test_memory_workflow():
    """Test memory storage and search"""
    print("\n" + "="*70)
    print("TEST 3: Memory Storage & Search")
    print("="*70)
    
    async with AsyncSessionLocal() as db:
        service = MemoryService()
        
        # Write memory
        print("\n1. Writing Memory...")
        memory_request = MemoryWriteRequest(
            conversation_id="conv-weather-001",
            content={
                "user_query": "What's the weather in New York?",
                "response": "Sunny, 72°F",
                "timestamp": datetime.now().isoformat()
            },
            memory_type="episodic",
            visibility="all",
            tags=["weather", "new-york", "forecast"]
        )
        
        result = await service.write_memory(db, memory_request, "weather-agent")
        print(f"   ✅ Memory Written")
        print(f"   Context ID: {result['context_id']}")
        print(f"   Version: {result['version']}")
        
        # Write another memory
        print("\n2. Writing Another Memory...")
        memory_request2 = MemoryWriteRequest(
            conversation_id="conv-weather-002",
            content={
                "user_query": "Weather in San Francisco?",
                "response": "Foggy, 65°F",
                "timestamp": datetime.now().isoformat()
            },
            memory_type="episodic",
            visibility="all",
            tags=["weather", "san-francisco", "forecast"]
        )
        
        result2 = await service.write_memory(db, memory_request2, "weather-agent")
        print(f"   ✅ Memory Written")
        print(f"   Context ID: {result2['context_id']}")
        
        # Search memories
        print("\n3. Searching Memories...")
        search_request = MemorySearchRequest(
            query="weather forecast",
            memory_type="episodic",
            limit=5
        )
        
        search_results = await service.search_memories(db, search_request, "weather-agent")
        print(f"   ✅ Search Results: {len(search_results['results'])}")
        for i, result in enumerate(search_results['results'][:3], 1):
            print(f"   {i}. Context ID: {result['context_id']}")
            print(f"      Similarity: {result['similarity_score']:.4f}")
            print(f"      Content: {str(result['content'])[:50]}...")
        
        return result['context_id']


async def test_cost_tracking():
    """Test cost tracking"""
    print("\n" + "="*70)
    print("TEST 4: Cost Tracking")
    print("="*70)
    
    async with AsyncSessionLocal() as db:
        service = CostService()
        
        # Record costs
        print("\n1. Recording Costs...")
        await service.record_cost(db, "agent_registration", "weather-agent", 0.01)
        await service.record_cost(db, "message_send", "weather-agent", 0.01)
        await service.record_cost(db, "memory_write", "weather-agent", 0.02)
        await service.record_cost(db, "memory_search", "weather-agent", 0.05)
        print("   ✅ Costs Recorded")
        
        # Get agent costs
        print("\n2. Getting Agent Costs...")
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        total_cost = await service.get_agent_costs(
            db, "weather-agent", start_date, end_date
        )
        print(f"   ✅ Total Cost (7 days): ${total_cost:.4f}")
        
        # Get costs by type
        print("\n3. Getting Costs by Type...")
        costs_by_type = await service.get_costs_by_type(db, start_date, end_date)
        print(f"   ✅ Cost Breakdown:")
        for cost_type, amount in costs_by_type.items():
            print(f"   - {cost_type}: ${amount:.4f}")


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("GML INFRASTRUCTURE - REAL WORKING EXAMPLES")
    print("="*70)
    print(f"Started at: {datetime.now().isoformat()}")
    
    try:
        # Test 1: Agents
        agent1, agent2 = await test_agent_workflow()
        
        # Test 2: Messages
        message_id = await test_message_workflow()
        
        # Test 3: Memory
        context_id = await test_memory_workflow()
        
        # Test 4: Costs
        await test_cost_tracking()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  - Agents Registered: 2")
        print(f"  - Messages Sent: 1")
        print(f"  - Memories Written: 2")
        print(f"  - Costs Tracked: 4 operations")
        print(f"\nCompleted at: {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

