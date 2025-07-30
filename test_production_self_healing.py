#!/usr/bin/env python3
"""
Test self-healing index creation on production server
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://46.62.130.230:8000"

def test_self_healing():
    print("🏥 Testing Self-Healing Index Creation")
    print("=" * 60)
    
    # Step 1: Store a memory (this should work even without index)
    print("\n1. Storing a multi-entity memory...")
    
    memory = {
        "witnessed_by": ["human-christian-test", "agent-claude-test"],
        "situation_type": "self_healing_test",
        "content": {
            "text": "Testing self-healing index creation",
            "speakers": {
                "human-christian-test": "Does the self-healing work?",
                "agent-claude-test": "Let's find out!"
            },
            "summary": "Self-healing test conversation"
        },
        "primary_vector": [0.5] * 768,  # Different from our usual test vector
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "interaction_quality": 0.99,
            "topic_tags": ["self-healing", "test", "index-creation"]
        }
    }
    
    store_response = requests.post(f"{BASE_URL}/cam/multi/store", json=memory, timeout=10)
    if store_response.status_code == 200:
        result = store_response.json()
        memory_id = result['memory_id']
        print(f"✅ Memory stored: {memory_id}")
    else:
        print(f"❌ Store failed: {store_response.status_code} - {store_response.text}")
        return
    
    # Step 2: Wait a moment for any async processing
    print("\n2. Waiting 2 seconds...")
    time.sleep(2)
    
    # Step 3: Try to retrieve (this should trigger self-healing if index is missing)
    print("\n3. Attempting retrieval (should trigger self-healing)...")
    
    retrieve_request = {
        "requesting_entity": "human-christian-test",
        "resonance_vectors": [{
            "vector": [0.5] * 768,  # Same as stored vector
            "weight": 1.0
        }],
        "retrieval_options": {
            "top_k": 10,
            "similarity_threshold": 0.0  # Get everything
        }
    }
    
    retrieve_response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=retrieve_request, timeout=10)
    if retrieve_response.status_code == 200:
        result = retrieve_response.json()
        print(f"✅ Retrieval successful!")
        print(f"   Found {len(result['memories'])} memories")
        print(f"   Search time: {result['search_time_ms']}ms")
        
        if result['memories']:
            for memory in result['memories']:
                print(f"   - {memory['memory_id']}: {memory['situation_summary']}")
                print(f"     Similarity: {memory['similarity_score']:.3f}")
        
        if len(result['memories']) > 0:
            print("\n🎉 SUCCESS: Self-healing worked! Index was created and memory retrieved!")
        else:
            print("\n⚠️  Memory was stored but not retrieved. Possible issues:")
            print("     - Index creation failed")
            print("     - Vector similarity too low")
            print("     - Entity ID mismatch")
            
    else:
        print(f"❌ Retrieval failed: {retrieve_response.status_code} - {retrieve_response.text}")
    
    # Step 4: Test with different entity (should get 0 results due to access control)
    print("\n4. Testing access control with different entity...")
    
    different_entity_request = {
        "requesting_entity": "unauthorized-entity-123",
        "resonance_vectors": [{
            "vector": [0.5] * 768,
            "weight": 1.0
        }],
        "retrieval_options": {
            "top_k": 10,
            "similarity_threshold": 0.0
        }
    }
    
    access_response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=different_entity_request, timeout=10)
    if access_response.status_code == 200:
        result = access_response.json()
        if len(result['memories']) == 0:
            print("✅ Access control working - unauthorized entity found 0 memories")
        else:
            print(f"❌ Access control failed - unauthorized entity found {len(result['memories'])} memories")
    
    print("\n" + "=" * 60)
    print("Self-healing test complete!")

if __name__ == "__main__":
    test_self_healing()