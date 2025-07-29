#!/usr/bin/env python3
"""
Flush all memories from the Engram Redis server
"""

import redis
import sys
from core.config import settings


def flush_memories():
    """Remove all memory-related keys from Redis"""
    
    print("⚠️  WARNING: This will delete ALL memories from the Engram server!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Aborted.")
        return
    
    try:
        # Connect to Redis
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=False
        )
        
        # Test connection
        client.ping()
        print(f"✅ Connected to Redis at {settings.redis_host}:{settings.redis_port}")
        
        # Count keys before deletion
        all_keys = []
        memory_keys = []
        annotation_keys = []
        causality_keys = []
        
        # Scan for all keys
        for key in client.scan_iter("*"):
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            all_keys.append(key_str)
            
            if key_str.startswith("memory:"):
                memory_keys.append(key)
            elif key_str.startswith("annotations:"):
                annotation_keys.append(key)
            elif key_str.startswith("causality:"):
                causality_keys.append(key)
        
        print(f"\nFound {len(all_keys)} total keys:")
        print(f"  - {len(memory_keys)} memory keys")
        print(f"  - {len(annotation_keys)} annotation keys")
        print(f"  - {len(causality_keys)} causality keys")
        
        if not memory_keys and not annotation_keys and not causality_keys:
            print("\n✅ No memories to flush!")
            return
        
        # Delete all memory-related keys
        print("\nFlushing memories...")
        
        deleted_count = 0
        
        # Delete in batches for efficiency
        batch_size = 1000
        
        for keys_to_delete in [memory_keys, annotation_keys, causality_keys]:
            for i in range(0, len(keys_to_delete), batch_size):
                batch = keys_to_delete[i:i + batch_size]
                if batch:
                    deleted_count += client.delete(*batch)
        
        # Also delete the vector index (it will be recreated automatically)
        try:
            client.execute_command('FT.DROPINDEX', settings.vector_index_name)
            print(f"✅ Dropped vector index: {settings.vector_index_name}")
        except:
            print(f"ℹ️  Vector index {settings.vector_index_name} not found or already dropped")
        
        print(f"\n✅ Successfully flushed {deleted_count} keys!")
        
        # Verify
        remaining = len(list(client.scan_iter("memory:*")))
        if remaining == 0:
            print("✅ All memories have been removed!")
        else:
            print(f"⚠️  Warning: {remaining} memory keys still remain")
            
    except redis.ConnectionError:
        print(f"❌ Could not connect to Redis at {settings.redis_host}:{settings.redis_port}")
        print("Make sure Redis is running and accessible.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def flush_all_redis():
    """Nuclear option - flush entire Redis database"""
    print("\n🚨 DANGER: This will delete EVERYTHING in the Redis database!")
    print("This includes all memories, configurations, and any other data.")
    response = input("Are you REALLY sure? Type 'DELETE EVERYTHING' to confirm: ")
    
    if response != 'DELETE EVERYTHING':
        print("Aborted.")
        return
    
    try:
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password
        )
        
        client.flushdb()
        print("💥 All Redis data has been deleted!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Flush memories from Engram")
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Flush entire Redis database (DANGEROUS!)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    args = parser.parse_args()
    
    if args.all:
        flush_all_redis()
    else:
        flush_memories()