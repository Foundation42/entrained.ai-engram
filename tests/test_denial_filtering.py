#!/usr/bin/env python3
"""
Test the new denial filtering capability
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

def test_denial_filtering():
    print("🔍 Testing Denial Filtering")
    print("=" * 60)
    
    # Get embedding for the problematic query
    query_text = "Do you remember my name?"
    embedding = get_embedding(query_text)
    
    if not embedding:
        print("❌ Failed to get embedding")
        return
    
    # Test WITHOUT denial filtering (old behavior)
    print(f"\n1️⃣ WITHOUT Denial Filtering (exclude_denials=False)")
    print("-" * 50)
    
    request_no_filter = {
        "requesting_entity": "human-christian-kind-hare",
        "resonance_vectors": [{
            "vector": embedding,
            "weight": 1.0
        }],
        "retrieval_options": {
            "top_k": 5,
            "similarity_threshold": 0.0,
            "exclude_denials": False  # Explicitly disable
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=request_no_filter, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            
            print(f"   📊 Found {len(memories)} memories")
            for i, memory in enumerate(memories):
                content = memory.get('content_preview', '')
                score = memory.get('similarity_score', 0)
                
                print(f"   #{i+1} (score: {score:.3f}): {content[:80]}...")
                
                # Check content type
                content_lower = content.lower()
                if any(phrase in content_lower for phrase in ["don't have access", "don't know", "sorry"]):
                    print(f"       ❌ DENIAL CONTENT")
                elif 'christian' in content_lower:
                    print(f"       🎯 CONTAINS NAME")
        else:
            print(f"   ❌ Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test WITH denial filtering (new behavior - default)
    print(f"\n2️⃣ WITH Denial Filtering (exclude_denials=True - DEFAULT)")
    print("-" * 50)
    
    request_with_filter = {
        "requesting_entity": "human-christian-kind-hare",
        "resonance_vectors": [{
            "vector": embedding,
            "weight": 1.0
        }],
        "retrieval_options": {
            "top_k": 5,
            "similarity_threshold": 0.0,
            "exclude_denials": True  # Explicitly enable (but it's default)
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=request_with_filter, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            
            print(f"   📊 Found {len(memories)} memories")
            for i, memory in enumerate(memories):
                content = memory.get('content_preview', '')
                score = memory.get('similarity_score', 0)
                
                print(f"   #{i+1} (score: {score:.3f}): {content[:80]}...")
                
                # Check content type
                content_lower = content.lower()
                if any(phrase in content_lower for phrase in ["don't have access", "don't know", "sorry"]):
                    print(f"       ❌ DENIAL CONTENT (SHOULD BE FILTERED!)")
                elif 'christian' in content_lower:
                    print(f"       🎯 CONTAINS NAME")
                elif 'liversedge' in content_lower:
                    print(f"       🏠 CONTAINS LOCATION")
        else:
            print(f"   ❌ Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 EXPECTED RESULT:")
    print("Test 1 should show denial memories (old problematic behavior)")
    print("Test 2 should show useful memories with Christian's info")
    print("=" * 60)

if __name__ == "__main__":
    test_denial_filtering()