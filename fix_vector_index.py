#!/usr/bin/env python3
"""
Fix missing vector index in Redis
"""

import redis
from core.config import settings
from core.redis_client_hash import RedisHashClient


def fix_vector_index():
    """Create the vector index if it doesn't exist"""
    
    print(f"🔧 Checking vector index: {settings.vector_index_name}")
    
    try:
        # Create Redis client
        client = RedisHashClient()
        client.connect()
        
        # Check if index exists
        try:
            info = client.client.execute_command('FT.INFO', settings.vector_index_name)
            print(f"✅ Vector index already exists!")
            print(f"   Documents indexed: {info[info.index('num_docs') + 1]}")
            return
        except redis.exceptions.ResponseError as e:
            if "Unknown Index name" in str(e) or "No such index" in str(e):
                print(f"⚠️  Vector index not found, creating it...")
            else:
                raise
        
        # Create the index
        client.ensure_vector_index()
        
        # Verify it was created
        try:
            info = client.client.execute_command('FT.INFO', settings.vector_index_name)
            print(f"✅ Vector index created successfully!")
            print(f"   Index name: {settings.vector_index_name}")
            print(f"   Vector dimensions: {settings.vector_dimensions}")
            print(f"   Distance metric: {settings.vector_distance_metric}")
        except Exception as e:
            print(f"❌ Failed to verify index creation: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(fix_vector_index())