#!/usr/bin/env python3
"""
Test Redis TAG field behavior with empty strings
"""

import redis
from core.config import settings
import time


def test_tag_filtering():
    """Test how Redis handles TAG filtering with empty values"""
    
    print("🧪 Testing Redis TAG field filtering")
    print("=" * 60)
    
    # Connect to Redis
    client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=False
    )
    
    # Clean up test data
    for key in client.scan_iter("test:*"):
        client.delete(key)
    
    # Create test index
    index_name = "test_tag_idx"
    try:
        client.execute_command('FT.DROPINDEX', index_name, 'DD')
    except:
        pass
    
    print("\n1. Creating test index with TAG field")
    client.execute_command(
        'FT.CREATE',
        index_name,
        'ON', 'HASH',
        'PREFIX', '1', 'test:',
        'SCHEMA',
        'session_id', 'TAG', 'SEPARATOR', ',',
        'content', 'TEXT'
    )
    
    # Test data
    test_cases = [
        ("test:1", {"session_id": "session-123", "content": "Memory with session"}),
        ("test:2", {"session_id": "", "content": "Memory with empty session"}),
        ("test:3", {"session_id": "none", "content": "Memory with 'none' session"}),
        ("test:4", {"content": "Memory without session_id field"}),  # Missing field
    ]
    
    # Store test data
    print("\n2. Storing test memories")
    for key, data in test_cases:
        client.hset(key, mapping=data)
        print(f"   Stored {key}: session_id='{data.get('session_id', 'MISSING')}'")
    
    time.sleep(0.5)  # Let Redis index
    
    # Test searches
    print("\n3. Testing searches")
    
    # Search for specific session
    print("\n   a) Search for session_id='session-123'")
    results = client.execute_command(
        'FT.SEARCH', index_name,
        '@session_id:{session-123}',
        'RETURN', '2', 'session_id', 'content'
    )
    print(f"      Found {results[0]} results")
    
    # Search for empty session
    print("\n   b) Search for empty session_id")
    try:
        results = client.execute_command(
            'FT.SEARCH', index_name,
            '@session_id:{""}',  # Empty string in quotes
            'RETURN', '2', 'session_id', 'content'
        )
        print(f"      Found {results[0]} results")
    except Exception as e:
        print(f"      Error: {e}")
    
    # Search for 'none' session
    print("\n   c) Search for session_id='none'")
    results = client.execute_command(
        'FT.SEARCH', index_name,
        '@session_id:{none}',
        'RETURN', '2', 'session_id', 'content'
    )
    print(f"      Found {results[0]} results")
    
    # Search all
    print("\n   d) Search all (no filter)")
    results = client.execute_command(
        'FT.SEARCH', index_name,
        '*',
        'RETURN', '2', 'session_id', 'content'
    )
    print(f"      Found {results[0]} results")
    for i in range(1, len(results), 2):
        if i+1 < len(results):
            fields = results[i+1]
            session_id = fields[fields.index(b'session_id')+1] if b'session_id' in fields else b'MISSING'
            content = fields[fields.index(b'content')+1]
            print(f"      - {results[i].decode()}: session_id='{session_id.decode() if isinstance(session_id, bytes) else session_id}'")
    
    # Clean up
    client.execute_command('FT.DROPINDEX', index_name, 'DD')
    for key in client.scan_iter("test:*"):
        client.delete(key)
    
    print("\n" + "=" * 60)
    print("🔍 KEY FINDINGS:")
    print("1. Empty strings in TAG fields may not filter correctly")
    print("2. Using 'none' as a placeholder is more reliable")
    print("3. Missing fields behave differently than empty strings")


if __name__ == "__main__":
    test_tag_filtering()