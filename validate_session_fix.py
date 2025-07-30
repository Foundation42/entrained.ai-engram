#!/usr/bin/env python3
"""
Validate that session isolation is working correctly
"""

import httpx
import asyncio
from datetime import datetime
import uuid
import json


async def validate_session_isolation():
    base_url = "http://localhost:8000"
    
    print("✅ Validating Session Isolation Fix")
    print("=" * 80)
    
    # Create test sessions with hyphens (problematic characters)
    session1_id = f"test-session-{uuid.uuid4()}"
    session2_id = f"test-session-{uuid.uuid4()}"
    
    # Simple embedding for testing
    test_embedding = [0.1] * 768
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\nSession 1: {session1_id}")
        print(f"Session 2: {session2_id}")
        
        # Store memory in session 1
        print("\n1. Storing 'Emily' in Session 1")
        memory1 = {
            "content": {
                "text": "My name is Emily and I love painting",
                "media": []
            },
            "primary_vector": test_embedding,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "test-agent-001",
                "memory_type": "personal",
                "session_id": session1_id,
                "confidence": 0.95
            },
            "tags": ["name", "identity", "emily"]
        }
        
        response = await client.post(f"{base_url}/cam/store", json=memory1)
        if response.status_code == 200:
            print("   ✅ Stored Emily's memory")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return
        
        # Store memory in session 2
        print("\n2. Storing 'David' in Session 2")
        memory2 = {
            "content": {
                "text": "My name is David and I enjoy coding",
                "media": []
            },
            "primary_vector": test_embedding,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "test-agent-001",
                "memory_type": "personal",
                "session_id": session2_id,
                "confidence": 0.95
            },
            "tags": ["name", "identity", "david"]
        }
        
        response = await client.post(f"{base_url}/cam/store", json=memory2)
        if response.status_code == 200:
            print("   ✅ Stored David's memory")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return
        
        # Wait a moment for indexing
        await asyncio.sleep(0.5)
        
        # Test 1: Search in Session 1 (should find only Emily)
        print("\n3. Searching in Session 1 (expecting only Emily)")
        search_request = {
            "resonance_vectors": [{
                "vector": test_embedding,
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 10,
                "similarity_threshold": 0.0
            },
            "filters": {
                "session_ids": [session1_id],
                "agent_ids": ["test-agent-001"]
            }
        }
        
        response = await client.post(f"{base_url}/cam/retrieve", json=search_request)
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {results['total_found']} memories")
            
            emily_found = False
            david_found = False
            
            for mem in results['memories']:
                if "Emily" in mem['content_preview']:
                    emily_found = True
                    print(f"   ✅ Found Emily: {mem['content_preview']}")
                elif "David" in mem['content_preview']:
                    david_found = True
                    print(f"   ❌ LEAK! Found David: {mem['content_preview']}")
            
            if emily_found and not david_found and results['total_found'] == 1:
                print("   ✅ Session 1 isolation WORKING!")
            else:
                print("   ❌ Session 1 isolation FAILED!")
        else:
            print(f"   ❌ Search failed: {response.status_code}")
        
        # Test 2: Search in Session 2 (should find only David)
        print("\n4. Searching in Session 2 (expecting only David)")
        search_request['filters']['session_ids'] = [session2_id]
        
        response = await client.post(f"{base_url}/cam/retrieve", json=search_request)
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {results['total_found']} memories")
            
            emily_found = False
            david_found = False
            
            for mem in results['memories']:
                if "Emily" in mem['content_preview']:
                    emily_found = True
                    print(f"   ❌ LEAK! Found Emily: {mem['content_preview']}")
                elif "David" in mem['content_preview']:
                    david_found = True
                    print(f"   ✅ Found David: {mem['content_preview']}")
            
            if david_found and not emily_found and results['total_found'] == 1:
                print("   ✅ Session 2 isolation WORKING!")
            else:
                print("   ❌ Session 2 isolation FAILED!")
        else:
            print(f"   ❌ Search failed: {response.status_code}")
        
        # Test 3: Search without session filter (should find both)
        print("\n5. Searching without session filter (expecting both)")
        search_request_no_session = {
            "resonance_vectors": [{
                "vector": test_embedding,
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 10,
                "similarity_threshold": 0.0
            },
            "filters": {
                "agent_ids": ["test-agent-001"]
                # No session filter
            }
        }
        
        response = await client.post(f"{base_url}/cam/retrieve", json=search_request_no_session)
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {results['total_found']} memories")
            
            emily_found = False
            david_found = False
            
            for mem in results['memories']:
                if "Emily" in mem['content_preview']:
                    emily_found = True
                    print(f"   ✅ Found Emily")
                elif "David" in mem['content_preview']:
                    david_found = True
                    print(f"   ✅ Found David")
            
            if emily_found and david_found:
                print("   ✅ Cross-session search working!")
        
        print("\n" + "=" * 80)
        print("\n🎯 SUMMARY:")
        print("If all tests passed, session isolation is working correctly!")
        print("The fix handles:")
        print("- Empty filters dict (no longer None)")
        print("- Special characters in session IDs (hyphens escaped)")
        print("- Proper session-based filtering")


if __name__ == "__main__":
    asyncio.run(validate_session_isolation())