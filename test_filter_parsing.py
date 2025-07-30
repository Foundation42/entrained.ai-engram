#!/usr/bin/env python3
"""
Test filter parsing issue - reproduce the exact problem
"""

import httpx
import asyncio
import json
from datetime import datetime


async def test_filter_parsing():
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Filter Parsing Issue")
    print("=" * 80)
    
    # Simple test embedding
    test_embedding = [0.1] * 768
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Request WITH filters object
        print("\n1. Testing request WITH filters object")
        request_with_filters = {
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
        
        print("\nRequest body:")
        print(json.dumps(request_with_filters, indent=2))
        
        response = await client.post(f"{base_url}/cam/retrieve", json=request_with_filters)
        print(f"\nResponse status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Found {result['total_found']} memories")
        
        # Test 2: Request WITHOUT filters object (might be the issue)
        print("\n\n2. Testing request WITHOUT filters object")
        request_no_filters = {
            "resonance_vectors": [{
                "vector": test_embedding,
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.0
            }
            # No filters key at all
        }
        
        print("\nRequest body:")
        print(json.dumps(request_no_filters, indent=2))
        
        response = await client.post(f"{base_url}/cam/retrieve", json=request_no_filters)
        print(f"\nResponse status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Found {result['total_found']} memories")
        
        # Test 3: Request with empty filters object
        print("\n\n3. Testing request with EMPTY filters object")
        request_empty_filters = {
            "resonance_vectors": [{
                "vector": test_embedding,
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.0
            },
            "filters": {}  # Empty filters object
        }
        
        print("\nRequest body:")
        print(json.dumps(request_empty_filters, indent=2))
        
        response = await client.post(f"{base_url}/cam/retrieve", json=request_empty_filters)
        print(f"\nResponse status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Found {result['total_found']} memories")
        
        # Test 4: Request with null filters
        print("\n\n4. Testing request with NULL filters")
        request_null_filters = {
            "resonance_vectors": [{
                "vector": test_embedding,
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.0
            },
            "filters": None  # Null filters
        }
        
        print("\nRequest body:")
        print(json.dumps(request_null_filters, indent=2))
        
        response = await client.post(f"{base_url}/cam/retrieve", json=request_null_filters)
        print(f"\nResponse status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Found {result['total_found']} memories")
        else:
            print(f"Error: {response.text}")
        
        print("\n" + "=" * 80)
        print("\nCheck the server logs to see which requests have filters parsed correctly!")


if __name__ == "__main__":
    asyncio.run(test_filter_parsing())