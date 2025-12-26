#!/usr/bin/env python3
"""
Standalone Ollama Test - No App Dependencies

Tests Ollama service directly without importing the full GML app.
This avoids circular import issues.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from openai import AsyncOpenAI, OpenAIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_API_KEY = "ollama"
OLLAMA_MODEL = "gpt-oss:20b"


class OllamaClient:
    """Simple Ollama client for testing"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, api_key: str = OLLAMA_API_KEY, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=httpx.Timeout(120.0),
        )
    
    async def health_check(self) -> tuple[bool, str]:
        """Check if Ollama is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url.replace('/v1', '')}/api/tags")
                if response.status_code == 200:
                    return True, "Ollama is healthy"
                return False, f"Ollama returned status {response.status_code}"
        except Exception as e:
            return False, f"Ollama error: {str(e)}"
    
    async def list_models(self) -> List[str]:
        """List available models"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url.replace('/v1', '')}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def chat(self, message: str, system_message: Optional[str] = None) -> str:
        """Simple chat"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise


async def main():
    """Run tests"""
    print("\n" + "="*70)
    print("STANDALONE OLLAMA TEST - GPT-OSS 20B")
    print("="*70)
    print()
    
    client = OllamaClient()
    
    # Test 1: Health
    print("1. Checking Ollama Health...")
    healthy, message = await client.health_check()
    if healthy:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
        print("\n   ⚠️  Setup required:")
        print("      ollama serve")
        print("      ollama pull gpt-oss:20b")
        return
    
    # Test 2: List Models
    print("\n2. Listing Models...")
    models = await client.list_models()
    if models:
        print(f"   ✅ Found {len(models)} models:")
        for model in models:
            print(f"      - {model}")
    else:
        print("   ⚠️  No models found")
    
    # Test 3: Chat
    print("\n3. Testing Chat...")
    try:
        response = await client.chat(
            "Explain what MXFP4 quantization is in one sentence.",
            "You are a helpful AI assistant."
        )
        print(f"   ✅ Response:")
        print(f"\n   {response}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n   ⚠️  Make sure:")
        print("      1. Ollama is running: ollama serve")
        print("      2. Model is pulled: ollama pull gpt-oss:20b")
        return
    
    # Test 4: Function Calling
    print("4. Testing Function Calling...")
    try:
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"]
                }
            }
        }]
        
        messages = [
            {"role": "user", "content": "What's the weather in Berlin?"}
        ]
        
        response = await client.client.chat.completions.create(
            model=client.model,
            messages=messages,
            tools=tools,
        )
        
        print(f"   ✅ Response received")
        msg = response.choices[0].message
        if msg.content:
            print(f"      Content: {msg.content}")
        if msg.tool_calls:
            print(f"      Tool Calls: {len(msg.tool_calls)}")
            for tc in msg.tool_calls:
                print(f"      - {tc.function.name}: {tc.function.arguments}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ OLLAMA INTEGRATION TEST COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Use in your code: from src.gml.services.ollama_service import OllamaService")
    print("  2. Test via API: http://localhost:8000/api/v1/ollama/chat")
    print("  3. View docs: http://localhost:8000/api/docs")


if __name__ == "__main__":
    asyncio.run(main())

