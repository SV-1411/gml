#!/usr/bin/env python3
"""
Test Both Ollama Models

Quick test for GPT-OSS 20B and Gemini 3 Flash Preview
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Direct import to avoid circular imports
import httpx
from openai import AsyncOpenAI

OLLAMA_BASE_URL = "http://localhost:11434/v1"


async def test_model(model_name: str, prompt: str):
    """Test a specific model"""
    print(f"\n{'='*70}")
    print(f"Testing: {model_name}")
    print(f"{'='*70}")
    
    client = AsyncOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
        timeout=httpx.Timeout(120.0),
    )
    
    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        print(f"✅ Response ({len(content)} chars):")
        print(f"\n{content}\n")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Test both models"""
    print("\n" + "="*70)
    print("TESTING BOTH OLLAMA MODELS")
    print("="*70)
    
    models = [
        ("gpt-oss:20b", "Explain what MXFP4 quantization is in 2 sentences."),
        ("gemini-3-flash-preview:cloud", "Explain what MXFP4 quantization is in 2 sentences.")
    ]
    
    results = []
    for model, prompt in models:
        result = await test_model(model, prompt)
        results.append((model, result))
        await asyncio.sleep(1)  # Brief pause between tests
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    for model, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {model}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 Both models working!")
    else:
        print("\n⚠️  Some models failed. Check Ollama setup.")


if __name__ == "__main__":
    asyncio.run(main())

