"""
Curated Memory API Endpoints

Enhanced memory storage and retrieval with AI-powered curation
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
import logging

from models.memory_curation import (
    MemoryCurationRequest, MemoryDecision, CurationPreferences,
    CuratedMemoryMetadata, RetrievalIntent, MemoryCleanupAction,
    StorageType, get_retention_expiry
)
from models.multi_entity import (
    MultiEntityMemory, MultiEntityMemoryCreateRequest,
    MultiEntityRetrievalRequest, MultiEntityRetrievalResponse
)
from services.memory_curator import memory_curator
from core.redis_client_multi_entity import redis_multi_entity_client
from services.embedding import embedding_service

logger = logging.getLogger(__name__)
router = APIRouter()


class CuratedMemoryCreateRequest(MultiEntityMemoryCreateRequest):
    """Enhanced memory creation request with curation preferences"""
    user_input: Optional[str] = None  # Original user input
    agent_response: Optional[str] = None  # Agent's response
    conversation_context: Optional[str] = None  # Broader context
    curation_preferences: Optional[CurationPreferences] = None  # Agent preferences
    force_storage: bool = False  # Bypass curation analysis
    

@router.post("/curated/analyze", response_model=MemoryDecision)
async def analyze_memory_worthiness(request: MemoryCurationRequest):
    """Analyze whether a conversation should be stored as memory"""
    try:
        logger.info(f"Analyzing memory worthiness for conversation turn")
        
        # Perform AI-powered curation analysis
        decision = await memory_curator.analyze_memory_worthiness(request)
        
        logger.info(f"Curation decision: store={decision.should_store}, confidence={decision.confidence_score}")
        return decision
        
    except Exception as e:
        logger.error(f"Error in memory analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory analysis failed: {str(e)}"
        )


@router.post("/curated/store", response_model=Dict[str, Any])
async def store_curated_memory(request: CuratedMemoryCreateRequest, background_tasks: BackgroundTasks):
    """Store memory with AI-powered curation"""
    try:
        logger.info(f"Storing curated memory for {len(request.witnessed_by)} entities")
        
        # Skip curation if forced or if we don't have conversation data
        if request.force_storage or not (request.user_input and request.agent_response):
            logger.info("Skipping curation analysis - storing directly")
            decision = MemoryDecision(
                should_store=True,
                storage_type=StorageType.CONTEXT,
                key_information=[],
                retention_policy="medium_term",
                privacy_sensitivity="personal",
                confidence_score=1.0,
                reasoning="Direct storage requested"
            )
        else:
            # Perform curation analysis
            curation_request = MemoryCurationRequest(
                user_input=request.user_input,
                agent_response=request.agent_response,
                conversation_context=request.conversation_context,
                existing_memory_count=await _get_user_memory_count(request.witnessed_by[0] if request.witnessed_by else "unknown"),
                curation_preferences=request.curation_preferences
            )
            
            decision = await memory_curator.analyze_memory_worthiness(curation_request)
            logger.info(f"Curation decision: {decision.should_store} (confidence: {decision.confidence_score})")
        
        # Don't store if curation says no
        if not decision.should_store:
            return {
                "memory_id": None,
                "status": "rejected_by_curation",
                "reasoning": decision.reasoning,
                "confidence_score": decision.confidence_score
            }
        
        # Enhance memory metadata with curation info
        enhanced_metadata = request.metadata.copy() if request.metadata else {}
        
        # Extract enum values safely
        storage_type_value = decision.storage_type.value if hasattr(decision.storage_type, 'value') else str(decision.storage_type)
        retention_policy_value = decision.retention_policy.value if hasattr(decision.retention_policy, 'value') else str(decision.retention_policy)
        privacy_sensitivity_value = decision.privacy_sensitivity.value if hasattr(decision.privacy_sensitivity, 'value') else str(decision.privacy_sensitivity)
        
        # Calculate expiry safely
        expiry_date = get_retention_expiry(retention_policy_value)
        expires_at = expiry_date.isoformat() if expiry_date else None
        
        enhanced_metadata.update({
            "storage_type": storage_type_value,
            "retention_policy": retention_policy_value,
            "privacy_sensitivity": privacy_sensitivity_value,
            "confidence_score": decision.confidence_score,
            "tags": decision.tags,
            "key_information": decision.key_information,
            "curation_timestamp": datetime.utcnow().isoformat(),
            "curation_version": "1.0",
            "expires_at": expires_at,
            "access_count": 0,
            "consolidation_group": None
        })
        
        # Store with enhanced metadata
        enhanced_request = MultiEntityMemoryCreateRequest(
            witnessed_by=request.witnessed_by,
            situation_id=request.situation_id,
            situation_type=request.situation_type,
            content=request.content,
            primary_vector=request.primary_vector,
            metadata=enhanced_metadata,
            access_control=request.access_control,
            causality=request.causality
        )
        
        # Use existing multi-entity storage
        from api.multi_entity_endpoints import store_multi_entity_memory
        result = await store_multi_entity_memory(enhanced_request)
        
        # Add curation info to response
        result.update({
            "curation_decision": {
                "storage_type": storage_type_value,
                "retention_policy": retention_policy_value,
                "confidence_score": decision.confidence_score,
                "key_information": decision.key_information,
                "reasoning": decision.reasoning
            }
        })
        
        # Schedule cleanup check in background
        if retention_policy_value != "permanent":
            background_tasks.add_task(_schedule_cleanup_check, result["memory_id"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing curated memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/curated/retrieve", response_model=MultiEntityRetrievalResponse)
async def retrieve_curated_memories(request: MultiEntityRetrievalRequest):
    """Retrieve memories with AI-powered intent analysis"""
    try:
        logger.info(f"Curated retrieval request from {request.requesting_entity}")
        
        # Analyze retrieval intent if we have query text
        query_text = getattr(request, 'query_text', None)
        conversation_context = getattr(request, 'conversation_context', '')
        
        if query_text:
            intent = await memory_curator.analyze_retrieval_intent(query_text, conversation_context)
            logger.info(f"Retrieval intent: {intent.intent_type}, types: {intent.storage_types_needed}")
            
            # Adjust retrieval options based on intent
            if isinstance(request.retrieval_options, dict):
                request.retrieval_options['similarity_threshold'] = intent.confidence_threshold
                request.retrieval_options['top_k'] = min(intent.max_results, request.retrieval_options.get('top_k', 10))
            else:
                request.retrieval_options = {
                    'similarity_threshold': intent.confidence_threshold,
                    'top_k': intent.max_results,
                    'exclude_denials': True
                }
        
        # Use existing multi-entity retrieval
        from api.multi_entity_endpoints import retrieve_multi_entity_memories
        response = await retrieve_multi_entity_memories(request)
        
        # Update access counts for retrieved memories
        for memory in response.memories:
            await _increment_access_count(memory.memory_id)
        
        # Add intent analysis to response if available
        if 'intent' in locals():
            response.retrieval_analysis = {
                "intent_type": intent.intent_type,
                "storage_types_searched": [t.value for t in intent.storage_types_needed],
                "confidence_threshold_used": intent.confidence_threshold,
                "reasoning": intent.reasoning
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in curated retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/curated/cleanup/analyze")
async def analyze_cleanup_opportunities(entity_id: str, limit: int = 100):
    """Analyze memories and suggest cleanup actions"""
    try:
        logger.info(f"Analyzing cleanup opportunities for {entity_id}")
        
        # Get entity's memories
        memory_ids = redis_multi_entity_client.client.smembers(f"entity_access:{entity_id}")
        memories = []
        
        for memory_id in list(memory_ids)[:limit]:
            memory_data = redis_multi_entity_client.get_memory(memory_id.decode(), entity_id)
            if memory_data:
                memories.append(memory_data)
        
        # Get cleanup suggestions
        cleanup_actions = await memory_curator.suggest_cleanup_actions(memories)
        
        return {
            "entity_id": entity_id,
            "memories_analyzed": len(memories),
            "cleanup_actions": [action.dict() for action in cleanup_actions],
            "summary": {
                "total_actions": len(cleanup_actions),
                "high_priority": len([a for a in cleanup_actions if a.priority == "high"]),
                "consolidation_candidates": len([a for a in cleanup_actions if a.action_type == "consolidate"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing cleanup opportunities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/curated/cleanup/execute")
async def execute_cleanup_action(action: MemoryCleanupAction, requesting_entity: str):
    """Execute a memory cleanup action"""
    try:
        logger.info(f"Executing cleanup action: {action.action_type} for {len(action.memory_ids)} memories")
        
        executed_count = 0
        
        if action.action_type == "delete":
            for memory_id in action.memory_ids:
                if redis_multi_entity_client.delete_memory(memory_id, requesting_entity):
                    executed_count += 1
        
        elif action.action_type == "archive":
            # Move to archive (implement archive storage)
            for memory_id in action.memory_ids:
                # For now, just mark as archived
                memory_data = redis_multi_entity_client.get_memory(memory_id, requesting_entity)
                if memory_data:
                    memory_data['metadata']['archived'] = True
                    memory_data['metadata']['archived_at'] = datetime.utcnow().isoformat()
                    redis_multi_entity_client.store_memory(memory_id, memory_data)
                    executed_count += 1
        
        elif action.action_type == "consolidate":
            # Consolidate multiple memories into one
            if action.new_content and len(action.memory_ids) > 1:
                # Get first memory as base
                base_memory = redis_multi_entity_client.get_memory(action.memory_ids[0], requesting_entity)
                if base_memory:
                    # Update content with consolidated version
                    base_memory['content']['text'] = action.new_content
                    base_memory['metadata']['consolidated_from'] = action.memory_ids[1:]
                    base_memory['metadata']['consolidated_at'] = datetime.utcnow().isoformat()
                    
                    # Store updated memory
                    redis_multi_entity_client.store_memory(action.memory_ids[0], base_memory)
                    
                    # Delete the other memories
                    for memory_id in action.memory_ids[1:]:
                        redis_multi_entity_client.delete_memory(memory_id, requesting_entity)
                    
                    executed_count = len(action.memory_ids)
        
        return {
            "action_type": action.action_type,
            "memories_affected": len(action.memory_ids),
            "successfully_executed": executed_count,
            "status": "completed" if executed_count > 0 else "failed",
            "reasoning": action.reasoning
        }
        
    except Exception as e:
        logger.error(f"Error executing cleanup action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/curated/stats/{entity_id}")
async def get_curation_stats(entity_id: str):
    """Get memory curation statistics for an entity"""
    try:
        # Get entity's memories
        memory_ids = redis_multi_entity_client.client.smembers(f"entity_access:{entity_id}")
        memories = []
        
        for memory_id in list(memory_ids):
            memory_data = redis_multi_entity_client.get_memory(memory_id.decode(), entity_id)
            if memory_data:
                memories.append(memory_data)
        
        # Analyze statistics
        total_memories = len(memories)
        storage_type_counts = {}
        retention_policy_counts = {}
        total_confidence = 0
        access_counts = []
        
        for memory in memories:
            metadata = memory.get('metadata', {})
            storage_type = metadata.get('storage_type', 'unknown')
            retention_policy = metadata.get('retention_policy', 'unknown')
            confidence = metadata.get('confidence_score', 0)
            access_count = metadata.get('access_count', 0)
            
            storage_type_counts[storage_type] = storage_type_counts.get(storage_type, 0) + 1
            retention_policy_counts[retention_policy] = retention_policy_counts.get(retention_policy, 0) + 1
            total_confidence += confidence
            access_counts.append(access_count)
        
        return {
            "entity_id": entity_id,
            "total_memories": total_memories,
            "storage_type_breakdown": storage_type_counts,
            "retention_policy_breakdown": retention_policy_counts,
            "average_confidence_score": total_confidence / max(1, total_memories),
            "average_access_count": sum(access_counts) / max(1, len(access_counts)),
            "most_accessed_memories": max(access_counts) if access_counts else 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting curation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Helper functions

async def _get_user_memory_count(entity_id: str) -> int:
    """Get count of existing memories for an entity"""
    try:
        memory_ids = redis_multi_entity_client.client.smembers(f"entity_access:{entity_id}")
        return len(memory_ids)
    except:
        return 0


async def _increment_access_count(memory_id: str):
    """Increment access count for a memory"""
    try:
        # Get the raw memory data
        raw_data = redis_multi_entity_client.client.hgetall(f"memory:{memory_id}")
        if raw_data:
            # Update access count
            current_count = int(raw_data.get(b'access_count', b'0').decode())
            redis_multi_entity_client.client.hset(f"memory:{memory_id}", "access_count", str(current_count + 1))
            redis_multi_entity_client.client.hset(f"memory:{memory_id}", "last_accessed", datetime.utcnow().isoformat())
    except Exception as e:
        logger.debug(f"Failed to increment access count for {memory_id}: {e}")


async def _schedule_cleanup_check(memory_id: str):
    """Schedule a cleanup check for a memory (background task)"""
    try:
        # This could be enhanced to use a proper task queue like Celery
        logger.info(f"Scheduled cleanup check for memory {memory_id}")
        # For now, just log the scheduling
    except Exception as e:
        logger.error(f"Error scheduling cleanup check: {e}")


# Enhanced retrieval request with query text
class CuratedRetrievalRequest(MultiEntityRetrievalRequest):
    """Enhanced retrieval request with query analysis"""
    query_text: Optional[str] = None  # The actual user query for intent analysis
    conversation_context: Optional[str] = None  # Broader conversation context