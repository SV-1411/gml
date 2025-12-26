#!/usr/bin/env python3
"""
Direct Ollama Test - No Circular Imports

Tests Ollama service directly without importing the full app.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import directly to avoid circular imports
from src.gml.services.ollama_service import OllamaService


async def test_ollama():
    """Test Ollama service directly"""
    print("\n" + "="*70)
    print("DIRECT OLLAMA TEST - GPT-OSS 20B")
    print("="*70)
    print()
    
    # Test 1: Health Check
    print("1. Checking Ollama Health...")
    service = OllamaService()
    healthy, message = await service.health_check()
    
    if healthy:
        print(f"   ✅ Ollama is healthy: {message}")
    else:
        print(f"   ❌ Ollama health check failed: {message}")
        print("\n   ⚠️  Make sure Ollama is running:")
        print("      ollama serve")
        print("      ollama pull gpt-oss:20b")
        return
    
    # Test 2: List Models
    print("\n2. Listing Available Models...")
    models = await service.list_models()
    if models:
        print(f"   ✅ Found {len(models)} models:")
        for model in models:
            print(f"      - {model}")
    else:
        print("   ⚠️  No models found")
    
    # Test 3: Simple Chat
    print("\n3. Testing Simple Chat...")
    try:
        response = await service.simple_chat(
            user_message="Explain what MXFP4 quantization is in one sentence.",
            system_message="You are a helpful AI assistant."
        )
        print(f"   ✅ Response received:")
        print(f"\n   {response}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n   ⚠️  Make sure:")
        print("      1. Ollama is running: ollama serve")
        print("      2. Model is pulled: ollama pull gpt-oss:20b")
        return
    
    # Test 4: Full Chat Completion
    print("4. Testing Full Chat Completion API...")
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Answer in one word."}
        ]
        
        response = await service.chat_completion(messages)
        print(f"   ✅ Response:")
        print(f"      Model: {response.model}")
        print(f"      Content: {response.choices[0].message.content}")
        print(f"      Finish Reason: {response.choices[0].finish_reason}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nOllama integration is working!")
    print("\nNext steps:")
    print("  1. Test via API: python test_ollama_api.py")
    print("  2. View API docs: http://localhost:8000/api/docs")
    print("  3. Use in your code: from src.gml.services.ollama_service import OllamaService")


if __name__ == "__main__":
    asyncio.run(test_ollama())

