from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class MediaItem(BaseModel):
    type: str
    url: str
    embedding: Optional[List[float]] = None
    description: Optional[str] = None
    mime_type: Optional[str] = None
    title: Optional[str] = None
    preview_text: Optional[str] = None
    domain: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None


class MemoryContent(BaseModel):
    text: str
    media: List[MediaItem] = []


class MemoryMetadata(BaseModel):
    timestamp: datetime
    agent_id: str
    memory_type: str
    session_id: Optional[str] = None  # For session isolation
    participants: Optional[List[str]] = None
    thread_id: Optional[str] = None
    domain: Optional[str] = None
    confidence: Optional[float] = None
    # Additional metadata fields that can be filtered
    custom_metadata: Optional[Dict[str, Any]] = None


class CausalityInfo(BaseModel):
    parent_memories: List[str] = []
    influence_strength: List[float] = []
    synthesis_type: Optional[str] = None
    reasoning: Optional[str] = None


class RetentionInfo(BaseModel):
    ttl: Optional[int] = None
    importance: float = 0.5
    decay_function: str = "logarithmic"


class MemoryCreateRequest(BaseModel):
    content: MemoryContent
    primary_vector: List[float]
    metadata: MemoryMetadata
    tags: List[str] = []
    causality: Optional[CausalityInfo] = None
    retention: Optional[RetentionInfo] = None


class MemoryCreateResponse(BaseModel):
    memory_id: str
    status: str
    timestamp: datetime
    vector_dimensions: int


class Memory(BaseModel):
    id: str = Field(default_factory=lambda: f"mem-{uuid4().hex[:12]}")
    content: MemoryContent
    primary_vector: List[float]
    metadata: MemoryMetadata
    tags: List[str] = []
    causality: Optional[CausalityInfo] = None
    retention: Optional[RetentionInfo] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    storage_backend: str = "redis"
    compression: Optional[str] = None


class AnnotationType(BaseModel):
    type: str
    content: str
    vector: Optional[List[float]] = None
    confidence: Optional[float] = None
    tags: List[str] = []
    evidence_links: List[str] = []


class Annotation(BaseModel):
    annotator_id: str
    annotation: AnnotationType
    created_at: datetime = Field(default_factory=datetime.utcnow)