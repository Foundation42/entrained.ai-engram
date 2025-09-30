#!/usr/bin/env python3
"""
Migration script to update from Ollama (768D) to OpenAI embeddings (1536D)

This script will:
1. Drop the existing Redis vector indices (768 dimensions)
2. Recreate them with OpenAI dimensions (1536 dimensions)
3. All existing memories will need to be re-embedded with OpenAI

IMPORTANT: This will temporarily make existing memories unsearchable until re-embedded.
"""

import redis
import logging
from core.config import settings
from core.redis_client_hash import redis_client
from core.redis_client_multi_entity import redis_multi_entity_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_redis_indices():
    """Drop and recreate Redis indices with new dimensions"""
    try:
        # Connect to Redis
        redis_client.connect()
        redis_multi_entity_client.connect()
        
        logger.info("🔄 MIGRATING TO OPENAI EMBEDDINGS (768D → 1536D)")
        logger.info("=" * 60)
        
        # Drop existing indices
        logger.info("📤 Dropping old vector indices...")
        
        try:
            redis_client.client.execute_command('FT.DROPINDEX', settings.vector_index_name, 'DD')
            logger.info(f"✅ Dropped hash index: {settings.vector_index_name}")
        except Exception as e:
            logger.info(f"ℹ️  Hash index {settings.vector_index_name} not found (expected): {e}")
        
        try:
            multi_entity_index = f"{settings.vector_index_name}_multi_entity"
            redis_multi_entity_client.client.execute_command('FT.DROPINDEX', multi_entity_index, 'DD')
            logger.info(f"✅ Dropped multi-entity index: {multi_entity_index}")
        except Exception as e:
            logger.info(f"ℹ️  Multi-entity index {multi_entity_index} not found (expected): {e}")
        
        # Recreate indices with new dimensions
        logger.info("📥 Creating new vector indices with OpenAI dimensions...")
        
        # Force recreation of indices
        redis_client.vector_index_created = False
        redis_multi_entity_client.vector_index_created = False
        
        # This will create the indices with the new dimensions from settings
        redis_client._create_vector_index()
        redis_multi_entity_client._create_vector_index()
        
        logger.info("=" * 60)
        logger.info("🎉 MIGRATION COMPLETE!")
        logger.info(f"✅ Updated vector dimensions: 768 → {settings.vector_dimensions}")
        logger.info("⚠️  NOTE: Existing memories will need to be re-embedded with OpenAI")
        logger.info("✅ New comments will automatically use OpenAI embeddings")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False
    finally:
        redis_client.close()

if __name__ == "__main__":
    success = migrate_redis_indices()
    if success:
        print("\n🚀 Ready to deploy OpenAI embeddings!")
    else:
        print("\n💥 Migration failed - check logs")
        exit(1)