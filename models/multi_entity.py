"""
Multi-Entity Memory Models for Engram

These models support shared experiences between multiple entities (humans and AIs),
with witness-based access control and natural privacy boundaries.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class SpeakerContent(BaseModel):
    """Individual speaker's contribution in a memory"""
    entity_id: str
    content: str
    timestamp: Optional[datetime] = None
    
    
class MemoryContentMultiEntity(BaseModel):
    """Content structure for multi-entity memories"""
    text: str  # Full conversation/experience text
    speakers: Dict[str, str] = {}  # entity_id -> their contribution
    summary: Optional[str] = None  # Brief summary of the interaction
    media: List[Any] = []  # Shared media in the experience
    

class SituationInfo(BaseModel):
    """Information about the situation/context where memory was created"""
    situation_id: str = Field(default_factory=lambda: f"sit-{uuid4().hex[:12]}")
    situation_type: str  # e.g., "1:1_conversation", "group_discussion", "public_presentation"
    duration_minutes: Optional[float] = None
    location: Optional[str] = None  # virtual or physical location
    context: Optional[str] = None  # e.g., "research_collaboration", "casual_chat"
    

class AccessControl(BaseModel):
    """Access control settings for a memory"""
    witnessed_by: List[str]  # Entity IDs who can access this memory
    privacy_level: str = "participants_only"  # participants_only, group, public
    excluded_entities: List[str] = []  # Explicit exclusions (for privacy)
    share_permissions: Dict[str, List[str]] = {}  # entity_id -> allowed actions
    

class MultiEntityMetadata(BaseModel):
    """Metadata for multi-entity memories"""
    timestamp: datetime
    situation_duration_minutes: Optional[float] = None
    interaction_quality: Optional[float] = None  # 0-1 quality score
    topic_tags: List[str] = []
    situation_context: Optional[str] = None
    entity_roles: Dict[str, str] = {}  # entity_id -> role in situation
    
    class Config:
        extra = "allow"  # Allow custom fields like article_id, comment_type, etc.
    

class MultiEntityMemory(BaseModel):
    """Complete multi-entity memory structure"""
    id: str = Field(default_factory=lambda: f"mem-{uuid4().hex[:12]}")
    witnessed_by: List[str]  # Primary witness list
    situation: SituationInfo
    content: MemoryContentMultiEntity
    primary_vector: List[float]
    metadata: MultiEntityMetadata
    access_control: AccessControl
    causality: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }


class MultiEntityMemoryCreateRequest(BaseModel):
    """Request to create a new multi-entity memory"""
    witnessed_by: List[str]
    situation_id: Optional[str] = None
    situation_type: str
    content: MemoryContentMultiEntity
    primary_vector: List[float]
    metadata: Dict[str, Any]  # Will be validated into MultiEntityMetadata
    causality: Optional[Dict[str, Any]] = None
    access_control: Optional[Dict[str, Any]] = None  # Will be validated into AccessControl


class EntityFilter(BaseModel):
    """Filters for entity-based memory retrieval"""
    witnessed_by_includes: Optional[List[str]] = None  # Must include these entities
    co_participants: Optional[List[str]] = None  # Memories with specific others
    exclude_private_to: Optional[List[str]] = None  # Exclude memories private to others
    entity_roles: Optional[Dict[str, str]] = None  # Filter by entity roles
    

class SituationFilter(BaseModel):
    """Filters for situation-based memory retrieval"""
    situation_types: Optional[List[str]] = None
    topic_tags: Optional[List[str]] = None
    time_range: Optional[Dict[str, datetime]] = None
    min_duration_minutes: Optional[float] = None
    max_duration_minutes: Optional[float] = None
    contexts: Optional[List[str]] = None
    

class MultiEntityRetrievalRequest(BaseModel):
    """Request for retrieving memories with entity-based access control"""
    requesting_entity: str  # Who is requesting
    resonance_vectors: List[Dict[str, Any]]
    entity_filters: Optional[EntityFilter] = None
    situation_filters: Optional[SituationFilter] = None
    retrieval_options: Dict[str, Any] = {
        "top_k": 10,
        "similarity_threshold": 0.7,
        "include_speakers_breakdown": True,
        "prioritize_recent": 0.0
    }


class MultiEntityMemorySearchResult(BaseModel):
    """Search result with access control information"""
    memory_id: str
    similarity_score: float
    access_granted: bool
    access_reason: str  # e.g., "witnessed_by_includes_requesting_entity"
    situation_summary: str
    co_participants: List[str]
    content_preview: str
    speakers_involved: List[str]
    metadata: Dict[str, Any]
    

class MultiEntityRetrievalResponse(BaseModel):
    """Response from multi-entity memory retrieval"""
    memories: List[MultiEntityMemorySearchResult]
    access_denied_count: int = 0
    total_found: int
    search_time_ms: int
    entity_verification: Dict[str, Any] = {}  # Entity verification details