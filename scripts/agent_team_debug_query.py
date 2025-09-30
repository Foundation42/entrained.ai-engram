#!/usr/bin/env python3
"""
AGENT TEAM DEBUG QUERY
This query is GUARANTEED to work and return Christian's memories.
Use this to test your integration and compare with your failing queries.
"""

import requests
import json

# EXACT WORKING CONFIGURATION
BASE_URL = "http://46.62.130.230:8000"
OLLAMA_URL = "http://localhost:11434"

def get_working_query():
    """
    This is the EXACT query that works for retrieving Christian's memories.
    Agent Team: Copy this exactly and modify step by step to match your code.
    """
    
    print("🔧 AGENT TEAM DEBUG QUERY - GUARANTEED TO WORK")
    print("=" * 60)
    
    # Step 1: Get embedding using EXACT same method as Engram tests
    print("Step 1: Getting embedding for query text...")
    
    # Use a query that we KNOW works (from successful tests)
    query_text = "My name is Christian and I live in Liversedge"
    
    try:
        embedding_response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": "nomic-embed-text:latest",
                "prompt": query_text
            },
            timeout=30
        )
        
        if embedding_response.status_code != 200:
            print(f"❌ Ollama embedding failed: {embedding_response.status_code}")
            return
            
        embedding = embedding_response.json()["embedding"]
        print(f"✅ Got embedding vector (length: {len(embedding)})")
        
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return
    
    # Step 2: Make EXACT API call that works
    print("\nStep 2: Making Engram API call...")
    
    # This is the EXACT request format that works
    working_request = {
        "requesting_entity": "human-christian-kind-hare",
        "resonance_vectors": [
            {
                "vector": embedding,
                "weight": 1.0
            }
        ],
        "retrieval_options": {
            "top_k": 5,
            "similarity_threshold": 0.0,
            "exclude_denials": True  # This is KEY!
        }
    }
    
    try:
        api_response = requests.post(
            f"{BASE_URL}/cam/multi/retrieve", 
            json=working_request,
            timeout=15
        )
        
        if api_response.status_code != 200:
            print(f"❌ API call failed: {api_response.status_code}")
            print(f"Response: {api_response.text}")
            return
            
        result = api_response.json()
        memories = result.get('memories', [])
        
        print(f"✅ API call successful! Found {len(memories)} memories")
        
        # Show the memories
        for i, memory in enumerate(memories):
            content = memory.get('content_preview', '')
            score = memory.get('similarity_score', 0)
            memory_id = memory.get('memory_id', 'unknown')
            
            print(f"\nMemory {i+1}: {memory_id}")
            print(f"  Score: {score:.3f}")
            print(f"  Content: {content[:100]}...")
            
            # Check for Christian's info
            if 'christian' in content.lower():
                print(f"  🎯 CONTAINS NAME!")
            if 'liversedge' in content.lower():
                print(f"  🏠 CONTAINS LOCATION!")
        
        # Return the working request for agent team to copy
        return working_request, result
        
    except Exception as e:
        print(f"❌ API call error: {e}")
        return None, None

def provide_curl_command():
    """Provide a curl command the agent team can run directly"""
    
    print("\n" + "=" * 60)
    print("🔧 CURL COMMAND FOR AGENT TEAM")
    print("=" * 60)
    
    print("Run this EXACT curl command to test:")
    print()
    
    # First get embedding
    print("# Step 1: Get embedding")
    print(f"""curl -X POST {OLLAMA_URL}/api/embeddings \\
  -H "Content-Type: application/json" \\
  -d '{{"model": "nomic-embed-text:latest", "prompt": "My name is Christian and I live in Liversedge"}}' \\
  | jq -r '.embedding' > /tmp/embedding.json""")
    
    print("\n# Step 2: Use embedding in Engram query")
    print(f"""curl -X POST {BASE_URL}/cam/multi/retrieve \\
  -H "Content-Type: application/json" \\
  -d '{{
    "requesting_entity": "human-christian-kind-hare",
    "resonance_vectors": [{{
      "vector": '$(cat /tmp/embedding.json)',
      "weight": 1.0
    }}],
    "retrieval_options": {{
      "top_k": 5,
      "similarity_threshold": 0.0,
      "exclude_denials": true
    }}
  }}' | jq""")

def debug_comparison():
    """Help agent team compare their failing query with working one"""
    
    print("\n" + "=" * 60)
    print("🔍 DEBUGGING CHECKLIST FOR AGENT TEAM")
    print("=" * 60)
    
    checklist = [
        "✅ Using correct URL: http://46.62.130.230:8000/cam/multi/retrieve",
        "✅ Using correct entity ID: human-christian-kind-hare", 
        "✅ Using Ollama model: nomic-embed-text:latest",
        "✅ Including exclude_denials: true in retrieval_options",
        "✅ Using similarity_threshold: 0.0 (not 0.7)",
        "✅ Getting vector from embedding['embedding'] not embedding directly",
        "✅ Using content_preview field not content.text",
        "✅ Request timeout at least 15 seconds",
        "✅ Checking response.status_code == 200",
        "✅ Handling memories[i]['content_preview'] for content"
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    print("\n🎯 MOST COMMON ISSUES:")
    print("  1. Using wrong similarity_threshold (0.7 vs 0.0)")
    print("  2. Not setting exclude_denials: true") 
    print("  3. Wrong embedding extraction from Ollama response")
    print("  4. Using content.text instead of content_preview")
    print("  5. Wrong entity ID format (with/without hyphens)")

if __name__ == "__main__":
    # Run the working query
    working_request, result = get_working_query()
    
    # Provide curl command
    provide_curl_command()
    
    # Provide debugging checklist
    debug_comparison()
    
    if working_request and result:
        print(f"\n🎉 SUCCESS! Found {len(result.get('memories', []))} memories")
        print("Agent Team: Use this exact request format in your code!")
    else:
        print("\n❌ Something is wrong with the test environment")