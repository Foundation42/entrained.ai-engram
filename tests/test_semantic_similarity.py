#!/usr/bin/env python3
"""
Test semantic similarity issue - are we getting the wrong memories?
"""

import requests
import json
from datetime import datetime

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
            print(f"❌ Ollama error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Ollama exception: {e}")
        return None

def test_different_queries():
    print("🔍 Testing Semantic Similarity Issues")
    print("=" * 60)
    
    # Different query types that might retrieve different memories
    test_queries = [
        {
            "name": "Recent Query (What agent asked)",
            "text": "Do you remember my name?",
            "expected": "Should match recent 'I don't know' responses"
        },
        {
            "name": "Introduction Query", 
            "text": "My name is Christian and I live in Liversedge",
            "expected": "Should match original introduction"
        },
        {
            "name": "Personal Info Query",
            "text": "Christian Liversedge West Yorkshire name location",
            "expected": "Should match personal information"
        },
        {
            "name": "Identity Query",
            "text": "user introduction personal information identity",
            "expected": "Should match introduction context"
        }
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n{i+1}️⃣ TESTING: {query['name']}")
        print(f"   Query: \"{query['text']}\"")
        print(f"   Expected: {query['expected']}")
        print("-" * 50)
        
        # Get embedding for this query
        embedding = get_embedding(query['text'])
        if not embedding:
            print("   ❌ Failed to get embedding")
            continue
            
        # Search with this embedding
        retrieval_request = {
            "requesting_entity": "human-christian-kind-hare",
            "resonance_vectors": [{
                "vector": embedding,
                "weight": 1.0
            }],
            "retrieval_options": {
                "top_k": 3,
                "similarity_threshold": 0.0
            }
        }
        
        try:
            response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=retrieval_request, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get('memories', [])
                
                print(f"   📊 Found {len(memories)} memories")
                
                for j, memory in enumerate(memories):
                    content = memory.get('content_preview', '')
                    score = memory.get('similarity_score', 0)
                    
                    print(f"   #{j+1} (score: {score:.3f}): {content[:80]}...")
                    
                    # Check if this contains Christian's name/location
                    content_lower = content.lower()
                    contains_christian = 'christian' in content_lower
                    contains_liversedge = 'liversedge' in content_lower
                    contains_denial = any(phrase in content_lower for phrase in [
                        "don't have access", "don't know", "sorry", "can't", "unable"
                    ])
                    
                    tags = []
                    if contains_christian:
                        tags.append("🎯 HAS NAME")
                    if contains_liversedge:
                        tags.append("🏠 HAS LOCATION") 
                    if contains_denial:
                        tags.append("❌ DENIAL")
                        
                    if tags:
                        print(f"      {' '.join(tags)}")
                
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 ANALYSIS:")
    print("If Query 1 returns denial memories and Query 2 returns introduction memories,")
    print("then the semantic similarity is working correctly but the agent needs to:")
    print("1. Use better query embeddings that match introductions, not questions")
    print("2. Prioritize older memories over recent ones")
    print("3. Filter out 'denial' type responses") 
    print("=" * 60)

if __name__ == "__main__":
    test_different_queries()