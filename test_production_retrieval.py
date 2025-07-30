#!/usr/bin/env python3
"""
Test retrieval with actual embeddings from production
"""

import httpx
import asyncio
import json


async def test_retrieval_with_embeddings():
    base_url = "http://46.62.130.230:8000"
    
    print("🔍 Testing Retrieval with Real Embeddings")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, generate a real embedding for our search query
        print("\n1. Generating embedding for search query...")
        
        embedding_request = {
            "text": "Engram multi-entity memory system witness access control"
        }
        
        response = await client.post(f"{base_url}/cam/generate_embedding", json=embedding_request)
        if response.status_code == 200:
            result = response.json()
            search_embedding = result['embedding']
            print(f"✅ Generated embedding (dim: {len(search_embedding)})")
        else:
            print(f"❌ Failed to generate embedding: {response.status_code}")
            return
        
        # Now search with this embedding
        print("\n2. Searching for Engram-related memories...")
        
        # Use a test entity ID that should have access
        test_entity = "human-christian-da31001e-9f5c-43ca-b3be-a54df52ed985"
        
        search_request = {
            "requesting_entity": test_entity,
            "resonance_vectors": [{
                "vector": search_embedding,
                "weight": 1.0
            }],
            "retrieval_options": {
                "top_k": 10,
                "similarity_threshold": 0.5,  # Lower threshold
                "include_speakers_breakdown": True
            }
        }
        
        response = await client.post(f"{base_url}/cam/multi/retrieve", json=search_request)
        if response.status_code == 200:
            results = response.json()
            print(f"\n✅ Search completed!")
            print(f"   Total found: {results['total_found']}")
            print(f"   Accessible: {len(results['memories'])}")
            print(f"   Access denied: {results['access_denied_count']}")
            print(f"   Search time: {results['search_time_ms']}ms")
            
            if results['memories']:
                print("\n📚 Retrieved Memories:")
                for i, mem in enumerate(results['memories'], 1):
                    print(f"\n   Memory {i}:")
                    print(f"   - ID: {mem['memory_id']}")
                    print(f"   - Similarity: {mem['similarity_score']:.3f}")
                    print(f"   - Summary: {mem['situation_summary']}")
                    print(f"   - Type: {mem.get('situation_type', 'unknown')}")
                    print(f"   - Co-participants: {', '.join(mem['co_participants'])}")
            else:
                print("\n   No memories found with current similarity threshold")
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    asyncio.run(test_retrieval_with_embeddings())