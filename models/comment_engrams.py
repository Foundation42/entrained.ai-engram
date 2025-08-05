"""
Comment-as-Engrams Data Models

Extends the existing multi-entity memory system to support web comments,
forum discussions, and editorial intelligence.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from uuid import uuid4

from models.multi_entity import (
    MultiEntityMemoryCreateRequest, 
    MultiEntityRetrievalRequest,
    EntityFilter,
    SituationFilter
)


# Comment-specific content types
CommentType = Literal["root_comment", "reply", "agent_response", "editorial_note"]
ArticleSection = Literal["main", "introduction", "conclusion", "sidebar", "footnote"]


class CommentContent(BaseModel):
    """Enhanced content model for comments"""
    text: str
    content_type: CommentType = "root_comment"
    article_id: str  # Which article this comment is on
    article_section: Optional[ArticleSection] = "main"  # Which part of article
    quoted_text: Optional[str] = None  # Text being quoted/referenced
    speakers: Dict[str, str] = {}  # entity_id -> their comment text
    summary: Optional[str] = None
    
    
class CommentMetadata(BaseModel):
    """Comment-specific metadata"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resonance_score: Optional[float] = None  # 0-1 engagement/quality score
    topic_tags: List[str] = []  # ["speculation", "technical", "question"]
    comment_type: CommentType = "root_comment"
    
    # Thread relationships
    reply_to_comment: Optional[str] = None  # Parent comment memory_id
    reply_chain_depth: int = 0  # How deep in thread (0 = root)
    thread_id: Optional[str] = None  # Groups related comments
    
    # Editorial tracking
    handled_by_agent: Optional[str] = None  # Which agent responded
    sparked_article: Optional[str] = None  # If led to new content
    editorial_priority: Optional[str] = None  # "high", "medium", "low"
    
    # Engagement metrics
    interaction_quality: float = 0.5  # Default neutral quality
    semantic_novelty: Optional[float] = None  # How unique vs existing comments
    

class CommentSituation(BaseModel):
    """Situation context for comments"""
    article_id: str
    article_title: str
    article_section: ArticleSection = "main"
    discussion_phase: str = "active"  # "active", "archived", "moderated"
    

class CommentAccessControl(BaseModel):
    """Access control for comments"""
    privacy_level: str = "public"  # "public", "members_only", "private"
    witnessed_by: List[str]  # Who can see this comment
    moderation_status: str = "approved"  # "pending", "approved", "hidden"
    share_permissions: Dict[str, List[str]] = {"public": ["read"]}


class CommentEngramRequest(BaseModel):
    """Simplified request for storing comments as Engrams"""
    # Core comment data
    author_id: str  # The commenting user/agent
    article_id: str
    comment_text: str
    
    # Optional thread context
    reply_to_comment: Optional[str] = None  # Parent comment memory_id
    quoted_text: Optional[str] = None
    
    # Comment-specific metadata
    comment_type: CommentType = "root_comment"
    article_section: ArticleSection = "main"
    resonance_score: Optional[float] = None
    topic_tags: List[str] = []
    
    # Situation context
    situation_type: str = "public_discussion"
    
    
class ThreadReconstructionRequest(BaseModel):
    """Request to reconstruct comment threads"""
    article_id: str
    thread_strategy: str = "hybrid"  # "hierarchical", "semantic", "hybrid"
    max_depth: int = 10
    include_agent_responses: bool = True
    semantic_clustering: bool = True
    
    
class CommentThread(BaseModel):
    """Reconstructed comment thread"""
    thread_id: str
    root_comment_id: str
    total_comments: int
    max_depth: int
    semantic_clusters: List[List[str]] = []  # Groups of related comment IDs
    
    
class ThreadComment(BaseModel):
    """Comment within a thread structure"""
    memory_id: str
    author_id: str
    author_name: Optional[str] = None
    comment_text: str
    timestamp: datetime
    
    # Thread position
    depth: int = 0
    parent_id: Optional[str] = None
    children: List[str] = []  # Child comment IDs
    
    # Semantic info
    resonance_score: Optional[float] = None
    topic_tags: List[str] = []
    semantic_cluster: Optional[int] = None
    
    # Agent interaction
    handled_by_agent: Optional[str] = None
    agent_response_id: Optional[str] = None
    

class EditorialIntelligenceRequest(BaseModel):
    """Request for editorial intelligence queries"""
    query_type: str  # "unanswered_gems", "trending_topics", "agent_opportunities"
    article_id: Optional[str] = None
    time_range: Optional[Dict[str, datetime]] = None
    resonance_threshold: float = 0.7
    limit: int = 20
    

class EditorialInsight(BaseModel):
    """Editorial intelligence result"""
    insight_type: str
    title: str
    description: str
    comments: List[ThreadComment]
    action_suggestions: List[str] = []
    priority_score: float = 0.5


# Specialized retrieval requests
class CommentRetrievalRequest(MultiEntityRetrievalRequest):
    """Enhanced retrieval for comments"""
    article_id: Optional[str] = None
    comment_types: Optional[List[CommentType]] = None
    include_thread_context: bool = True
    semantic_expansion: bool = True  # Find semantically related comments
    

class SemanticThreadRequest(BaseModel):
    """Request for semantic thread clustering"""
    article_id: str
    similarity_threshold: float = 0.8
    min_cluster_size: int = 2
    max_clusters: int = 10
    include_cross_article: bool = False  # Find related comments from other articles