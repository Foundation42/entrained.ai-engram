#!/usr/bin/env python3
"""
Inspect stored memories to check session_id values
"""

import redis
from core.config import settings
import json


def inspect_memories():
    """Inspect all stored memories and their session_ids"""
    
    print("🔍 Inspecting Stored Memories")
    print("=" * 80)
    
    # Connect to Redis
    client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=False
    )
    
    # Find all memory keys
    memory_keys = list(client.scan_iter("memory:*"))
    print(f"\nFound {len(memory_keys)} memories in Redis")
    
    if not memory_keys:
        print("No memories found!")
        return
    
    # Inspect each memory
    print("\nMemory Details:")
    print("-" * 80)
    
    session_stats = {}
    
    for i, key in enumerate(memory_keys[:10], 1):  # Limit to first 10
        key_str = key.decode('utf-8')
        print(f"\n{i}. Key: {key_str}")
        
        # Get all hash fields
        memory_data = client.hgetall(key)
        
        # Decode and display relevant fields
        session_id = memory_data.get(b'session_id', b'MISSING').decode('utf-8')
        agent_id = memory_data.get(b'agent_id', b'MISSING').decode('utf-8')
        content = memory_data.get(b'content', b'').decode('utf-8')[:100]
        
        print(f"   Session ID: '{session_id}' (length: {len(session_id)})")
        print(f"   Agent ID: {agent_id}")
        print(f"   Content: {content}...")
        
        # Parse metadata JSON if available
        if b'metadata_json' in memory_data:
            try:
                metadata = json.loads(memory_data[b'metadata_json'].decode('utf-8'))
                print(f"   Metadata session_id: '{metadata.get('session_id', 'MISSING')}'")
            except:
                pass
        
        # Track session statistics
        session_stats[session_id] = session_stats.get(session_id, 0) + 1
    
    # Summary
    print("\n" + "=" * 80)
    print("\nSession ID Summary:")
    for session_id, count in session_stats.items():
        print(f"   '{session_id}': {count} memories")
    
    # Test a search with empty session
    print("\n" + "=" * 80)
    print("\nTesting Search Filters:")
    
    # Try to search for memories with empty session_id
    try:
        print("\n1. Searching for session_id='' (empty string)")
        results = client.execute_command(
            'FT.SEARCH',
            settings.vector_index_name,
            '@session_id:{""}',
            'RETURN', '2', 'session_id', 'content',
            'LIMIT', '0', '5'
        )
        print(f"   Found {results[0]} results")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Try to search for memories with 'none' session_id
    try:
        print("\n2. Searching for session_id='none'")
        results = client.execute_command(
            'FT.SEARCH',
            settings.vector_index_name,
            '@session_id:{none}',
            'RETURN', '2', 'session_id', 'content',
            'LIMIT', '0', '5'
        )
        print(f"   Found {results[0]} results")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    inspect_memories()