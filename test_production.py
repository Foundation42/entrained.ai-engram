#!/usr/bin/env python3
"""
Test the production deployment of entrained.ai-engram
"""

import httpx
import asyncio
from datetime import datetime
import json


async def test_production():
    base_url = "http://46.62.130.230:8000"
    
    print("🚀 Testing Production entrained.ai-engram")
    print(f"   Server: {base_url}")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health Check
        print("\n1. Health Check...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"   ✅ Status: {health['status']}")
                print(f"   ✅ Redis: {health['redis']}")
                print(f"   ✅ Vector Index: {health['vector_index']}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return
        except Exception as e:
            print(f"   ❌ Could not connect: {e}")
            return
        
        # 2. API Info
        print("\n2. API Information...")
        try:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                info = response.json()
                print(f"   Name: {info['name']}")
                print(f"   Version: {info['version']}")
                print(f"   Description: {info['description']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 3. Store a test memory
        print("\n3. Storing Test Memory...")
        
        # Create a simple embedding (mock for testing)
        import random
        random.seed(42)
        test_embedding = [random.gauss(0, 1) for _ in range(768)]
        norm = sum(x**2 for x in test_embedding) ** 0.5
        test_embedding = [x/norm for x in test_embedding]
        
        test_memory = {
            "content": {
                "text": "Production test from Claude Code: entrained.ai-engram is successfully deployed!",
                "media": []
            },
            "primary_vector": test_embedding,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-code-test",
                "memory_type": "test",
                "domain": "system_test",
                "confidence": 0.99
            },
            "tags": ["production-test", "deployment", "claude-code"]
        }
        
        try:
            response = await client.post(f"{base_url}/cam/store", json=test_memory)
            if response.status_code == 200:
                result = response.json()
                memory_id = result['memory_id']
                print(f"   ✅ Stored memory: {memory_id}")
                print(f"   Timestamp: {result['timestamp']}")
                
                # 4. Retrieve the memory
                print("\n4. Retrieving Test Memory...")
                response = await client.get(f"{base_url}/cam/memory/{memory_id}")
                if response.status_code == 200:
                    retrieved = response.json()
                    print(f"   ✅ Retrieved successfully")
                    print(f"   Content: {retrieved['content']['text'][:50]}...")
                    print(f"   Agent: {retrieved['metadata']['agent_id']}")
                    print(f"   Tags: {', '.join(retrieved['tags'])}")
            else:
                print(f"   ❌ Failed to store: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 5. Test Vector Search
        print("\n5. Testing Vector Search...")
        
        search_request = {
            "resonance_vectors": [{
                "vector": test_embedding,  # Search with same vector
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.5
            }
        }
        
        try:
            response = await client.post(f"{base_url}/cam/retrieve", json=search_request)
            if response.status_code == 200:
                results = response.json()
                print(f"   ✅ Search completed in {results['search_time_ms']}ms")
                print(f"   Found {results['total_found']} results")
                
                if results['memories']:
                    print("\n   Top results:")
                    for i, mem in enumerate(results['memories'][:3], 1):
                        print(f"   {i}. Score: {mem['similarity_score']:.3f}")
                        print(f"      {mem['content_preview'][:60]}...")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Production test completed!")
        print(f"\nAPI Documentation available at: {base_url}/docs")
        print(f"RedisInsight available at: http://46.62.130.230:8002")


if __name__ == "__main__":
    asyncio.run(test_production())