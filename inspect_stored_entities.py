#!/usr/bin/env python3
"""
Inspect what entity IDs are actually stored in the database
"""

import requests
import json

BASE_URL = "http://46.62.130.230:8000" 
ADMIN_USER = "admin"
ADMIN_PASS = "engram-admin-2025"

def inspect_stored_entities():
    print("🔍 Inspecting Stored Entity IDs")
    print("=" * 60)
    
    # First, let's store a test memory with a known entity ID so we can retrieve it
    print("\n1. Storing a test memory with known entity ID...")
    
    test_memory = {
        "witnessed_by": ["test-entity-debug-123"],
        "situation_type": "debug_test", 
        "content": {
            "text": "Debug test to check entity ID storage",
            "speakers": {
                "test-entity-debug-123": "This is a debug test"
            },
            "summary": "Debug entity ID test"
        },
        "primary_vector": [0.7] * 768,  # Unique test vector
        "metadata": {
            "timestamp": "2025-07-30T15:30:00Z",
            "interaction_quality": 1.0,
            "topic_tags": ["debug", "entity-test"]
        }
    }
    
    store_response = requests.post(f"{BASE_URL}/cam/multi/store", json=test_memory, timeout=10)
    if store_response.status_code == 200:
        result = store_response.json()
        test_memory_id = result['memory_id']
        print(f"✅ Test memory stored: {test_memory_id}")
    else:
        print(f"❌ Test store failed: {store_response.status_code}")
        return
    
    # Now retrieve it to confirm our test works
    print("\n2. Retrieving test memory to confirm our approach works...")
    
    test_retrieve = {
        "requesting_entity": "test-entity-debug-123",
        "resonance_vectors": [{
            "vector": [0.7] * 768,
            "weight": 1.0
        }],
        "retrieval_options": {
            "top_k": 10,
            "similarity_threshold": 0.0
        }
    }
    
    test_response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=test_retrieve, timeout=10)
    if test_response.status_code == 200:
        result = test_response.json()
        if len(result['memories']) > 0:
            print(f"✅ Test retrieval worked: found {len(result['memories'])} memories")
            print("   This confirms our approach is correct")
        else:
            print("❌ Test retrieval failed - this suggests a deeper issue")
            return
    
    # Now let's try to find what entity IDs might be stored by trying variations
    print("\n3. Searching for common entity ID patterns...")
    
    common_patterns = [
        # Christian variations
        "christian",
        "human-christian", 
        "user-christian",
        "human-christian-user",
        
        # Agent variations  
        "claude",
        "agent-claude",
        "claude-prime",
        "agent-claude-prime",
        "claude-4",
        
        # Session-based IDs
        "session-",
        "user-",
        "human-",
        "agent-",
        
        # UUID patterns (just prefixes)
        "mem-",
        "sit-"
    ]
    
    found_entities = []
    
    for pattern in common_patterns:
        # Try the pattern with common suffixes
        test_entities = [
            pattern,
            f"{pattern}-123",
            f"{pattern}-456", 
            f"{pattern}-test",
            f"{pattern}-user"
        ]
        
        for entity in test_entities:
            retrieve_request = {
                "requesting_entity": entity,
                "resonance_vectors": [{
                    "vector": [0.5] * 768,
                    "weight": 1.0
                }],
                "retrieval_options": {
                    "top_k": 10,
                    "similarity_threshold": 0.0
                }
            }
            
            try:
                response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=retrieve_request, timeout=5)
                if response.status_code == 200:
                    result = response.json()
                    if len(result['memories']) > 0:
                        print(f"🎉 FOUND: '{entity}' can access {len(result['memories'])} memories!")
                        found_entities.append({
                            'entity': entity,
                            'memory_count': len(result['memories']),
                            'memories': result['memories']
                        })
                        
                        # Show details of found memories
                        for memory in result['memories']:
                            print(f"   - {memory['memory_id']}: {memory['situation_summary']}")
                            print(f"     Co-participants: {memory['co_participants']}")
                        
            except Exception as e:
                continue  # Skip errors, we're just scanning
    
    print("\n" + "=" * 60)
    print("📊 RESULTS:")
    
    if found_entities:
        print(f"✅ Found {len(found_entities)} entity IDs that can access memories:")
        for entity_info in found_entities:
            print(f"   - {entity_info['entity']}: {entity_info['memory_count']} memories")
        
        print("\n💡 SOLUTION:")
        print("The agent needs to use these EXACT entity IDs for retrieval!")
        print("Check the agent's entity ID generation code.")
        
    else:
        print("❌ No entity IDs found that can access the stored memories")
        print("This suggests either:")
        print("   1. Entity IDs are using a completely different format")
        print("   2. There's an issue with the witness-based access control")
        print("   3. The stored memories have corrupted entity data")
        
        print("\n🔧 Next steps:")
        print("   1. Check the agent's entity ID generation logic")
        print("   2. Look at the actual stored memory data in Redis")
        print("   3. Consider using the admin flush to reset and test with known IDs")

if __name__ == "__main__":
    inspect_stored_entities()