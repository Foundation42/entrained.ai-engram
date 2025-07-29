from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ResonanceVector(BaseModel):
    vector: List[float]
    weight: float = 1.0
    label: Optional[str] = None
    description: Optional[str] = None


class TagFilter(BaseModel):
    include: List[str] = []
    exclude: List[str] = []


class TimestampRange(BaseModel):
    after: Optional[datetime] = None
    before: Optional[datetime] = None


class RetrievalFilters(BaseModel):
    timestamp_range: Optional[TimestampRange] = None
    memory_types: Optional[List[str]] = None
    agent_ids: Optional[List[str]] = None
    confidence_threshold: Optional[float] = None
    domains: Optional[List[str]] = None


class RetrievalConfig(BaseModel):
    top_k: int = 10
    similarity_threshold: float = 0.75
    diversity_lambda: float = 0.5
    boost_recent: float = 0.0


class OrderingCriteria(BaseModel):
    field: str
    direction: str = "desc"
    weight: float = 1.0


class RetrievalRequest(BaseModel):
    resonance_vectors: List[ResonanceVector]
    tags: Optional[TagFilter] = None
    filters: Optional[RetrievalFilters] = None
    retrieval: RetrievalConfig = RetrievalConfig()
    ordering: Optional[List[OrderingCriteria]] = None


class MemorySearchResult(BaseModel):
    memory_id: str
    similarity_score: float
    content_preview: str
    metadata: Dict[str, Any]
    tags: List[str]
    media_count: int = 0
    annotation_count: int = 0


class RetrievalResponse(BaseModel):
    memories: List[MemorySearchResult]
    total_found: int
    search_time_ms: int
    query_vector_dims: int