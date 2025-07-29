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
            if request.filters.agent_ids:
                filters["agent_ids"] = request.filters.agent_ids
            if request.filters.memory_types:
                filters["memory_types"] = request.filters.memory_types
        
        # Prepare tags
        include_tags = request.tags.include if request.tags else []
        
        # Search memories
        results = redis_client.search_memories(
            query_vector=query_vector,
            top_k=request.retrieval.top_k,
            filters=filters if filters else None,
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