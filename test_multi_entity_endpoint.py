#!/usr/bin/env python3
"""
Simple test to verify multi-entity endpoints are working
Run this directly to test the endpoints without any complex agent code
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://46.62.130.230:8000"  # or http://localhost:8000 for local

def test_multi_entity_store():
    """Test the multi-entity store endpoint with minimal data"""
    
    print("Testing Multi-Entity Store Endpoint")
    print("=" * 50)
    
    # Minimal valid request
    memory = {
        "witnessed_by": ["test-entity-1", "test-entity-2"],
        "situation_type": "test_conversation",  # Simple string, top-level
        "content": {
            "text": "This is a test conversation",
            "speakers": {
                "test-entity-1": "Hello!",
                "test-entity-2": "Hi there!"
            },
            "summary": "Test greeting"
        },
        "primary_vector": [0.1] * settings.vector_dimensions,  # Dummy embedding
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "interaction_quality": 0.9,
            "topic_tags": ["test"]
        }
    }
    
    print("Request body:")
    print(json.dumps(memory, indent=2)[:200] + "...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/cam/multi/store",
            json=memory,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Memory ID: {result['memory_id']}")
            return result['memory_id']
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {type(e).__name__}: {e}")
        return None


def test_multi_entity_retrieve(memory_id=None):
    """Test the multi-entity retrieve endpoint"""
    
    print("\n\nTesting Multi-Entity Retrieve Endpoint")
    print("=" * 50)
    
    request = {
        "requesting_entity": "test-entity-1",
        "resonance_vectors": [{
            "vector": [0.1] * settings.vector_dimensions,
            "weight": 1.0
        }],
        "retrieval_options": {
            "top_k": 10,
            "similarity_threshold": 0.0  # Get everything
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/cam/multi/retrieve",
            json=request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Found {len(result['memories'])} memories")
            
            if memory_id and result['memories']:
                # Check if our test memory is there
                found = any(m['memory_id'] == memory_id for m in result['memories'])
                if found:
                    print(f"✅ Test memory {memory_id} was retrieved successfully!")
                else:
                    print(f"⚠️  Test memory {memory_id} was not found in results")
                    
            return result
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {type(e).__name__}: {e}")
        return None


if __name__ == "__main__":
    print("Multi-Entity Endpoint Test")
    print("=" * 70)
    print(f"Testing against: {BASE_URL}")
    print()
    
    # Test store
    memory_id = test_multi_entity_store()
    
    # Test retrieve
    if memory_id:
        test_multi_entity_retrieve(memory_id)
    else:
        print("\nSkipping retrieve test since store failed")
    
    print("\n" + "=" * 70)
    print("Test complete!")
    print("\nIf both tests passed, the multi-entity endpoints are working correctly.")
    print("The AttributeError must be in the agent's code, not the server.")