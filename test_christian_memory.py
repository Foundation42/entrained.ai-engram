#!/usr/bin/env python3
"""
Test memory retrieval for Christian specifically
"""

import requests
import json

BASE_URL = "http://46.62.130.230:8000"

def test_christian_memory():
    print("🔍 Testing memory retrieval for Christian")
    print("=" * 50)
    
    # Test different entity ID variations for Christian
    christian_variations = [
        "human-christian-kind-hare",
        "humanchristiankindhare", 
        "christian",
        "human-christian",
        "user-christian"
    ]
    
    # Create a test vector
    test_vector = [0.5] * 768
    
    for entity_id in christian_variations:
        print(f"\n🔍 Testing entity ID: {entity_id}")
        
        retrieval_request = {
            "requesting_entity": entity_id,
            "resonance_vectors": [{
                "vector": test_vector,
                "weight": 1.0
            }],
            "retrieval_options": {
                "top_k": 10,
                "similarity_threshold": 0.0
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/cam/multi/retrieve",
                json=retrieval_request,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memory_count = len(result.get('memories', []))
                print(f"   📊 Found {memory_count} memories")
                
                if memory_count > 0:
                    print(f"   🎉 SUCCESS! Memories found for '{entity_id}'")
                    for memory in result['memories']:
                        print(f"      - {memory['memory_id']}: {memory['situation_summary']}")
                        print(f"        Co-participants: {memory['co_participants']}")
                else:
                    print(f"   ❌ No memories found for '{entity_id}'")
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    # Also test if we can store a memory for Christian and then retrieve it
    print(f"\n🔧 Testing storage and immediate retrieval for Christian")
    
    test_memory = {
        "witnessed_by": ["human-christian-kind-hare", "agent-claude-prime"],
        "situation_type": "name_conversation",
        "content": {
            "text": "Christian introduced himself and mentioned he lives in Liversedge, West Yorkshire",
            "speakers": {
                "human-christian-kind-hare": "My name is Christian and I live in Liversedge in West Yorkshire",
                "agent-claude-prime": "Hello, Christian! It's great to meet you."
            },
            "summary": "Christian's introduction and location"
        },
        "primary_vector": test_vector,
        "metadata": {
            "timestamp": "2025-07-30T18:35:00Z",
            "interaction_quality": 1.0,
            "topic_tags": ["introduction", "personal", "location"]
        }
    }
    
    # Store the memory
    try:
        store_response = requests.post(f"{BASE_URL}/cam/multi/store", json=test_memory, timeout=10)
        if store_response.status_code == 200:
            result = store_response.json()
            memory_id = result['memory_id']
            print(f"   ✅ Stored test memory: {memory_id}")
            
            # Now try to retrieve it
            retrieval_request = {
                "requesting_entity": "human-christian-kind-hare",
                "resonance_vectors": [{
                    "vector": test_vector,
                    "weight": 1.0
                }],
                "retrieval_options": {
                    "top_k": 10,
                    "similarity_threshold": 0.0
                }
            }
            
            retrieve_response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=retrieval_request, timeout=10)
            if retrieve_response.status_code == 200:
                result = retrieve_response.json()
                memory_count = len(result.get('memories', []))
                print(f"   🔍 After storage, found {memory_count} memories for 'human-christian-kind-hare'")
                
                if memory_count > 0:
                    for memory in result['memories']:
                        if memory['memory_id'] == memory_id:
                            print(f"   🎉 SUCCESS! Can retrieve the memory we just stored")
                            print(f"      Content: {memory['content_preview']}")
                            break
                else:
                    print(f"   ❌ FAIL! Cannot retrieve the memory we just stored")
            else:
                print(f"   ❌ Retrieval failed: HTTP {retrieve_response.status_code}")
        else:
            print(f"   ❌ Storage failed: HTTP {store_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception during test: {e}")

if __name__ == "__main__":
    test_christian_memory()