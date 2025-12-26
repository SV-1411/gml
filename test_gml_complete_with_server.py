#!/usr/bin/env python3
"""
Complete GML Test - Checks Server First

Tests complete GML workflow, but checks if server is running first.
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import httpx
from openai import AsyncOpenAI

OLLAMA_BASE_URL = "http://localhost:11434/v1"
API_BASE_URL = "http://localhost:8000"


async def check_server():
    """Check if API server is running"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                return True, "Server is running"
            return False, f"Server returned {response.status_code}"
    except Exception as e:
        return False, f"Server not accessible: {str(e)}"


async def test_ollama_models():
    """Test both Ollama models"""
    print("\n" + "="*70)
    print("TEST: Both Ollama Models")
    print("="*70)
    
    models = [
        ("gpt-oss:20b", "Explain multi-agent systems in 2 sentences."),
        ("gemini-3-flash-preview:cloud", "Explain multi-agent systems in 2 sentences.")
    ]
    
    client = AsyncOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
        timeout=httpx.Timeout(120.0),
    )
    
    for model_name, prompt in models:
        print(f"\n1. Testing {model_name}...")
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            print(f"   ✅ Response ({len(content)} chars):")
            print(f"   {content[:200]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")


async def test_agent_registration():
    """Test agent registration if server is running"""
    print("\n" + "="*70)
    print("TEST: Agent Registration")
    print("="*70)
    
    server_ok, message = await check_server()
    if not server_ok:
        print(f"   ⚠️  {message}")
        print("\n   To start the server:")
        print("   cd src && python -m uvicorn gml.api.main:app --reload")
        print("   Or run: ./START_SERVER.sh")
        return
    
    print(f"   ✅ {message}")
    
    agent_data = {
        "agent_id": "weather-ollama-test",
        "name": "Weather Agent (Ollama)",
        "version": "1.0.0",
        "description": "Test agent with Ollama",
        "capabilities": ["weather", "llm"]
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/agents/register",
                json=agent_data
            )
            if response.status_code == 201:
                result = response.json()
                print(f"\n   ✅ Agent registered: {result.get('agent_id')}")
            else:
                print(f"\n   ⚠️  Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"\n   ❌ Error: {e}")


async def main():
    """Run tests"""
    print("\n" + "="*70)
    print("GML COMPLETE TEST - With Server Check")
    print("="*70)
    
    # Test Ollama models (always works)
    await test_ollama_models()
    
    # Test agent registration (needs server)
    await test_agent_registration()
    
    print("\n" + "="*70)
    print("✅ TESTS COMPLETED")
    print("="*70)
    print("\nNote: Agent registration requires the API server to be running.")
    print("Ollama model tests work independently.")


if __name__ == "__main__":
    asyncio.run(main())

