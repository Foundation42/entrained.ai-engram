"""
Admin API endpoints for Engram

Provides safe administration operations like database cleanup
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging
from typing import Dict, Any
import secrets

from core.redis_client_hash import redis_client
from core.redis_client_multi_entity import redis_multi_entity_client

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBasic()

# Simple authentication (in production, use proper auth)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "engram-admin-2025"  # Change this in production!


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.post("/admin/flush/memories", dependencies=[Depends(verify_admin)])
async def safe_flush_memories() -> Dict[str, Any]:
    """
    Safely flush all memories while preserving vector indexes
    
    This is better than the standalone flush script because:
    - It preserves vector indexes (no recreation needed)
    - It's accessible via API
    - It provides detailed feedback
    - It handles both single-agent and multi-entity systems
    """
    logger.warning("Admin requested safe memory flush")
    
    try:
        # Count existing data
        single_agent_keys = []
        multi_entity_keys = []
        entity_access_keys = []
        situation_keys = []
        
        # Scan for memory-related keys
        for key in redis_client.client.scan_iter("*"):
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            
            if key_str.startswith("memory:"):
                # Determine if it's single-agent or multi-entity based on content
                try:
                    memory_data = redis_client.client.hgetall(key)
                    if b'witnessed_by' in memory_data:
                        multi_entity_keys.append(key)
                    else:
                        single_agent_keys.append(key)
                except:
                    # If we can't read it, assume single-agent
                    single_agent_keys.append(key)
                    
            elif key_str.startswith("entity_access:"):
                entity_access_keys.append(key)
            elif key_str.startswith("situation:"):
                situation_keys.append(key)
        
        initial_counts = {
            "single_agent_memories": len(single_agent_keys),
            "multi_entity_memories": len(multi_entity_keys),
            "entity_access_keys": len(entity_access_keys),
            "situation_keys": len(situation_keys),
            "total_keys": len(single_agent_keys) + len(multi_entity_keys) + len(entity_access_keys) + len(situation_keys)
        }
        
        logger.info(f"Found {initial_counts['total_keys']} keys to delete")
        
        if initial_counts['total_keys'] == 0:
            return {
                "status": "success",
                "message": "No memories to flush",
                "deleted_counts": initial_counts,
                "indexes_preserved": True
            }
        
        # Delete memory keys in batches
        deleted_count = 0
        batch_size = 1000
        
        all_keys = single_agent_keys + multi_entity_keys + entity_access_keys + situation_keys
        
        for i in range(0, len(all_keys), batch_size):
            batch = all_keys[i:i + batch_size]
            if batch:
                deleted_count += redis_client.client.delete(*batch)
        
        # Verify deletion
        remaining_memories = len(list(redis_client.client.scan_iter("memory:*")))
        remaining_entity_access = len(list(redis_client.client.scan_iter("entity_access:*")))
        remaining_situations = len(list(redis_client.client.scan_iter("situation:*")))
        
        # Check that indexes are still intact
        single_agent_index_exists = True
        multi_entity_index_exists = True
        
        try:
            redis_client.client.execute_command('FT.INFO', 'engram_vector_idx')
        except:
            single_agent_index_exists = False
            
        try:
            redis_client.client.execute_command('FT.INFO', 'engram_vector_idx_multi')
        except:
            multi_entity_index_exists = False
        
        result = {
            "status": "success",
            "message": f"Successfully flushed {deleted_count} keys",
            "initial_counts": initial_counts,
            "deleted_count": deleted_count,
            "remaining_counts": {
                "memories": remaining_memories,
                "entity_access": remaining_entity_access,
                "situations": remaining_situations
            },
            "indexes_preserved": {
                "single_agent_index": single_agent_index_exists,
                "multi_entity_index": multi_entity_index_exists
            }
        }
        
        if not single_agent_index_exists or not multi_entity_index_exists:
            result["warning"] = "Some vector indexes are missing - they will be auto-created on next use"
        
        logger.info(f"Safe flush completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Safe flush failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flush operation failed: {str(e)}"
        )


@router.post("/admin/recreate/indexes", dependencies=[Depends(verify_admin)])
async def recreate_indexes() -> Dict[str, Any]:
    """
    Recreate vector indexes if they're missing
    
    Useful after manual Redis operations or as a maintenance task
    """
    logger.info("Admin requested index recreation")
    
    try:
        results = {}
        
        # Recreate single-agent index
        try:
            redis_client._ensure_vector_index()
            results["single_agent"] = "recreated_successfully"
        except Exception as e:
            results["single_agent"] = f"failed: {str(e)}"
        
        # Recreate multi-entity index
        try:
            redis_multi_entity_client._ensure_vector_index()
            results["multi_entity"] = "recreated_successfully"
        except Exception as e:
            results["multi_entity"] = f"failed: {str(e)}"
        
        return {
            "status": "success",
            "message": "Index recreation completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Index recreation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Index recreation failed: {str(e)}"
        )


@router.get("/admin/status", dependencies=[Depends(verify_admin)])
async def admin_status() -> Dict[str, Any]:
    """
    Get detailed system status for admin monitoring
    """
    try:
        # Count different types of keys
        memory_keys = len(list(redis_client.client.scan_iter("memory:*")))
        entity_access_keys = len(list(redis_client.client.scan_iter("entity_access:*")))
        situation_keys = len(list(redis_client.client.scan_iter("situation:*")))
        
        # Check index status
        single_agent_index = True
        multi_entity_index = True
        
        try:
            redis_client.client.execute_command('FT.INFO', 'engram_vector_idx')
        except:
            single_agent_index = False
            
        try:
            redis_client.client.execute_command('FT.INFO', 'engram_vector_idx_multi')
        except:
            multi_entity_index = False
        
        return {
            "status": "healthy",
            "memory_counts": {
                "total_memories": memory_keys,
                "entity_access_keys": entity_access_keys,
                "situation_keys": situation_keys
            },
            "indexes": {
                "single_agent": "exists" if single_agent_index else "missing",
                "multi_entity": "exists" if multi_entity_index else "missing"
            },
            "redis_connection": "connected"
        }
        
    except Exception as e:
        logger.error(f"Admin status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )