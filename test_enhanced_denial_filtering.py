#!/usr/bin/env python3
"""
Test the enhanced denial filtering with the specific phrases Christian found
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

def test_enhanced_filtering():
    print("🔍 Testing Enhanced Denial Filtering")
    print("=" * 60)
    
    # Test the specific problematic query Christian found
    test_queries = [
        {
            "name": "Name Query (Previously problematic)",
            "text": "Do you remember my name?",
            "should_filter": "You haven't mentioned your name yet"
        },
        {
            "name": "Location Query (Previously working)", 
            "text": "Where do I live?",
            "expected": "Should find Liversedge references"
        },
        {
            "name": "Identity Query (Should work well)",
            "text": "My name is Christian and I live in Liversedge",
            "expected": "Should find introduction memories"
        }
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n{i+1}️⃣ Testing: {query['name']}")
        print(f"   Query: \"{query['text']}\"")
        print("-" * 50)
        
        # Get embedding
        embedding = get_embedding(query['text'])
        if not embedding:
            print("   ❌ Failed to get embedding")
            continue
        
        # Test WITH enhanced denial filtering
        request_with_filtering = {
            "requesting_entity": "human-christian-kind-hare",
            "resonance_vectors": [{
                "vector": embedding,
                "weight": 1.0
            }],
            "retrieval_options": {
                "top_k": 10,  # Get more to see what's filtered
                "similarity_threshold": 0.0,
                "exclude_denials": True  # Enhanced filtering
            }
        }
        
        try:
            response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=request_with_filtering, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get('memories', [])
                
                print(f"   📊 Found {len(memories)} memories after enhanced filtering")
                
                denial_found = False
                good_memories = 0
                
                for j, memory in enumerate(memories[:5]):  # Show first 5
                    content = memory.get('content_preview', '')
                    score = memory.get('similarity_score', 0)
                    
                    print(f"   #{j+1} (score: {score:.3f}): {content[:80]}...")
                    
                    # Check for the specific denial phrases Christian found
                    content_lower = content.lower()
                    
                    # Check for denial patterns
                    denial_patterns = [
                        "haven't mentioned", "you haven't", "didn't tell me", 
                        "don't have access", "don't know", "sorry"
                    ]
                    
                    is_denial = any(pattern in content_lower for pattern in denial_patterns)
                    
                    if is_denial:
                        denial_found = True
                        print(f"       ❌ DENIAL DETECTED (should be filtered!)")
                    elif 'christian' in content_lower or 'liversedge' in content_lower:
                        good_memories += 1
                        print(f"       🎯 GOOD MEMORY (contains facts)")
                    else:
                        print(f"       ⚪ NEUTRAL MEMORY")
                
                # Summary for this query
                if denial_found:
                    print(f"   ⚠️  Still finding denial responses - filter needs improvement")
                elif good_memories > 0:
                    print(f"   ✅ Success! Found {good_memories} good memories, no denials")
                else:
                    print(f"   🔍 No denials found, but also no good memories")
                    
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 GOAL: All queries should return good memories with no denial responses")
    print("If denials still appear, we need to add more patterns to the filter")
    print("=" * 60)

if __name__ == "__main__":
    test_enhanced_filtering()