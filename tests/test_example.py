import httpx
import asyncio
from datetime import datetime
import numpy as np
import json


# Example embeddings (normally would come from Ollama)
def generate_random_embedding(seed=None):
    """Generate a random 1536-dimensional embedding for testing"""
    if seed:
        np.random.seed(seed)
    embedding = np.random.randn(1536)
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.tolist()


async def test_engram():
    """Test Engram API with example data"""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Check health
        print("Checking health...")
        response = await client.get(f"{base_url}/health")
        print(f"Health check: {response.json()}")
        
        # Store some memories
        print("\nStoring memories...")
        
        # Memory 1: Machine learning discussion
        memory1 = {
            "content": {
                "text": "Discussion about neural network efficiency and activation patterns. "
                       "We explored how certain architectures can achieve better performance "
                       "with fewer parameters by using sparse activation patterns.",
                "media": [
                    {
                        "type": "website",
                        "url": "https://distill.pub/2020/circuits/",
                        "title": "Neural Network Interpretability",
                        "embedding": generate_random_embedding(1),
                        "preview_text": "Interactive visualizations of neural network internals..."
                    }
                ]
            },
            "primary_vector": generate_random_embedding(100),
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "conversation",
                "participants": ["claude", "prof.smith@university.edu"],
                "domain": "machine_learning",
                "confidence": 0.95
            },
            "tags": ["faculty:claude", "domain:ml", "efficiency", "neural-networks"],
            "causality": {
                "parent_memories": [],
                "influence_strength": [],
                "synthesis_type": "original_insight"
            }
        }
        
        response = await client.post(f"{base_url}/cam/store", json=memory1)
        memory1_id = response.json()["memory_id"]
        print(f"Stored memory 1: {memory1_id}")
        
        # Memory 2: Energy efficiency insight
        memory2 = {
            "content": {
                "text": "Key insight: By implementing activation-free layers in certain parts "
                       "of the network, we can reduce energy consumption by up to 40% while "
                       "maintaining 95% of the original accuracy.",
                "media": []
            },
            "primary_vector": generate_random_embedding(101),
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "insight",
                "domain": "machine_learning",
                "confidence": 0.9
            },
            "tags": ["faculty:claude", "domain:ml", "energy-efficiency", "breakthrough"],
            "causality": {
                "parent_memories": [memory1_id],
                "influence_strength": [0.8],
                "synthesis_type": "refinement",
                "reasoning": "Built upon the sparse activation discussion"
            }
        }
        
        response = await client.post(f"{base_url}/cam/store", json=memory2)
        memory2_id = response.json()["memory_id"]
        print(f"Stored memory 2: {memory2_id}")
        
        # Memory 3: Cognitive science connection
        memory3 = {
            "content": {
                "text": "Interesting parallel with human cognition: The sparse activation "
                       "patterns we observe in efficient neural networks mirror the selective "
                       "attention mechanisms in human visual processing.",
                "media": []
            },
            "primary_vector": generate_random_embedding(102),
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "gpt4-faculty-002",
                "memory_type": "connection",
                "domain": "cognitive_science",
                "confidence": 0.85
            },
            "tags": ["faculty:gpt4", "domain:cogsci", "cross-domain", "attention"],
            "causality": {
                "parent_memories": [memory1_id, memory2_id],
                "influence_strength": [0.7, 0.5],
                "synthesis_type": "cross_domain_connection",
                "reasoning": "Connecting ML efficiency concepts with cognitive science"
            }
        }
        
        response = await client.post(f"{base_url}/cam/store", json=memory3)
        memory3_id = response.json()["memory_id"]
        print(f"Stored memory 3: {memory3_id}")
        
        # Test retrieval
        print("\nTesting retrieval...")
        
        # Create a query vector similar to memory 2 (energy efficiency)
        query_vector = generate_random_embedding(101)
        # Add some noise
        query_vector = (np.array(query_vector) + np.random.randn(1536) * 0.1).tolist()
        
        retrieval_request = {
            "resonance_vectors": [
                {
                    "vector": query_vector,
                    "weight": 1.0,
                    "label": "primary_query",
                    "description": "Looking for energy efficiency insights"
                }
            ],
            "tags": {
                "include": ["domain:ml"],
                "exclude": ["draft"]
            },
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.5
            }
        }
        
        response = await client.post(f"{base_url}/cam/retrieve", json=retrieval_request)
        results = response.json()
        print(f"Found {results['total_found']} memories in {results['search_time_ms']}ms")
        for mem in results["memories"]:
            print(f"  - {mem['memory_id']}: {mem['similarity_score']:.3f} - {mem['content_preview'][:80]}...")
        
        # Test annotation
        print("\nAdding annotation...")
        
        annotation = {
            "annotator_id": "research-assistant-007",
            "annotation": {
                "type": "relevance_boost",
                "content": "This insight has been validated in production environments",
                "confidence": 0.95,
                "tags": ["validated", "production-ready"]
            }
        }
        
        response = await client.post(f"{base_url}/cam/memory/{memory2_id}/annotate", json=annotation)
        print(f"Annotation result: {response.json()}")
        
        # Get memory details
        print(f"\nGetting details for memory {memory2_id}...")
        response = await client.get(f"{base_url}/cam/memory/{memory2_id}")
        memory_details = response.json()
        print(f"Memory type: {memory_details['metadata']['memory_type']}")
        print(f"Confidence: {memory_details['metadata']['confidence']}")
        print(f"Tags: {memory_details['tags']}")
        
        # Get annotations
        response = await client.get(f"{base_url}/cam/memory/{memory2_id}/annotations")
        annotations = response.json()
        print(f"Annotations: {len(annotations['annotations'])} found")


if __name__ == "__main__":
    print("Engram Test Suite")
    print("=================")
    print("Make sure Engram is running (docker-compose up)")
    print()
    
    asyncio.run(test_engram())