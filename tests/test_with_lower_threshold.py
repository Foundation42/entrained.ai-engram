#!/usr/bin/env python3
"""
Test denial filtering with lower similarity threshold to find good memories
"""

import requests
import json

BASE_URL = "http://46.62.130.230:8000"
OLLAMA_URL = "http://localhost:11434"

def get_embedding(text):
    """Get embedding for text using Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": "nomic-embed-text:latest",
                "prompt": text
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["embedding"]
        else:
            return None
    except Exception as e:
        return None

def test_lower_threshold():
    print("🔍 Testing Lower Similarity Threshold with Denial Filtering")
    print("=" * 60)
    
    # Get embedding for the problematic query
    query_text = "Do you remember my name?"
    embedding = get_embedding(query_text)
    
    if not embedding:
        print("❌ Failed to get embedding")
        return
    
    # Test with much lower threshold and more results
    request_with_filter = {
        "requesting_entity": "human-christian-kind-hare",
        "resonance_vectors": [{
            "vector": embedding,
            "weight": 1.0
        }],
        "retrieval_options": {
            "top_k": 15,  # Get more results
            "similarity_threshold": 0.0,  # Very low threshold
            "exclude_denials": True  # Filter denials
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=request_with_filter, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            
            print(f"   📊 Found {len(memories)} memories after denial filtering")
            
            if len(memories) == 0:
                print("   🔍 Still no memories - let's check what got filtered out")
                
                # Try again WITHOUT filtering to see full results
                request_no_filter = {
                    "requesting_entity": "human-christian-kind-hare",
                    "resonance_vectors": [{
                        "vector": embedding,
                        "weight": 1.0
                    }],
                    "retrieval_options": {
                        "top_k": 15,  # Get more results
                        "similarity_threshold": 0.0,  # Very low threshold
                        "exclude_denials": False  # No filtering
                    }
                }
                
                response2 = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=request_no_filter, timeout=10)
                if response2.status_code == 200:
                    result2 = response2.json()
                    memories2 = result2.get('memories', [])
                    
                    print(f"\n   📊 WITHOUT filtering: {len(memories2)} total memories")
                    denial_count = 0
                    good_count = 0
                    
                    for i, memory in enumerate(memories2):
                        content = memory.get('content_preview', '')
                        score = memory.get('similarity_score', 0)
                        
                        content_lower = content.lower()
                        is_denial = any(phrase in content_lower for phrase in [
                            "don't have access", "don't know", "sorry", "can't", "unable"
                        ])
                        
                        if is_denial:
                            denial_count += 1
                        else:
                            good_count += 1
                            print(f"   #{i+1} GOOD (score: {score:.3f}): {content[:80]}...")
                            
                            if 'christian' in content_lower:
                                print(f"       🎯 CONTAINS NAME!")
                            if 'liversedge' in content_lower:
                                print(f"       🏠 CONTAINS LOCATION!")
                    
                    print(f"\n   📊 Summary: {denial_count} denials filtered out, {good_count} good memories found")
            else:
                # Show the good memories we found
                for i, memory in enumerate(memories):
                    content = memory.get('content_preview', '')
                    score = memory.get('similarity_score', 0)
                    
                    print(f"   #{i+1} (score: {score:.3f}): {content[:80]}...")
                    
                    content_lower = content.lower()
                    if 'christian' in content_lower:
                        print(f"       🎯 CONTAINS NAME!")
                    if 'liversedge' in content_lower:
                        print(f"       🏠 CONTAINS LOCATION!")
        else:
            print(f"   ❌ Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_lower_threshold()