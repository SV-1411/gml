#!/usr/bin/env python3
"""
Test Ollama Integration with GML Infrastructure

Tests the Ollama service with GPT-OSS 20B model.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gml.services.ollama_service import OllamaService, get_ollama_service


async def test_ollama_health():
    """Test Ollama health check"""
    print("\n" + "="*70)
    print("TEST 1: Ollama Health Check")
    print("="*70)
    
    service = OllamaService()
    healthy, message = await service.health_check()
    
    if healthy:
        print(f"✅ Ollama is healthy: {message}")
    else:
        print(f"❌ Ollama health check failed: {message}")
        print("\n⚠️  Make sure Ollama is running:")
        print("   ollama serve")
        print("   ollama pull gpt-oss:20b")
    
    return healthy


async def test_list_models():
    """Test listing available Ollama models"""
    print("\n" + "="*70)
    print("TEST 2: List Available Models")
    print("="*70)
    
    service = OllamaService()
    models = await service.list_models()
    
    if models:
        print(f"✅ Found {len(models)} models:")
        for model in models:
            print(f"   - {model}")
    else:
        print("⚠️  No models found or Ollama not accessible")
    
    return len(models) > 0


async def test_simple_chat():
    """Test simple chat completion"""
    print("\n" + "="*70)
    print("TEST 3: Simple Chat Completion")
    print("="*70)
    
    try:
        service = OllamaService()
        
        print("\n1. Sending message to Ollama...")
        response = await service.simple_chat(
            user_message="Explain what MXFP4 quantization is in one sentence.",
            system_message="You are a helpful AI assistant."
        )
        
        print(f"✅ Response received:")
        print(f"\n{response}\n")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n⚠️  Make sure:")
        print("   1. Ollama is running: ollama serve")
        print("   2. Model is pulled: ollama pull gpt-oss:20b")
        return False


async def test_chat_completion():
    """Test full chat completion API"""
    print("\n" + "="*70)
    print("TEST 4: Full Chat Completion API")
    print("="*70)
    
    try:
        service = OllamaService()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Answer in one word."}
        ]
        
        print("\n1. Sending chat completion request...")
        response = await service.chat_completion(messages)
        
        print(f"✅ Response received:")
        print(f"   Model: {response.model}")
        print(f"   Content: {response.choices[0].message.content}")
        print(f"   Finish Reason: {response.choices[0].finish_reason}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_function_calling():
    """Test function calling (tools)"""
    print("\n" + "="*70)
    print("TEST 5: Function Calling (Tools)")
    print("="*70)
    
    try:
        service = OllamaService()
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather in a given city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "The city name"}
                        },
                        "required": ["city"]
                    },
                },
            }
        ]
        
        print("\n1. Sending message with function tools...")
        response = await service.chat_with_tools(
            user_message="What's the weather in Berlin right now?",
            tools=tools,
            system_message="You are a helpful assistant that can check weather."
        )
        
        print(f"✅ Response received:")
        message = response.choices[0].message
        
        if message.content:
            print(f"   Content: {message.content}")
        
        if message.tool_calls:
            print(f"   Tool Calls: {len(message.tool_calls)}")
            for tool_call in message.tool_calls:
                print(f"   - Function: {tool_call.function.name}")
                print(f"     Arguments: {tool_call.function.arguments}")
        else:
            print("   No tool calls (model may have answered directly)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_with_agent():
    """Test integration with GML agent system"""
    print("\n" + "="*70)
    print("TEST 6: Integration with GML Agent System")
    print("="*70)
    
    try:
        from src.gml.services.agent_service import AgentService
        from src.gml.api.schemas.agents import AgentRegisterRequest
        from src.gml.db.database import get_session_factory
        
        # Register an agent that uses Ollama
        async with get_session_factory()() as db:
            service = AgentService()
            
            request = AgentRegisterRequest(
                agent_id="ollama-agent-001",
                name="Ollama-Powered Agent",
                version="1.0.0",
                description="Agent powered by GPT-OSS 20B via Ollama",
                capabilities=["llm", "chat", "reasoning"]
            )
            
            result = await service.register_agent(db, request)
            print(f"✅ Agent registered: {result['agent_id']}")
            
            # Now test Ollama with this agent
            ollama_service = OllamaService()
            response = await ollama_service.simple_chat(
                user_message=f"Your agent ID is {result['agent_id']}. Say hello!",
                system_message="You are an AI agent in the GML infrastructure."
            )
            
            print(f"\n✅ Ollama response for agent:")
            print(f"{response}\n")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("OLLAMA INTEGRATION TEST - GPT-OSS 20B")
    print("="*70)
    print("\nPrerequisites:")
    print("  1. Ollama installed and running: ollama serve")
    print("  2. Model pulled: ollama pull gpt-oss:20b")
    print("  3. Ollama accessible at: http://localhost:11434")
    print()
    
    results = []
    
    # Test 1: Health check
    results.append(await test_ollama_health())
    
    if not results[0]:
        print("\n" + "="*70)
        print("❌ Ollama is not available. Please start Ollama first.")
        print("="*70)
        print("\nSetup commands:")
        print("  ollama serve")
        print("  ollama pull gpt-oss:20b")
        return
    
    # Test 2: List models
    results.append(await test_list_models())
    
    # Test 3: Simple chat
    results.append(await test_simple_chat())
    
    # Test 4: Full API
    results.append(await test_chat_completion())
    
    # Test 5: Function calling
    results.append(await test_function_calling())
    
    # Test 6: Integration
    results.append(await test_integration_with_agent())
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    test_names = [
        "Health Check",
        "List Models",
        "Simple Chat",
        "Chat Completion",
        "Function Calling",
        "Agent Integration"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ollama integration is working!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")


if __name__ == "__main__":
    asyncio.run(main())

