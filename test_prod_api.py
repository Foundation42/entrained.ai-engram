#!/usr/bin/env python3
"""Test connection to production Engram API"""
import httpx
import asyncio
import json

# Your production server
PROD_URL = "https://engram-fi-1.entrained.ai:8443"
API_KEY = "engram-production-secure-key-2025-comments-system"  # Production API key


async def test_production():
    """Test production Engram API"""
    print(f"🔍 Testing Engram API at {PROD_URL}\n")
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # Test 1: Health check (no auth needed)
        print("1. Testing /health endpoint...")
        try:
            response = await client.get(f"{PROD_URL}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {json.dumps(data, indent=6)}\n")
            else:
                print(f"   Response: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
        
        # Test 2: Root endpoint
        print("2. Testing / endpoint...")
        try:
            response = await client.get(f"{PROD_URL}/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Name: {data['name']}")
                print(f"   ✅ Version: {data['version']}")
                print(f"   ✅ Features: {', '.join(data['features'])}\n")
            else:
                print(f"   Response: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
        
        # Test 3: Store a memory (requires API key)
        print("3. Testing /cam/store endpoint (with auth)...")
        try:
            test_memory = {
                "content": {
                    "text": "Test memory from local machine",
                    "media": []
                },
                "primary_vector": [0.1] * 1536,  # Dummy vector
                "metadata": {
                    "timestamp": "2025-09-30T14:30:00Z",
                    "agent_id": "test-local",
                    "memory_type": "test"
                },
                "tags": ["test", "local"]
            }
            
            headers = {"X-API-Key": API_KEY} if API_KEY != "your-api-key-here" else {}
            response = await client.post(
                f"{PROD_URL}/cam/store",
                json=test_memory,
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Memory stored: {data['memory_id']}\n")
            elif response.status_code == 401:
                print(f"   ⚠️  Need API key (update script with key from .env)\n")
            else:
                print(f"   Response: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(test_production())
