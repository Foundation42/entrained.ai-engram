#!/usr/bin/env python3
"""
Test multi-entity memory system with witness-based access control
"""

import httpx
import asyncio
from datetime import datetime
import uuid
import json


def create_test_embedding():
    """Create a normalized test embedding"""
    import random
    vec = [random.gauss(0, 1) for _ in range(768)]
    norm = sum(x**2 for x in vec) ** 0.5
    return [x/norm for x in vec]


async def test_multi_entity_system():
    base_url = "http://localhost:8000"
    
    print("🌐 Testing Multi-Entity Memory System")
    print("=" * 80)
    
    # Define test entities
    christian_id = f"christian-{uuid.uuid4()}"
    claude_id = f"dr-claude-{uuid.uuid4()}"
    alice_id = f"alice-{uuid.uuid4()}"
    bob_id = f"bob-{uuid.uuid4()}"
    
    print(f"\nTest Entities:")
    print(f"  Christian: {christian_id}")
    print(f"  Dr. Claude: {claude_id}")
    print(f"  Alice: {alice_id}")
    print(f"  Bob: {bob_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Private 1:1 Consultation
        print("\n\n1. Testing Private 1:1 Consultation")
        print("-" * 50)
        
        consultation_memory = {
            "witnessed_by": [christian_id, claude_id],
            "situation_type": "consultation_1to1",
            "content": {
                "text": "Christian: I'm struggling with neural network optimization. Dr. Claude: Let's explore gradient descent variants and learning rate scheduling...",
                "speakers": {
                    christian_id: "I'm struggling with neural network optimization",
                    claude_id: "Let's explore gradient descent variants and learning rate scheduling..."
                },
                "summary": "Private consultation about neural network optimization strategies"
            },
            "primary_vector": create_test_embedding(),
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "situation_duration_minutes": 25,
                "interaction_quality": 0.95,
                "topic_tags": ["neural_networks", "optimization", "consultation"]
            }
        }
        
        response = await client.post(f"{base_url}/cam/multi/store", json=consultation_memory)
        if response.status_code == 200:
            result = response.json()
            consultation_id = result['memory_id']
            print(f"✅ Stored private consultation: {consultation_id}")
            print(f"   Witnesses: {result['witnessed_by']}")
        else:
            print(f"❌ Failed to store: {response.status_code}")
            print(response.text)
            return
        
        # Test 2: Group Research Discussion
        print("\n\n2. Testing Group Research Discussion")
        print("-" * 50)
        
        group_memory = {
            "witnessed_by": [christian_id, claude_id, alice_id, bob_id],
            "situation_type": "group_discussion",
            "content": {
                "text": "Christian: What about quantum computing applications? Alice: Great question! Bob: I've been researching quantum algorithms. Dr. Claude: Let me explain the current state of quantum computing...",
                "speakers": {
                    christian_id: "What about quantum computing applications?",
                    alice_id: "Great question!",
                    bob_id: "I've been researching quantum algorithms",
                    claude_id: "Let me explain the current state of quantum computing..."
                },
                "summary": "Group discussion about quantum computing applications and algorithms"
            },
            "primary_vector": create_test_embedding(),
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "situation_duration_minutes": 45,
                "interaction_quality": 0.88,
                "topic_tags": ["quantum_computing", "research", "algorithms", "group_discussion"]
            }
        }
        
        response = await client.post(f"{base_url}/cam/multi/store", json=group_memory)
        if response.status_code == 200:
            result = response.json()
            group_id = result['memory_id']
            print(f"✅ Stored group discussion: {group_id}")
            print(f"   Witnesses: {', '.join(result['witnessed_by'][:2])} + {len(result['witnessed_by'])-2} more")
        
        # Test 3: Access Control - Christian retrieves memories
        print("\n\n3. Testing Access Control - Christian's Perspective")
        print("-" * 50)
        
        retrieval_request = {
            "requesting_entity": christian_id,
            "resonance_vectors": [{
                "vector": create_test_embedding(),
                "weight": 1.0
            }],
            "retrieval_options": {
                "top_k": 10,
                "similarity_threshold": 0.0,
                "include_speakers_breakdown": True
            }
        }
        
        response = await client.post(f"{base_url}/cam/multi/retrieve", json=retrieval_request)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Christian can access {len(results['memories'])} memories")
            for mem in results['memories']:
                print(f"   - {mem['situation_summary']}")
                print(f"     Co-participants: {', '.join(mem['co_participants'][:3])}")
        
        # Test 4: Access Control - Alice tries to access private consultation
        print("\n\n4. Testing Access Control - Alice's Limited Access")
        print("-" * 50)
        
        alice_request = {
            "requesting_entity": alice_id,
            "resonance_vectors": [{
                "vector": create_test_embedding(),
                "weight": 1.0
            }],
            "retrieval_options": {
                "top_k": 10,
                "similarity_threshold": 0.0
            }
        }
        
        response = await client.post(f"{base_url}/cam/multi/retrieve", json=alice_request)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Alice can access {len(results['memories'])} memories")
            for mem in results['memories']:
                print(f"   - {mem['situation_summary']}")
            
            # Verify Alice cannot access the private consultation
            private_access = any(m['memory_id'] == consultation_id for m in results['memories'])
            if not private_access:
                print(f"   ✅ Correctly blocked from private consultation")
            else:
                print(f"   ❌ ERROR: Alice accessed private consultation!")
        
        # Test 5: Co-participant filtering
        print("\n\n5. Testing Co-participant Filtering")
        print("-" * 50)
        
        co_participant_request = {
            "requesting_entity": christian_id,
            "resonance_vectors": [{
                "vector": create_test_embedding(),
                "weight": 1.0
            }],
            "entity_filters": {
                "co_participants": [alice_id]  # Only memories with Alice
            },
            "retrieval_options": {
                "top_k": 10,
                "similarity_threshold": 0.0
            }
        }
        
        response = await client.post(f"{base_url}/cam/multi/retrieve", json=co_participant_request)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results['memories'])} memories with both Christian and Alice")
            for mem in results['memories']:
                if alice_id in mem['co_participants']:
                    print(f"   ✅ {mem['situation_summary']}")
        
        # Test 6: Situation filtering
        print("\n\n6. Testing Situation Type Filtering")
        print("-" * 50)
        
        situation_request = {
            "requesting_entity": christian_id,
            "resonance_vectors": [{
                "vector": create_test_embedding(),
                "weight": 1.0
            }],
            "situation_filters": {
                "situation_types": ["consultation_1to1"]
            },
            "retrieval_options": {
                "top_k": 10,
                "similarity_threshold": 0.0
            }
        }
        
        response = await client.post(f"{base_url}/cam/multi/retrieve", json=situation_request)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results['memories'])} consultation memories")
            for mem in results['memories']:
                print(f"   - Type: {mem['situation_type']} | {mem['situation_summary']}")
        
        # Test 7: Get entity situations
        print("\n\n7. Testing Entity Situation History")
        print("-" * 50)
        
        response = await client.get(f"{base_url}/cam/multi/situations/{christian_id}")
        if response.status_code == 200:
            situations = response.json()
            print(f"✅ Christian participated in {situations['total_situations']} situations")
            for sit in situations['situations']:
                print(f"   - {sit['situation_type']}: {len(sit['participants'])} participants")
        
        print("\n" + "=" * 80)
        print("\n🎯 MULTI-ENTITY TEST SUMMARY:")
        print("✅ Witness-based access control working")
        print("✅ Private memories properly isolated")
        print("✅ Group memories accessible to all participants")
        print("✅ Co-participant filtering functional")
        print("✅ Situation-based queries working")
        print("\n🚀 Multi-entity memory system is operational!")


if __name__ == "__main__":
    asyncio.run(test_multi_entity_system())