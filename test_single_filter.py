#!/usr/bin/env python3
"""
Test a single filter request to see detailed logs
"""

import httpx
import asyncio
import json


async def test_single_filter():
    base_url = "http://localhost:8000"
    
    print("Testing single filter request")
    print("=" * 60)
    
    # Simple test embedding
    test_embedding = [0.1] * 768
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Request with filters
        request = {
            "resonance_vectors": [{
                "vector": test_embedding,
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.0
            },
            "filters": {
                "agent_ids": ["test-agent"],
                "session_ids": ["test-session-123"]
            }
        }
        
        print("\nSending request with filters...")
        print(json.dumps(request["filters"], indent=2))
        
        response = await client.post(f"{base_url}/cam/retrieve", json=request)
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Found {result['total_found']} memories")
        else:
            print(f"Error: {response.text}")
        
        print("\nNow check the logs with: docker logs entrained-ai-engram-api --tail 50")


if __name__ == "__main__":
    asyncio.run(test_single_filter())