"""
Multi-Entity API endpoints for Engram

Handles storage and retrieval of shared experiences between multiple entities
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
import logging

from models.multi_entity import (
    MultiEntityMemory,
    MultiEntityMemoryCreateRequest,
    MultiEntityRetrievalRequest,
    MultiEntityRetrievalResponse,
    MultiEntityMemorySearchResult,
    AccessControl,
    SituationInfo,
    MemoryContentMultiEntity,
    MultiEntityMetadata
)
from core.redis_client_multi_entity import redis_multi_entity_client
from services.embedding import embedding_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/multi/store", response_model=Dict[str, Any])
async def store_multi_entity_memory(request: MultiEntityMemoryCreateRequest):
    """Store a new multi-entity memory with witness-based access control"""
    try:
        logger.info(f"Storing multi-entity memory witnessed by {len(request.witnessed_by)} entities")
        
        # Validate witnessed_by list
        if not request.witnessed_by:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Memory must have at least one witness"
            )
        
        # Create situation info with validation
        try:
            situation = SituationInfo(
                situation_id=request.situation_id or f"sit-{datetime.utcnow().timestamp()}",
                situation_type=request.situation_type
            )
        except Exception as e:
            logger.error(f"Error creating situation: {e}")
            logger.error(f"Request situation_type: {request.situation_type}, type: {type(request.situation_type)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid situation data: {str(e)}"
            )
        
        # Create access control
        privacy_level = 'participants_only'
        if request.access_control and isinstance(request.access_control, dict):
            privacy_level = request.access_control.get('privacy_level', 'participants_only')
        
        access_control = AccessControl(
            witnessed_by=request.witnessed_by,
            privacy_level=privacy_level
        )
        
        # Create metadata with validation
        try:
            metadata = MultiEntityMetadata(**request.metadata)
        except Exception as e:
            logger.error(f"Error creating metadata: {e}")
            # Create with required fields only
            metadata = MultiEntityMetadata(
                timestamp=request.metadata.get('timestamp', datetime.utcnow()),
                situation_duration_minutes=request.metadata.get('situation_duration_minutes'),
                interaction_quality=request.metadata.get('interaction_quality'),
                topic_tags=request.metadata.get('topic_tags', [])
            )
        
        # Create memory object
        memory = MultiEntityMemory(
            witnessed_by=request.witnessed_by,
            situation=situation,
            content=request.content,
            primary_vector=request.primary_vector,
            metadata=metadata,
            access_control=access_control,
            causality=request.causality
        )
        
        # Convert to dict for storage
        memory_dict = memory.dict()
        
        # Store in Redis
        success = redis_multi_entity_client.store_memory(memory.id, memory_dict)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store multi-entity memory"
            )
        
        return {
            "memory_id": memory.id,
            "status": "stored",
            "witnessed_by": request.witnessed_by,
            "situation_id": situation.situation_id,
            "timestamp": memory.created_at,
            "access_control": {
                "privacy_level": access_control.privacy_level,
                "witness_count": len(request.witnessed_by)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing multi-entity memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/multi/retrieve", response_model=MultiEntityRetrievalResponse)
async def retrieve_multi_entity_memories(request: MultiEntityRetrievalRequest):
    """Retrieve memories with entity-based access control"""
    try:
        start_time = datetime.utcnow()
        
        logger.info(f"Multi-entity retrieval request from {request.requesting_entity}")
        
        # Validate requesting entity
        if not request.requesting_entity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="requesting_entity is required"
            )
        
        # Combine resonance vectors if multiple provided
        if len(request.resonance_vectors) == 1:
            query_vector = request.resonance_vectors[0]['vector']
        else:
            # Combine vectors with weights
            vectors = [rv['vector'] for rv in request.resonance_vectors]
            weights = [rv.get('weight', 1.0) for rv in request.resonance_vectors]
            query_vector = embedding_service.combine_vectors(vectors, weights)
        
        # Prepare filters
        entity_filters = request.entity_filters.dict() if request.entity_filters else {}
        situation_filters = request.situation_filters.dict() if request.situation_filters else {}
        
        # Get retrieval options safely
        if isinstance(request.retrieval_options, dict):
            top_k = request.retrieval_options.get('top_k', 10)
            similarity_threshold = request.retrieval_options.get('similarity_threshold', 0.7)
        else:
            top_k = 10
            similarity_threshold = 0.7
        
        # Search memories with access control
        results = redis_multi_entity_client.search_memories(
            requesting_entity=request.requesting_entity,
            query_vector=query_vector,
            top_k=top_k,
            entity_filters=entity_filters,
            situation_filters=situation_filters
        )
        
        # Filter by similarity threshold
        filtered_results = [r for r in results if r['similarity_score'] >= similarity_threshold]
        
        # Apply denial content filtering if requested
        exclude_denials = request.retrieval_options.get('exclude_denials', True) if isinstance(request.retrieval_options, dict) else True
        
        if exclude_denials:
            denial_phrases = [
                "don't have access", "don't know", "sorry", "can't", "unable", 
                "i don't have", "i'm sorry", "i cannot", "no access to personal data",
                "don't remember", "can't remember", "no memory of", "not familiar with",
                "haven't mentioned", "you haven't", "didn't tell me", "haven't told me",
                "haven't shared", "not provided", "haven't provided", "no information about",
                "would need you to", "please tell me", "feel free to share", "happy to help",
                "don't recall", "can't recall", "no record of", "not aware of"
            ]
            
            non_denial_results = []
            for result in filtered_results:
                content = result.get('content_preview', '').lower()
                is_denial = any(phrase in content for phrase in denial_phrases)
                
                if not is_denial:
                    non_denial_results.append(result)
                else:
                    logger.debug(f"Filtered out denial memory: {result.get('memory_id', 'unknown')}")
            
            filtered_results = non_denial_results
        
        # Convert to response format
        memories = []
        access_denied_count = 0
        
        for result in filtered_results[:top_k]:
            if result['access_granted']:
                memories.append(MultiEntityMemorySearchResult(**result))
            else:
                access_denied_count += 1
        
        # Calculate search time
        search_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return MultiEntityRetrievalResponse(
            memories=memories,
            access_denied_count=access_denied_count,
            total_found=len(filtered_results),
            search_time_ms=search_time_ms,
            entity_verification={
                "requesting_entity": request.requesting_entity,
                "access_granted_count": len(memories),
                "search_scope": "witnessed_memories_only"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving multi-entity memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/multi/memory/{memory_id}")
async def get_multi_entity_memory(memory_id: str, requesting_entity: str):
    """Get a specific memory with access control check"""
    try:
        logger.info(f"Memory {memory_id} requested by {requesting_entity}")
        
        # Retrieve with access control
        memory = redis_multi_entity_client.get_memory(memory_id, requesting_entity)
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id} not found or access denied"
            )
        
        return {
            "memory": memory,
            "access_verification": {
                "requesting_entity": requesting_entity,
                "access_granted": True,
                "access_reason": "entity_is_witness"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/multi/situations/{entity_id}")
async def get_entity_situations(entity_id: str, limit: int = 50):
    """Get recent situations an entity has participated in"""
    try:
        # Get entity's accessible memories
        entity_key = f"entity_access:{entity_id}"
        memory_ids = redis_multi_entity_client.client.smembers(entity_key)
        
        situations = {}
        for memory_id in list(memory_ids)[:limit]:
            memory_data = redis_multi_entity_client.get_memory(memory_id.decode(), entity_id)
            if memory_data:
                situation = memory_data.get('situation', {})
                sit_id = situation.get('situation_id')
                if sit_id and sit_id not in situations:
                    situations[sit_id] = {
                        'situation_id': sit_id,
                        'situation_type': situation.get('situation_type'),
                        'participants': memory_data.get('witnessed_by', []),
                        'created_at': memory_data.get('created_at'),
                        'memory_count': 1
                    }
                elif sit_id:
                    situations[sit_id]['memory_count'] += 1
        
        return {
            "entity_id": entity_id,
            "situations": list(situations.values()),
            "total_situations": len(situations)
        }
        
    except Exception as e:
        logger.error(f"Error getting situations for {entity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/multi/migrate/legacy")
async def migrate_legacy_memory(memory_id: str):
    """Migrate a single-agent memory to multi-entity format"""
    try:
        # This would be implemented to convert old memories
        # For now, return a placeholder
        return {
            "status": "migration_not_implemented",
            "memory_id": memory_id,
            "message": "Legacy migration will be implemented in Phase 2"
        }
        
    except Exception as e:
        logger.error(f"Error migrating memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

