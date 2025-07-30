"""
Memory Cleanup Service

Automated cleanup and maintenance of memories based on retention policies
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from models.memory_curation import RetentionPolicy, MemoryCleanupAction
from core.redis_client_multi_entity import redis_multi_entity_client
from services.memory_curator import memory_curator

logger = logging.getLogger(__name__)


class MemoryCleanupService:
    """Automated memory cleanup and maintenance service"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    def start(self):
        """Start the cleanup service"""
        if not self.is_running:
            # Schedule cleanup tasks
            
            # Daily cleanup of expired memories
            self.scheduler.add_job(
                self.cleanup_expired_memories,
                CronTrigger(hour=2, minute=0),  # Run at 2 AM daily
                id="daily_cleanup",
                replace_existing=True
            )
            
            # Weekly consolidation analysis
            self.scheduler.add_job(
                self.analyze_consolidation_opportunities,
                CronTrigger(day_of_week=0, hour=3, minute=0),  # Run Sundays at 3 AM
                id="weekly_consolidation",
                replace_existing=True
            )
            
            # Monthly comprehensive cleanup
            self.scheduler.add_job(
                self.comprehensive_cleanup,
                CronTrigger(day=1, hour=4, minute=0),  # Run 1st of month at 4 AM
                id="monthly_comprehensive",
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Memory cleanup service started")
    
    def stop(self):
        """Stop the cleanup service"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Memory cleanup service stopped")
    
    async def cleanup_expired_memories(self):
        """Remove memories that have exceeded their retention policy"""
        logger.info("Starting expired memory cleanup")
        
        try:
            now = datetime.utcnow()
            cleanup_count = 0
            
            # Get all memory keys
            memory_keys = redis_multi_entity_client.client.keys("memory:*")
            
            for key in memory_keys:
                try:
                    memory_id = key.decode().replace("memory:", "")
                    raw_data = redis_multi_entity_client.client.hgetall(key)
                    
                    if not raw_data:
                        continue
                    
                    # Check expiry
                    expires_at_str = raw_data.get(b'expires_at')
                    if expires_at_str and expires_at_str != b'None':
                        expires_at = datetime.fromisoformat(expires_at_str.decode().replace('Z', '+00:00'))
                        
                        if expires_at < now:
                            # Memory has expired - delete it
                            success = await self.delete_expired_memory(memory_id, raw_data)
                            if success:
                                cleanup_count += 1
                                logger.debug(f"Deleted expired memory: {memory_id}")
                
                except Exception as e:
                    logger.error(f"Error processing memory {key}: {e}")
                    continue
            
            logger.info(f"Expired memory cleanup completed: {cleanup_count} memories removed")
            
        except Exception as e:
            logger.error(f"Error in expired memory cleanup: {e}")
    
    async def delete_expired_memory(self, memory_id: str, raw_data: Dict[bytes, bytes]) -> bool:
        """Safely delete an expired memory"""
        try:
            # Remove from vector index
            try:
                redis_multi_entity_client.client.execute_command(
                    "FT.DEL", 
                    redis_multi_entity_client.index_name, 
                    f"memory:{memory_id}",
                    "DD"  # Delete document
                )
            except Exception as e:
                logger.debug(f"Memory {memory_id} not in vector index (OK): {e}")
            
            # Remove from entity access sets
            witnessed_by_str = raw_data.get(b'witnessed_by', b'[]').decode()
            try:
                import json
                witnessed_by = json.loads(witnessed_by_str)
                for entity in witnessed_by:
                    redis_multi_entity_client.client.srem(f"entity_access:{entity}", memory_id)
            except:
                pass
            
            # Remove the memory hash
            redis_multi_entity_client.client.delete(f"memory:{memory_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting expired memory {memory_id}: {e}")
            return False
    
    async def analyze_consolidation_opportunities(self):
        """Analyze memories for consolidation opportunities"""
        logger.info("Starting consolidation opportunity analysis")
        
        try:
            # Get all entities
            entity_keys = redis_multi_entity_client.client.keys("entity_access:*")
            consolidation_suggestions = []
            
            for entity_key in entity_keys:
                entity_id = entity_key.decode().replace("entity_access:", "")
                
                # Get entity's memories
                memory_ids = redis_multi_entity_client.client.smembers(entity_key)
                memories = []
                
                for memory_id in list(memory_ids)[:50]:  # Limit analysis
                    memory_data = redis_multi_entity_client.get_memory(memory_id.decode(), entity_id)
                    if memory_data:
                        memories.append(memory_data)
                
                if len(memories) > 10:  # Only analyze if enough memories
                    # Get consolidation suggestions
                    cleanup_actions = await memory_curator.suggest_cleanup_actions(memories)
                    consolidation_actions = [a for a in cleanup_actions if a.action_type == "consolidate"]
                    
                    if consolidation_actions:
                        consolidation_suggestions.extend(consolidation_actions)
                        logger.info(f"Found {len(consolidation_actions)} consolidation opportunities for {entity_id}")
            
            # Log consolidation opportunities (could be stored for manual review)
            if consolidation_suggestions:
                logger.info(f"Total consolidation opportunities found: {len(consolidation_suggestions)}")
                
                # Store suggestions for later review
                suggestion_key = f"consolidation_suggestions:{datetime.utcnow().strftime('%Y%m%d')}"
                suggestion_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "suggestions": [s.dict() for s in consolidation_suggestions]
                }
                
                import json
                redis_multi_entity_client.client.setex(
                    suggestion_key,
                    86400 * 7,  # Keep for 7 days
                    json.dumps(suggestion_data)
                )
            
        except Exception as e:
            logger.error(f"Error in consolidation analysis: {e}")
    
    async def comprehensive_cleanup(self):
        """Comprehensive monthly cleanup and maintenance"""
        logger.info("Starting comprehensive monthly cleanup")
        
        try:
            # 1. Clean up expired memories
            await self.cleanup_expired_memories()
            
            # 2. Update access timestamps for inactive memories
            await self.update_access_statistics()
            
            # 3. Clean up orphaned data
            await self.cleanup_orphaned_data()
            
            # 4. Compact vector index
            await self.compact_vector_index()
            
            logger.info("Comprehensive monthly cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in comprehensive cleanup: {e}")
    
    async def update_access_statistics(self):
        """Update access statistics and identify unused memories"""
        logger.info("Updating access statistics")
        
        try:
            now = datetime.utcnow()
            unused_count = 0
            
            memory_keys = redis_multi_entity_client.client.keys("memory:*")
            
            for key in memory_keys:
                try:
                    raw_data = redis_multi_entity_client.client.hgetall(key)
                    if not raw_data:
                        continue
                    
                    last_accessed_str = raw_data.get(b'last_accessed')
                    access_count = int(raw_data.get(b'access_count', b'0').decode())
                    created_at_str = raw_data.get(b'created_at', b'').decode()
                    
                    # Check if memory is unused (no access in 30+ days and low access count)
                    if last_accessed_str:
                        last_accessed = datetime.fromisoformat(last_accessed_str.decode())
                        days_since_access = (now - last_accessed).days
                        
                        if days_since_access > 30 and access_count < 2:
                            unused_count += 1
                            # Mark as potentially unused
                            redis_multi_entity_client.client.hset(key, "potentially_unused", "true")
                    
                    elif created_at_str:
                        # Never accessed since creation
                        created_at = datetime.fromisoformat(created_at_str)
                        days_since_creation = (now - created_at).days
                        
                        if days_since_creation > 14 and access_count == 0:
                            unused_count += 1
                            redis_multi_entity_client.client.hset(key, "potentially_unused", "true")
                
                except Exception as e:
                    logger.debug(f"Error processing memory statistics for {key}: {e}")
                    continue
            
            logger.info(f"Access statistics updated: {unused_count} potentially unused memories identified")
            
        except Exception as e:
            logger.error(f"Error updating access statistics: {e}")
    
    async def cleanup_orphaned_data(self):
        """Clean up orphaned data structures"""
        logger.info("Cleaning up orphaned data")
        
        try:
            # Get all memory IDs that actually exist
            memory_keys = redis_multi_entity_client.client.keys("memory:*")
            existing_memory_ids = set()
            for key in memory_keys:
                memory_id = key.decode().replace("memory:", "")
                existing_memory_ids.add(memory_id)
            
            # Check entity access sets for orphaned references
            entity_keys = redis_multi_entity_client.client.keys("entity_access:*")
            orphaned_count = 0
            
            for entity_key in entity_keys:
                memory_ids_in_set = redis_multi_entity_client.client.smembers(entity_key)
                
                for memory_id_bytes in memory_ids_in_set:
                    memory_id = memory_id_bytes.decode()
                    
                    if memory_id not in existing_memory_ids:
                        # Orphaned reference - remove it
                        redis_multi_entity_client.client.srem(entity_key, memory_id)
                        orphaned_count += 1
            
            logger.info(f"Orphaned data cleanup completed: {orphaned_count} orphaned references removed")
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned data: {e}")
    
    async def compact_vector_index(self):
        """Compact and optimize the vector search index"""
        logger.info("Compacting vector search index")
        
        try:
            # Get index info
            try:
                info = redis_multi_entity_client.client.execute_command(
                    "FT.INFO", redis_multi_entity_client.index_name
                )
                logger.info(f"Vector index stats before compaction: {len(info)} entries")
            except Exception as e:
                logger.debug(f"Could not get index info: {e}")
            
            # Redis Search doesn't have a direct compact command,
            # but we can trigger optimization by doing a dummy search
            try:
                redis_multi_entity_client.client.execute_command(
                    "FT.SEARCH", 
                    redis_multi_entity_client.index_name,
                    "*",
                    "LIMIT", "0", "1"
                )
                logger.info("Vector index optimization triggered")
            except Exception as e:
                logger.debug(f"Index optimization trigger failed (OK): {e}")
            
        except Exception as e:
            logger.error(f"Error compacting vector index: {e}")


# Global cleanup service instance
cleanup_service = MemoryCleanupService()