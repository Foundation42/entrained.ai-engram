#!/usr/bin/env python3
"""
Quick test after index fix
"""

import requests
import json

BASE_URL = "http://46.62.130.230:8000"

# Store a new memory after index fix
test_memory = {
    "witnessed_by": ["test-post-fix-user"],
    "situation_type": "post_fix_test",
    "content": {
        "text": "Testing memory after index recreation",
        "speakers": {
            "test-post-fix-user": "This should work now"
        },
        "summary": "Post-fix validation test"
    },
    "primary_vector": [0.1] * 768,
    "metadata": {
        "timestamp": "2025-07-30T18:30:00Z",
        "interaction_quality": 1.0,
        "topic_tags": ["post-fix", "test"]
    }
}

print("🔧 Testing after index fix...")

# Store memory
response = requests.post(f"{BASE_URL}/cam/multi/store", json=test_memory, timeout=10)
if response.status_code == 200:
    memory_id = response.json()['memory_id']
    print(f"✅ Stored memory: {memory_id}")
    
    # Try to retrieve it
    retrieval_request = {
        "requesting_entity": "test-post-fix-user",
        "resonance_vectors": [{
            "vector": [0.1] * 768,
            "weight": 1.0
        }],
        "retrieval_options": {
            "top_k": 10,
            "similarity_threshold": 0.0
        }
    }
    
    response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=retrieval_request, timeout=10)
    if response.status_code == 200:
        result = response.json()
        memory_count = len(result.get('memories', []))
        print(f"🔍 Retrieved {memory_count} memories")
        
        if memory_count > 0:
            print("🎉 SUCCESS: Multi-entity retrieval is working!")
            for memory in result['memories']:
                print(f"   - {memory['memory_id']}: {memory['situation_summary']}")
        else:
            print("❌ Still not working - 0 memories retrieved")
    else:
        print(f"❌ Retrieval failed: HTTP {response.status_code}")
else:
    print(f"❌ Storage failed: HTTP {response.status_code}")