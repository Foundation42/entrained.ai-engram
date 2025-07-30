"""
Memory Curation Models for AI-powered memory analysis and categorization
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, computed_field
from enum import Enum


class StorageType(str, Enum):
    """Categories for memory storage"""
    FACTS = "facts"                    # Permanent factual information
    PREFERENCES = "preferences"        # User preferences and patterns
    CONTEXT = "context"               # Conversation and project context
    TEMPORARY = "temporary"           # Short-term contextual information
    SKILLS = "skills"                 # User capabilities and expertise
    RELATIONSHIPS = "relationships"   # Social connections and dynamics


class RetentionPolicy(str, Enum):
    """Memory retention policies"""
    PERMANENT = "permanent"           # Keep indefinitely
    LONG_TERM = "long_term"          # Keep for 1 year
    MEDIUM_TERM = "medium_term"      # Keep for 30 days
    SHORT_TERM = "short_term"        # Keep for 7 days
    SESSION_ONLY = "session_only"    # Keep only for current session


class PrivacySensitivity(str, Enum):
    """Privacy sensitivity levels"""
    PUBLIC = "public"                 # Can be shared broadly
    PERSONAL = "personal"            # Personal but not sensitive
    PRIVATE = "private"              # Sensitive personal information
    CONFIDENTIAL = "confidential"    # Highly sensitive, strict access


class CurationPreferences(BaseModel):
    """Agent-specific curation preferences"""
    priority_topics: List[str] = Field(default_factory=list, description="Topics this agent cares most about")
    retention_bias: Literal["conservative", "balanced", "aggressive"] = "balanced"
    privacy_sensitivity: PrivacySensitivity = PrivacySensitivity.PERSONAL
    agent_personality: str = Field(default="general_assistant", description="Agent personality type")
    custom_filters: Dict[str, Any] = Field(default_factory=dict, description="Custom filtering rules")
    context_window_priority: List[str] = Field(default_factory=list, description="What context is most important")


class MemoryObservation(BaseModel):
    """A single memory observation - like a Columbo note"""
    memory_type: StorageType = Field(description="Type of information observed")
    content: str = Field(description="The specific information observed")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence this information is accurate")
    ephemerality_score: float = Field(ge=0.0, le=1.0, description="How quickly this becomes outdated (0=permanent, 1=expires immediately)")
    privacy_sensitivity: PrivacySensitivity = Field(description="Privacy level of this information")
    contextual_value: float = Field(ge=0.0, le=1.0, description="How useful for future conversations")
    tags: List[str] = Field(default_factory=list, description="Semantic tags for this observation")
    reasoning: str = Field(description="Why this observation was noted")
    
    @computed_field
    @property
    def should_store(self) -> bool:
        """Business logic: should this observation be stored?"""
        # Don't store if highly ephemeral (weather, mood, etc.)
        if self.ephemerality_score > 0.8:
            return False
        
        # Don't store if very low confidence
        if self.confidence_score < 0.3:
            return False
            
        # Don't store if no contextual value
        if self.contextual_value < 0.2:
            return False
            
        return True
    
    @property 
    def retention_policy(self) -> RetentionPolicy:
        """Business logic: how long should this be stored?"""
        if self.ephemerality_score > 0.6:
            return RetentionPolicy.SHORT_TERM
        elif self.ephemerality_score > 0.3:
            return RetentionPolicy.MEDIUM_TERM
        elif self.memory_type in [StorageType.FACTS, StorageType.SKILLS]:
            return RetentionPolicy.LONG_TERM
        else:
            return RetentionPolicy.MEDIUM_TERM


class MemoryDecision(BaseModel):
    """Decision about whether and how to store memories from a conversation turn"""
    observations: List[MemoryObservation] = Field(default_factory=list, description="All observations made by the LLM")
    overall_reasoning: str = Field(description="Overall analysis of the conversation turn")
    consolidation_candidates: List[str] = Field(default_factory=list, description="Memory IDs that could be merged")
    
    @computed_field
    @property
    def should_store(self) -> bool:
        """Whether any observations should be stored (derived from business logic)"""
        return any(obs.should_store for obs in self.observations)
    
    @property
    def storage_worthy_observations(self) -> List[MemoryObservation]:
        """Only the observations that pass our business logic filters"""
        return [obs for obs in self.observations if obs.should_store]
    
    # Legacy fields for backward compatibility
    storage_type: StorageType = Field(default=StorageType.CONTEXT, description="Primary storage type (legacy)")
    key_information: List[str] = Field(default_factory=list, description="Key facts extracted (legacy)")
    retention_policy: RetentionPolicy = Field(default=RetentionPolicy.MEDIUM_TERM, description="Primary retention policy (legacy)")
    privacy_sensitivity: PrivacySensitivity = Field(default=PrivacySensitivity.PERSONAL, description="Primary privacy level (legacy)")
    confidence_score: float = Field(default=0.5, description="Overall confidence score (legacy)")
    reasoning: str = Field(default="", description="Overall reasoning (legacy)")
    tags: List[str] = Field(default_factory=list, description="Overall tags (legacy)")
    consolidation_candidate: bool = Field(default=False, description="Legacy consolidation flag")


class MemoryCurationRequest(BaseModel):
    """Request for memory curation analysis"""
    user_input: str = Field(description="User's input in the conversation")
    agent_response: str = Field(description="Agent's response")
    conversation_context: Optional[str] = Field(None, description="Broader conversation context")
    existing_memory_count: int = Field(default=0, description="Number of existing memories for this user")
    curation_preferences: Optional[CurationPreferences] = Field(None, description="Agent-specific preferences")
    session_metadata: Dict[str, Any] = Field(default_factory=dict, description="Session-specific information")


class MemoryCleanupAction(BaseModel):
    """Action to take during memory cleanup"""
    action_type: Literal["delete", "archive", "consolidate", "update_retention", "merge"] = Field(description="Type of cleanup action")
    memory_ids: List[str] = Field(description="Memory IDs affected by this action")
    reasoning: str = Field(description="Why this action is needed")
    new_content: Optional[str] = Field(None, description="New consolidated content if merging")
    priority: Literal["low", "medium", "high", "critical"] = Field(default="medium", description="Urgency of cleanup")


class RetrievalIntent(BaseModel):
    """Analysis of what type of memories are needed for a query"""
    intent_type: Literal["facts", "preferences", "context", "skills", "relationships", "mixed"] = Field(description="Primary intent")
    storage_types_needed: List[StorageType] = Field(description="Types of memories to retrieve")
    temporal_focus: Literal["recent", "all_time", "specific_period"] = Field(description="Time focus for retrieval")
    confidence_threshold: float = Field(ge=0.0, le=1.0, description="Minimum confidence for relevant memories")
    max_results: int = Field(default=10, description="Maximum number of memories to return")
    reasoning: str = Field(description="Analysis of the query intent")


class CuratedMemoryMetadata(BaseModel):
    """Enhanced metadata for curated memories"""
    storage_type: StorageType
    retention_policy: RetentionPolicy
    privacy_sensitivity: PrivacySensitivity
    confidence_score: float
    tags: List[str]
    key_information: List[str]
    curation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    curation_version: str = Field(default="1.0", description="Version of curation algorithm used")
    agent_preferences_used: Optional[Dict[str, Any]] = Field(None, description="Preferences that influenced curation")
    expires_at: Optional[datetime] = Field(None, description="When this memory should be cleaned up")
    last_accessed: Optional[datetime] = Field(None, description="Last time this memory was retrieved")
    access_count: int = Field(default=0, description="Number of times this memory has been accessed")
    consolidation_group: Optional[str] = Field(None, description="Group ID for related memories")


class MemoryCurationStats(BaseModel):
    """Statistics about memory curation performance"""
    total_interactions_analyzed: int = 0
    memories_stored: int = 0
    memories_rejected: int = 0
    storage_type_breakdown: Dict[StorageType, int] = Field(default_factory=dict)
    retention_policy_breakdown: Dict[RetentionPolicy, int] = Field(default_factory=dict)
    average_confidence_score: float = 0.0
    cleanup_actions_taken: int = 0
    agent_satisfaction_scores: Dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


def get_retention_expiry(policy: RetentionPolicy, created_at: datetime = None) -> Optional[datetime]:
    """Calculate expiry date based on retention policy"""
    if created_at is None:
        created_at = datetime.utcnow()
    
    if policy == RetentionPolicy.PERMANENT:
        return None
    elif policy == RetentionPolicy.LONG_TERM:
        return created_at + timedelta(days=365)
    elif policy == RetentionPolicy.MEDIUM_TERM:
        return created_at + timedelta(days=30)
    elif policy == RetentionPolicy.SHORT_TERM:
        return created_at + timedelta(days=7)
    elif policy == RetentionPolicy.SESSION_ONLY:
        return created_at + timedelta(hours=4)  # Assume 4-hour sessions
    else:
        return created_at + timedelta(days=30)  # Default fallback