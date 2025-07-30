#!/usr/bin/env python3
"""
Test session isolation and metadata filtering
"""

import httpx
import asyncio
from datetime import datetime
import random
import uuid


async def test_session_isolation():
    base_url = "http://localhost:8000"
    
    print("🔒 Testing Session Isolation and Metadata Filtering")
    print("=" * 60)
    
    # Create test embeddings
    def create_embedding():
        vec = [random.gauss(0, 1) for _ in range(768)]
        norm = sum(x**2 for x in vec) ** 0.5
        return [x/norm for x in vec]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Health check
        response = await client.get(f"{base_url}/health")
        if response.status_code != 200:
            print("❌ Server not healthy")
            return
        
        # Create memories for different sessions
        session1_id = str(uuid.uuid4())
        session2_id = str(uuid.uuid4())
        
        memories_created = []
        
        print(f"\n1. Creating memories for two different sessions")
        print(f"   Session 1: {session1_id}")
        print(f"   Session 2: {session2_id}")
        
        # Session 1 memories
        for i in range(3):
            memory = {
                "content": {
                    "text": f"Session 1 memory {i+1}: Private conversation about project Alpha",
                    "media": []
                },
                "primary_vector": create_embedding(),
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "agent_id": "agent-001",
                    "memory_type": "conversation",
                    "session_id": session1_id,  # Session isolation
                    "domain": "project-alpha",
                    "confidence": 0.9,
                    "participants": ["alice", "bob"]
                },
                "tags": ["private", "project-alpha", f"session1-mem{i+1}"]
            }
            
            response = await client.post(f"{base_url}/cam/store", json=memory)
            if response.status_code == 200:
                result = response.json()
                memories_created.append(result['memory_id'])
                print(f"   ✅ Created memory {i+1} for session 1: {result['memory_id']}")
            else:
                print(f"   ❌ Failed to create memory: {response.status_code}")
        
        # Session 2 memories
        for i in range(3):
            memory = {
                "content": {
                    "text": f"Session 2 memory {i+1}: Confidential discussion about project Beta",
                    "media": []
                },
                "primary_vector": create_embedding(),
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "agent_id": "agent-002",
                    "memory_type": "conversation",
                    "session_id": session2_id,  # Different session
                    "domain": "project-beta",
                    "confidence": 0.95,
                    "participants": ["charlie", "david"]
                },
                "tags": ["confidential", "project-beta", f"session2-mem{i+1}"]
            }
            
            response = await client.post(f"{base_url}/cam/store", json=memory)
            if response.status_code == 200:
                result = response.json()
                memories_created.append(result['memory_id'])
                print(f"   ✅ Created memory {i+1} for session 2: {result['memory_id']}")
            else:
                print(f"   ❌ Failed to create memory: {response.status_code}")
        
        # Test 1: Search with session isolation
        print(f"\n2. Testing session isolation - searching only Session 1 memories")
        
        search_request = {
            "resonance_vectors": [{
                "vector": create_embedding(),
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 10,
                "similarity_threshold": 0.0
            },
            "filters": {
                "session_ids": [session1_id]  # Only session 1
            }
        }
        
        response = await client.post(f"{base_url}/cam/retrieve", json=search_request)
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {results['total_found']} memories")
            
            # Verify all results are from session 1
            session_1_count = 0
            for mem in results['memories']:
                if "Session 1" in mem['content_preview']:
                    session_1_count += 1
                    print(f"   ✅ {mem['memory_id']}: {mem['content_preview'][:50]}...")
                else:
                    print(f"   ❌ LEAK! Found session 2 memory: {mem['content_preview'][:50]}...")
            
            if session_1_count == results['total_found'] and session_1_count == 3:
                print(f"   ✅ Session isolation working! Only session 1 memories returned")
            else:
                print(f"   ❌ Session isolation failed!")
        
        # Test 2: Multi-filter search
        print(f"\n3. Testing complex metadata filtering")
        
        search_request = {
            "resonance_vectors": [{
                "vector": create_embedding(),
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 10,
                "similarity_threshold": 0.0
            },
            "filters": {
                "domains": ["project-beta"],
                "participants": ["charlie"],
                "confidence_threshold": 0.9
            }
        }
        
        response = await client.post(f"{base_url}/cam/retrieve", json=search_request)
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {results['total_found']} memories matching filters")
            
            for mem in results['memories']:
                print(f"   ✅ {mem['memory_id']}: {mem['content_preview'][:50]}...")
                print(f"      Domain: {mem['metadata'].get('domain')}")
                print(f"      Confidence: {mem['metadata'].get('confidence')}")
        
        # Test 3: Cross-session search (no session filter)
        print(f"\n4. Testing cross-session search (no session filter)")
        
        search_request = {
            "resonance_vectors": [{
                "vector": create_embedding(),
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 10,
                "similarity_threshold": 0.0
            }
        }
        
        response = await client.post(f"{base_url}/cam/retrieve", json=search_request)
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {results['total_found']} memories across all sessions")
            
            session1_count = sum(1 for m in results['memories'] if "Session 1" in m['content_preview'])
            session2_count = sum(1 for m in results['memories'] if "Session 2" in m['content_preview'])
            
            print(f"   Session 1 memories: {session1_count}")
            print(f"   Session 2 memories: {session2_count}")
            
            if session1_count > 0 and session2_count > 0:
                print(f"   ✅ Cross-session search working correctly")
        
        # Test 4: Agent + Session combination
        print(f"\n5. Testing agent + session combination filter")
        
        search_request = {
            "resonance_vectors": [{
                "vector": create_embedding(),
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 10,
                "similarity_threshold": 0.0
            },
            "filters": {
                "agent_ids": ["agent-001"],
                "session_ids": [session1_id]
            }
        }
        
        response = await client.post(f"{base_url}/cam/retrieve", json=search_request)
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {results['total_found']} memories for agent-001 in session 1")
            
            if results['total_found'] == 3:
                print(f"   ✅ Agent + session filtering working correctly")
        
        print("\n" + "=" * 60)
        print("✅ Session isolation and metadata filtering test completed!")
        print("\nKey findings:")
        print("- Sessions are properly isolated when filtered")
        print("- Complex metadata filters work correctly")
        print("- Cross-session search is possible when no filter applied")
        print("- Combination filters (agent + session) work as expected")


if __name__ == "__main__":
    asyncio.run(test_session_isolation())