#!/usr/bin/env python3
"""
Test Ollama API Endpoints

Tests the Ollama API endpoints via HTTP.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_ollama_health():
    """Test Ollama health endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Ollama Health Check")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/v1/ollama/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_list_models():
    """Test listing models"""
    print("\n" + "="*70)
    print("TEST 2: List Ollama Models")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/v1/ollama/models")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data.get('count', 0)} models:")
        for model in data.get('models', []):
            print(f"  - {model}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200


def test_simple_chat():
    """Test simple chat endpoint"""
    print("\n" + "="*70)
    print("TEST 3: Simple Chat")
    print("="*70)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/ollama/simple",
        params={
            "message": "Explain what MXFP4 quantization is in one sentence.",
            "system_message": "You are a helpful AI assistant."
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Model: {data.get('model')}")
        print(f"\nResponse:\n{data.get('response')}\n")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200


def test_chat_completion():
    """Test full chat completion"""
    print("\n" + "="*70)
    print("TEST 4: Chat Completion")
    print("="*70)
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Answer in one word."}
        ],
        "model": "gpt-oss:20b",
        "temperature": 0.7
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/ollama/chat",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Model: {data.get('model')}")
        print(f"Content: {data.get('content')}")
        print(f"Finish Reason: {data.get('finish_reason')}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("OLLAMA API ENDPOINT TESTS")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print("\nPrerequisites:")
    print("  1. Ollama running: ollama serve")
    print("  2. Model pulled: ollama pull gpt-oss:20b")
    print("  3. API server running on port 8000")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server is not responding correctly!")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("\n   Please start the server first:")
        print("   cd src && uvicorn gml.api.main:app --reload")
        return
    
    results = []
    
    results.append(test_ollama_health())
    results.append(test_list_models())
    results.append(test_simple_chat())
    results.append(test_chat_completion())
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    test_names = [
        "Health Check",
        "List Models",
        "Simple Chat",
        "Chat Completion"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All API tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")


if __name__ == "__main__":
    main()

