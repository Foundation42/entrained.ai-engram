from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
import logging

from models.memory import (
    MemoryCreateRequest,
    MemoryCreateResponse,
    Memory,
    Annotation
)
from models.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    MemorySearchResult
)
from core.redis_client_hash import redis_client
from core.config import settings
from services.embedding import embedding_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/store", response_model=MemoryCreateResponse)
async def store_memory(request: MemoryCreateRequest):
    """Store a new memory in the system"""
    try:
        # Create memory object
        memory = Memory(
            content=request.content,
            primary_vector=request.primary_vector,
            metadata=request.metadata,
            tags=request.tags,
            causality=request.causality,
            retention=request.retention
        )
        
        # Convert to dict for storage
        memory_dict = memory.model_dump(mode="json")
        
        # Store in Redis
        success = redis_client.store_memory(memory.id, memory_dict)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store memory"
            )
        
        return MemoryCreateResponse(
            memory_id=memory.id,
            status="stored",
            timestamp=memory.created_at,
            vector_dimensions=len(request.primary_vector)
        )
        
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_memories(request: RetrievalRequest):
    """Retrieve memories based on semantic similarity"""
    try:
        start_time = datetime.utcnow()
        
        # Debug logging
        logger.info(f"Retrieval request received")
        logger.info(f"Request type: {type(request)}")
        logger.info(f"Request filters object: {request.filters}")
        logger.info(f"Request filters type: {type(request.filters)}")
        
        if request.filters:
            logger.info(f"Filters is truthy")
            logger.info(f"Filter model dump: {request.filters.model_dump()}")
            logger.info(f"Filter dict: {request.filters.__dict__ if hasattr(request.filters, '__dict__') else 'No __dict__'}")
            
            # Log each filter field
            for field_name in ['agent_ids', 'session_ids', 'memory_types', 'domains']:
                field_value = getattr(request.filters, field_name, 'ATTR_NOT_FOUND')
                logger.info(f"  {field_name}: {field_value} (type: {type(field_value)})")
        
        # Combine resonance vectors if multiple provided
        if len(request.resonance_vectors) == 1:
            query_vector = request.resonance_vectors[0].vector
        else:
            # Combine vectors with weights
            vectors = [rv.vector for rv in request.resonance_vectors]
            weights = [rv.weight for rv in request.resonance_vectors]
            query_vector = embedding_service.combine_vectors(vectors, weights)
        
        # Prepare filters
        filters = {}
        if request.filters:
            # Use getattr with default None to handle all cases
            agent_ids = getattr(request.filters, 'agent_ids', None)
            if agent_ids is not None:
                filters["agent_ids"] = agent_ids
                
            memory_types = getattr(request.filters, 'memory_types', None)
            if memory_types is not None:
                filters["memory_types"] = memory_types
                
            session_ids = getattr(request.filters, 'session_ids', None)
            if session_ids is not None:
                filters["session_ids"] = session_ids
                
            domains = getattr(request.filters, 'domains', None)
            if domains is not None:
                filters["domains"] = domains
                
            thread_ids = getattr(request.filters, 'thread_ids', None)
            if thread_ids is not None:
                filters["thread_ids"] = thread_ids
                
            participants = getattr(request.filters, 'participants', None)
            if participants is not None:
                filters["participants"] = participants
                
            confidence_threshold = getattr(request.filters, 'confidence_threshold', None)
            if confidence_threshold is not None:
                filters["confidence_threshold"] = confidence_threshold
                
            timestamp_range = getattr(request.filters, 'timestamp_range', None)
            if timestamp_range is not None:
                filters["timestamp_range"] = {
                    "after": timestamp_range.after if timestamp_range.after else None,
                    "before": timestamp_range.before if timestamp_range.before else None
                }
        
        # Prepare tags
        include_tags = request.tags.include if request.tags else []
        
        # Debug log filters before search
        logger.info(f"Filters being passed to search: {filters}")
        logger.info(f"Filter keys: {list(filters.keys()) if filters else 'None'}")
        
        # Search memories (always pass filters dict, even if empty)
        results = redis_client.search_memories(
            query_vector=query_vector,
            top_k=request.retrieval.top_k,
            filters=filters,  # Pass empty dict instead of None
            tags=include_tags if include_tags else None
        )
        
        # Filter by similarity threshold
        filtered_results = [
            r for r in results 
            if r["similarity_score"] >= request.retrieval.similarity_threshold
        ]
        
        # Convert to response format
        memories = []
        for result in filtered_results[:request.retrieval.top_k]:
            memories.append(MemorySearchResult(
                memory_id=result["memory_id"],
                similarity_score=result["similarity_score"],
                content_preview=result["content_preview"],
                metadata=result["metadata"],
                tags=result["tags"],
                media_count=0,  # TODO: Calculate from actual data
                annotation_count=len(redis_client.get_annotations(result["memory_id"]))
            ))
        
        # Calculate search time
        search_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return RetrievalResponse(
            memories=memories,
            total_found=len(filtered_results),
            search_time_ms=search_time_ms,
            query_vector_dims=len(query_vector)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/memory/{memory_id}")
async def get_memory_detail(memory_id: str):
    """Get detailed information about a specific memory"""
    try:
        memory = redis_client.get_memory(memory_id)
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id} not found"
            )
        
        return memory
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/memory/{memory_id}/annotate")
async def add_annotation(memory_id: str, annotation: Annotation):
    """Add an annotation to a memory"""
    try:
        # Check if memory exists
        memory = redis_client.get_memory(memory_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id} not found"
            )
        
        # Add annotation
        annotation_dict = annotation.model_dump(mode="json")
        success = redis_client.add_annotation(memory_id, annotation_dict)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add annotation"
            )
        
        return {"status": "success", "message": "Annotation added"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding annotation to {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/memory/{memory_id}/annotations")
async def get_annotations(memory_id: str):
    """Get all annotations for a memory"""
    try:
        # Check if memory exists
        memory = redis_client.get_memory(memory_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id} not found"
            )
        
        annotations = redis_client.get_annotations(memory_id)
        return {"memory_id": memory_id, "annotations": annotations}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting annotations for {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )