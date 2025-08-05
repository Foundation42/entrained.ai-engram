#!/usr/bin/env python3
"""
Recreate Redis vector indices with correct dimensions for OpenAI embeddings
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.redis_client_hash import redis_client
from core.redis_client_multi_entity import redis_multi_entity_client
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def recreate_redis_indices():
    """Drop and recreate Redis vector indices with correct dimensions"""
    print("🔧 RECREATING REDIS VECTOR INDICES")
    print("=" * 60)
    print(f"📊 New vector dimensions: {settings.vector_dimensions}")
    print(f"📊 Vector algorithm: {settings.vector_algorithm}")
    print(f"📊 Distance metric: {settings.vector_distance_metric}")
    
    # Connect to Redis clients
    print("\n🔌 Connecting to Redis...")
    redis_client.connect()
    redis_multi_entity_client.connect()
    
    # Drop existing indices
    print("\n🗑️ Dropping existing vector indices...")
    
    # Drop single-entity index
    try:
        redis_client.client.execute_command('FT.DROPINDEX', settings.vector_index_name, 'DD')
        print(f"   ✅ Dropped single-entity index: {settings.vector_index_name}")
    except Exception as e:
        print(f"   ⚠️ Single-entity index not found or already dropped: {e}")
    
    # Drop multi-entity index  
    multi_entity_index_name = f"{settings.vector_index_name}_multi"
    try:
        redis_multi_entity_client.client.execute_command('FT.DROPINDEX', multi_entity_index_name, 'DD')
        print(f"   ✅ Dropped multi-entity index: {multi_entity_index_name}")
    except Exception as e:
        print(f"   ⚠️ Multi-entity index not found or already dropped: {e}")
    
    # Reset index creation flags
    redis_client.vector_index_created = False
    redis_multi_entity_client.vector_index_created = False
    
    # Recreate indices with correct dimensions
    print(f"\n🔨 Recreating indices with {settings.vector_dimensions} dimensions...")
    
    # Recreate single-entity index
    try:
        redis_client._ensure_vector_index()
        print(f"   ✅ Recreated single-entity index: {settings.vector_index_name}")
    except Exception as e:
        print(f"   ❌ Failed to recreate single-entity index: {e}")
    
    # Recreate multi-entity index
    try:
        redis_multi_entity_client._ensure_vector_index()
        print(f"   ✅ Recreated multi-entity index: {multi_entity_index_name}")
    except Exception as e:
        print(f"   ❌ Failed to recreate multi-entity index: {e}")
    
    # Verify indices
    print(f"\n🔍 Verifying recreated indices...")
    
    # Verify single-entity index
    try:
        info = redis_client.client.execute_command('FT.INFO', settings.vector_index_name)
        print(f"   ✅ Single-entity index verified: {settings.vector_index_name}")
        
        # Parse the info to find vector field dimensions
        for i, item in enumerate(info):
            if isinstance(item, bytes) and item.decode() == 'embedding':
                # The next few items contain the vector field info
                for j in range(i, min(i+20, len(info))):
                    if isinstance(info[j], bytes) and info[j].decode() == 'DIM':
                        if j+1 < len(info):
                            dims = info[j+1].decode() if isinstance(info[j+1], bytes) else str(info[j+1])
                            print(f"      📊 Vector dimensions: {dims}")
                            break
                break
                
    except Exception as e:
        print(f"   ❌ Failed to verify single-entity index: {e}")
    
    # Verify multi-entity index
    try:
        info = redis_multi_entity_client.client.execute_command('FT.INFO', multi_entity_index_name)
        print(f"   ✅ Multi-entity index verified: {multi_entity_index_name}")
        
        # Parse the info to find vector field dimensions
        for i, item in enumerate(info):
            if isinstance(item, bytes) and item.decode() == 'embedding':
                # The next few items contain the vector field info
                for j in range(i, min(i+20, len(info))):
                    if isinstance(info[j], bytes) and info[j].decode() == 'DIM':
                        if j+1 < len(info):
                            dims = info[j+1].decode() if isinstance(info[j+1], bytes) else str(info[j+1])
                            print(f"      📊 Vector dimensions: {dims}")
                            break
                break
                
    except Exception as e:
        print(f"   ❌ Failed to verify multi-entity index: {e}")
    
    print(f"\n" + "=" * 60)
    print("🎯 REDIS INDICES RECREATION COMPLETE")
    print("⚠️  Note: All existing vector data has been deleted!")
    print("💡 You may need to re-store some test data to verify functionality.")

if __name__ == "__main__":
    asyncio.run(recreate_redis_indices())