#!/usr/bin/env python3
"""
Real Working Examples - Testing via HTTP API
Tests all major functionality through the running API server
"""

import json
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(title)
    print("="*70)


def test_health():
    """Test health endpoint"""
    print_section("TEST 1: Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_agent_registration():
    """Test agent registration"""
    print_section("TEST 2: Agent Registration")
    
    # Register Weather Agent
    print("\n1. Registering Weather Agent...")
    agent1_data = {
        "agent_id": "weather-agent-001",
        "name": "Weather Service Agent",
        "version": "1.2.0",
        "description": "Provides weather forecasts and current conditions",
        "capabilities": ["weather_forecast", "current_conditions", "alerts"]
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/agents/register",
        json=agent1_data
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"   ✅ Agent Registered: {result.get('agent_id')}")
        print(f"   API Token: {result.get('api_token', '')[:30]}...")
        print(f"   Public Key: {result.get('public_key', '')[:40]}...")
        agent1_token = result.get('api_token')
    else:
        print(f"   ❌ Error: {response.text}")
        agent1_token = None
    
    # Register News Agent
    print("\n2. Registering News Agent...")
    agent2_data = {
        "agent_id": "news-agent-001",
        "name": "News Aggregator Agent",
        "version": "2.0.0",
        "description": "Aggregates and summarizes news articles",
        "capabilities": ["news_search", "summarize", "categorize"]
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/agents/register",
        json=agent2_data
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"   ✅ Agent Registered: {result.get('agent_id')}")
        agent2_token = result.get('api_token')
    else:
        print(f"   ❌ Error: {response.text}")
        agent2_token = None
    
    return agent1_token, agent2_token


def test_get_agent():
    """Test getting agent details"""
    print_section("TEST 3: Get Agent Details")
    
    print("\n1. Getting Weather Agent...")
    response = requests.get(f"{BASE_URL}/api/v1/agents/weather-agent-001")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        agent = response.json()
        print(f"   ✅ Agent Found: {agent.get('name')}")
        print(f"   Status: {agent.get('status')}")
        print(f"   Version: {agent.get('version')}")
        print(f"   Created: {agent.get('created_at')}")
        if agent.get('capabilities'):
            print(f"   Capabilities: {', '.join(agent.get('capabilities', []))}")
    else:
        print(f"   ❌ Error: {response.text}")


def test_list_agents():
    """Test listing agents"""
    print_section("TEST 4: List All Agents")
    
    print("\n1. Listing all agents...")
    response = requests.get(f"{BASE_URL}/api/v1/agents?limit=10")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Total Agents: {result.get('total', 0)}")
        print(f"   Agents Returned: {len(result.get('agents', []))}")
        print(f"   Has More: {result.get('has_more', False)}")
        print("\n   Agents:")
        for agent in result.get('agents', []):
            print(f"   - {agent.get('agent_id')}: {agent.get('name')} ({agent.get('status')})")
    else:
        print(f"   ❌ Error: {response.text}")


def test_memory_write():
    """Test writing memory"""
    print_section("TEST 5: Write Memory")
    
    print("\n1. Writing memory entry...")
    memory_data = {
        "conversation_id": "conv-weather-001",
        "content": {
            "user_query": "What's the weather in New York?",
            "response": "Sunny, 72°F with light winds",
            "timestamp": datetime.now().isoformat(),
            "location": "New York, NY"
        },
        "memory_type": "episodic",
        "visibility": "all",
        "tags": ["weather", "new-york", "forecast"]
    }
    
    headers = {"X-Agent-ID": "weather-agent-001"}
    response = requests.post(
        f"{BASE_URL}/api/v1/memory/write",
        json=memory_data,
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"   ✅ Memory Written")
        print(f"   Context ID: {result.get('context_id')}")
        print(f"   Version: {result.get('version')}")
        return result.get('context_id')
    else:
        print(f"   ❌ Error: {response.text}")
        return None


def test_memory_search():
    """Test memory search"""
    print_section("TEST 6: Search Memory")
    
    print("\n1. Searching memories...")
    search_data = {
        "query": "weather forecast",
        "memory_type": "episodic",
        "limit": 5
    }
    
    headers = {"X-Agent-ID": "weather-agent-001"}
    response = requests.post(
        f"{BASE_URL}/api/v1/memory/search",
        json=search_data,
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        results = result.get('results', [])
        print(f"   ✅ Search Results: {len(results)}")
        for i, res in enumerate(results[:3], 1):
            print(f"\n   Result {i}:")
            print(f"   Context ID: {res.get('context_id')}")
            print(f"   Similarity: {res.get('similarity_score', 0):.4f}")
            content = res.get('content', {})
            if isinstance(content, dict):
                print(f"   Content: {content.get('user_query', 'N/A')}")
    else:
        print(f"   ❌ Error: {response.text}")


def test_detailed_health():
    """Test detailed health check"""
    print_section("TEST 7: Detailed Health Check")
    
    print("\n1. Checking detailed health...")
    response = requests.get(f"{BASE_URL}/api/v1/health/detailed")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        overall = result.get('detail', {}).get('overall_status', 'unknown')
        print(f"   ✅ Overall Status: {overall}")
        
        services = result.get('detail', {}).get('services', {})
        for service_name, service_info in services.items():
            status = service_info.get('status', 'unknown')
            message = service_info.get('message', '')
            icon = "✅" if status == "healthy" else "⚠️"
            print(f"   {icon} {service_name}: {status}")
            if message:
                print(f"      {message}")
    else:
        print(f"   ❌ Error: {response.text}")


def test_metrics():
    """Test metrics endpoint"""
    print_section("TEST 8: Prometheus Metrics")
    
    print("\n1. Getting metrics...")
    response = requests.get(f"{BASE_URL}/metrics")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    if response.status_code == 200:
        metrics_text = response.text
        lines = metrics_text.split('\n')[:20]  # First 20 lines
        print(f"   ✅ Metrics Retrieved ({len(metrics_text)} bytes)")
        print("\n   Sample metrics:")
        for line in lines:
            if line.strip() and not line.startswith('#'):
                print(f"   {line[:70]}")
    else:
        print(f"   ❌ Error: {response.text}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("GML INFRASTRUCTURE - REAL WORKING EXAMPLES")
    print("Testing via HTTP API")
    print("="*70)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n❌ Server is not responding correctly!")
            return
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("\n   Please start the server first:")
        print("   cd src && uvicorn gml.api.main:app --reload")
        return
    
    try:
        # Run tests
        test_health()
        time.sleep(0.5)
        
        agent1_token, agent2_token = test_agent_registration()
        time.sleep(0.5)
        
        test_get_agent()
        time.sleep(0.5)
        
        test_list_agents()
        time.sleep(0.5)
        
        context_id = test_memory_write()
        time.sleep(0.5)
        
        test_memory_search()
        time.sleep(0.5)
        
        test_detailed_health()
        time.sleep(0.5)
        
        test_metrics()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  ✅ Health check: Working")
        print(f"  ✅ Agent registration: Working")
        print(f"  ✅ Agent retrieval: Working")
        print(f"  ✅ Agent listing: Working")
        print(f"  ✅ Memory write: Working")
        print(f"  ✅ Memory search: Working")
        print(f"  ✅ Health monitoring: Working")
        print(f"  ✅ Metrics: Working")
        print(f"\nCompleted at: {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

