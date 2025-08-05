#!/usr/bin/env python3
"""
Diagnose entity ID format issues
"""

import httpx
import asyncio
import json


async def diagnose_entity_format():
    base_url = "http://46.62.130.230:8000"
    
    print("🔍 Diagnosing Entity ID Format Issues")
    print("=" * 60)
    
    # Test different entity ID formats
    test_cases = [
        {
            "name": "Standard UUID format",
            "entity_id": "human-christian-12345678-90ab-cdef-ghij-klmnopqrstuv",
            "description": "Entity ID with hyphens in UUID"
        },
        {
            "name": "No hyphens in UUID", 
            "entity_id": "human-christian-1234567890abcdefghijklmnopqrstuv",
            "description": "Entity ID without any hyphens in UUID part"
        },
        {
            "name": "Human readable (no UUID)",
            "entity_id": "human-christian-kindhare",
            "description": "Entity ID without UUID, just readable name"
        },
        {
            "name": "All hyphens removed",
            "entity_id": "humanchristiankindhare",
            "description": "Entity ID with all hyphens removed"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for test in test_cases:
            print(f"\n\nTesting: {test['name']}")
            print(f"Entity ID: {test['entity_id']}")
            print(f"Description: {test['description']}")
            print("-" * 50)
            
            # Try to store a memory
            memory = {
                "witnessed_by": [test['entity_id']],
                "situation_type": "diagnostic_test",
                "content": {
                    "text": f"Testing entity format: {test['name']}",
                    "speakers": {
                        test['entity_id']: "Testing entity ID format"
                    },
                    "summary": f"Diagnostic test for {test['name']}"
                },
                "primary_vector": [0.1] * settings.vector_dimensions,  # Dummy vector
                "metadata": {
                    "timestamp": "2025-07-30T12:00:00Z",
                    "situation_duration_minutes": 1,
                    "interaction_quality": 1.0,
                    "topic_tags": ["diagnostic", "test"]
                }
            }
            
            response = await client.post(f"{base_url}/cam/multi/store", json=memory)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Storage successful!")
                print(f"   Memory ID: {result['memory_id']}")
                
                # Now try to retrieve
                retrieval = {
                    "requesting_entity": test['entity_id'],
                    "resonance_vectors": [{
                        "vector": [0.1] * settings.vector_dimensions,
                        "weight": 1.0
                    }],
                    "retrieval_options": {
                        "top_k": 10,
                        "similarity_threshold": 0.0
                    }
                }
                
                ret_response = await client.post(f"{base_url}/cam/multi/retrieve", json=retrieval)
                if ret_response.status_code == 200:
                    ret_result = ret_response.json()
                    print(f"✅ Retrieval successful!")
                    print(f"   Found {len(ret_result['memories'])} memories")
                else:
                    print(f"❌ Retrieval failed: {ret_response.status_code}")
                    print(f"   {ret_response.text}")
                    
            else:
                print(f"❌ Storage failed: {response.status_code}")
                print(f"   {response.text}")
        
        print("\n\n" + "=" * 60)
        print("RECOMMENDATION:")
        print("Entity IDs should use the format: 'type-name-uuid'")
        print("Where UUID can have hyphens (they'll be removed internally)")
        print("Example: 'human-christian-12345678-90ab-cdef-ghij-klmnopqrstuv'")


if __name__ == "__main__":
    asyncio.run(diagnose_entity_format())