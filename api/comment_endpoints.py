"""
Comment-as-Engrams API Endpoints

Provides web comment functionality using the Engram memory system,
enabling semantic threading, agent participation, and editorial intelligence.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
import logging
from uuid import uuid4

from models.comment_engrams import (
    CommentEngramRequest, CommentContent, CommentMetadata, CommentAccessControl,
    ThreadReconstructionRequest, CommentThread, ThreadComment,
    EditorialIntelligenceRequest, EditorialInsight,
    CommentRetrievalRequest, SemanticThreadRequest
)
from models.multi_entity import (
    MultiEntityMemoryCreateRequest, MemoryContentMultiEntity, 
    SituationInfo, AccessControl, MultiEntityMetadata
)
from core.redis_client_multi_entity import redis_multi_entity_client
from services.embedding import embedding_service
from services.memory_curator import memory_curator
from core.security import content_validator
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/store", response_model=Dict[str, Any])
async def store_comment(request: CommentEngramRequest, background_tasks: BackgroundTasks):
    """Store a comment as an Engram memory"""
    try:
        # Validate and sanitize request content
        request_dict = request.dict()
        validated_data = content_validator.validate_comment_request(request_dict)
        
        # Update request with validated data
        request.comment_text = validated_data["comment_text"]
        request.author_id = validated_data["author_id"]
        request.article_id = validated_data["article_id"]
        
        logger.info(f"Storing comment from {request.author_id} on article {request.article_id}")
        
        # Build the witnessed_by list
        witnessed_by = [request.author_id, "public"]
        if "agent-claude-prime" not in witnessed_by:
            witnessed_by.append("agent-claude-prime")  # Agents can see public comments
            
        # Create comment content structure
        content = MemoryContentMultiEntity(
            text=f"User: {request.comment_text}",
            speakers={request.author_id: request.comment_text},
            summary=f"Comment by {request.author_id} on {request.article_id}",
            media=[]
        )
        
        # Create situation info
        situation = SituationInfo(
            situation_id=f"article-{request.article_id}-comments",
            situation_type=request.situation_type,
            location=f"article:{request.article_id}",
            context=f"Comment thread on {request.article_id}"
        )
        
        # Enhanced metadata with comment-specific fields
        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "comment_type": request.comment_type,
            "article_id": request.article_id,
            "article_section": request.article_section,
            "reply_to_comment": request.reply_to_comment,
            "quoted_text": request.quoted_text,
            "resonance_score": request.resonance_score or 0.5,
            "topic_tags": request.topic_tags,
            "interaction_quality": 0.8,  # Default for user comments
            "reply_chain_depth": await _calculate_reply_depth(request.reply_to_comment),
            "thread_id": await _get_or_create_thread_id(request.reply_to_comment, request.article_id),
            "semantic_novelty": None,  # Will be calculated in background
            "handled_by_agent": None,
            "sparked_article": None,
            "editorial_priority": None
        }
        
        # Access control
        access_control = AccessControl(
            witnessed_by=witnessed_by,
            privacy_level="public",
            excluded_entities=[],
            share_permissions={"public": ["read"]}
        )
        
        # Generate embedding for the comment
        try:
            primary_vector = await embedding_service.generate_embedding(request.comment_text)
            if not primary_vector:
                logger.warning("Embedding service returned None, using default vector")
                primary_vector = [0.1] * settings.vector_dimensions
        except Exception as e:
            logger.error(f"Embedding service error: {e}, using default vector")
            primary_vector = [0.1] * settings.vector_dimensions
        
        # Create the Engram memory request
        engram_request = MultiEntityMemoryCreateRequest(
            witnessed_by=witnessed_by,
            situation_id=situation.situation_id,
            situation_type=situation.situation_type,
            content=content,
            primary_vector=primary_vector,
            metadata=metadata,
            access_control=access_control.__dict__,
            causality={
                "parent_comment": request.reply_to_comment,
                "article_context": request.article_id,
                "interaction_type": "user_comment"
            } if request.reply_to_comment else None
        )
        
        # Store using existing Engram infrastructure
        from api.multi_entity_endpoints import store_multi_entity_memory
        result = await store_multi_entity_memory(engram_request)
        
        # Background tasks
        background_tasks.add_task(_calculate_semantic_novelty, result["memory_id"], request.comment_text)
        background_tasks.add_task(_check_agent_response_opportunity, result["memory_id"], request)
        
        # Enhance response with comment-specific info
        result.update({
            "comment_type": request.comment_type,
            "article_id": request.article_id,
            "thread_id": metadata["thread_id"],
            "reply_depth": metadata["reply_chain_depth"]
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error storing comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/article/{article_id}/thread", response_model=List[ThreadComment])
async def get_article_thread(
    article_id: str,
    include_agents: bool = True,
    max_depth: int = 10,
    sort_by: str = "timestamp"  # "timestamp", "resonance", "semantic"
):
    """Get all comments for an article as a threaded structure"""
    try:
        logger.info(f"Retrieving comment thread for article {article_id}")
        
        # Search for all comments - use same approach as semantic search
        entity_filters = {"witnessed_by_includes": ["public"]}
        situation_filters = {"situation_types": ["public_discussion"]}
        
        try:
            logger.info("Starting memory search for thread reconstruction...")
            comments_search = redis_multi_entity_client.search_memories(
                requesting_entity="public",
                query_vector=[0.1] * settings.vector_dimensions,
                top_k=1000,  # Get all comments
                entity_filters=entity_filters,
                situation_filters=situation_filters
            )
            
            logger.info(f"Search completed successfully")
            logger.info(f"Found {len(comments_search)} total memories in search")
            logger.info(f"Search results type: {type(comments_search)}")
            logger.info(f"Search results sample: {comments_search[:1] if comments_search else 'EMPTY'}")
            
        except Exception as search_error:
            logger.error(f"Search failed with error: {search_error}")
            logger.error(f"Error type: {type(search_error)}")
            comments_search = []
        
        # Filter to only this article's comments using metadata
        article_comments = []
        for result in comments_search:
            metadata = result.get('metadata', {})
            result_article_id = metadata.get('article_id')
            memory_id = result.get('memory_id', 'unknown')
            
            # Log more details for debugging
            logger.info(f"Checking memory {memory_id}")
            logger.info(f"  Article ID in metadata: {result_article_id}")
            logger.info(f"  Looking for article ID: {article_id}")
            logger.info(f"  Metadata keys: {list(metadata.keys())}")
            
            if result_article_id == article_id:
                article_comments.append(result)
                logger.info(f"  ✅ MATCH - Added to results")
            else:
                logger.info(f"  ❌ NO MATCH - Skipped")
        
        logger.info(f"Found {len(article_comments)} comments for article {article_id}")
        
        # Convert to ThreadComment objects and build hierarchy
        thread_comments = []
        comment_map = {}  # memory_id -> ThreadComment
        
        for comment_data in article_comments:
            metadata = comment_data.get('metadata', {})
            content = comment_data.get('content', {})
            
            # Extract author and comment text from search result format
            # Search results have 'speakers_involved' and 'content_preview' at top level
            speakers_involved = comment_data.get('speakers_involved', [])
            content_preview = comment_data.get('content_preview', '')
            
            if speakers_involved:
                author_id = speakers_involved[0]  # First speaker is the author
            else:
                author_id = "unknown"
            
            # Extract comment text from content_preview (format: "User: actual comment text")
            if content_preview.startswith('User: '):
                comment_text = content_preview[6:]  # Remove "User: " prefix
            else:
                comment_text = content_preview or ""
            
            thread_comment = ThreadComment(
                memory_id=comment_data['memory_id'],
                author_id=author_id,
                comment_text=comment_text,
                timestamp=datetime.fromisoformat(metadata.get('timestamp', datetime.utcnow().isoformat())),
                depth=metadata.get('reply_chain_depth', 0),
                parent_id=metadata.get('reply_to_comment'),
                resonance_score=metadata.get('resonance_score', 0.5),
                topic_tags=metadata.get('topic_tags', []),
                handled_by_agent=metadata.get('handled_by_agent')
            )
            
            comment_map[thread_comment.memory_id] = thread_comment
            thread_comments.append(thread_comment)
        
        # Build parent-child relationships
        for comment in thread_comments:
            if comment.parent_id and comment.parent_id in comment_map:
                parent = comment_map[comment.parent_id]
                parent.children.append(comment.memory_id)
        
        # Sort based on preference
        if sort_by == "resonance":
            thread_comments.sort(key=lambda c: c.resonance_score or 0, reverse=True)
        elif sort_by == "semantic":
            # TODO: Implement semantic clustering sort
            thread_comments.sort(key=lambda c: c.timestamp)
        else:  # timestamp
            thread_comments.sort(key=lambda c: c.timestamp)
        
        logger.info(f"Retrieved {len(thread_comments)} comments for article {article_id}")
        return thread_comments
        
    except Exception as e:
        logger.error(f"Error retrieving article thread: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/editorial/insights", response_model=List[EditorialInsight])
async def get_editorial_insights(request: EditorialIntelligenceRequest):
    """Get editorial intelligence insights about comments"""
    try:
        logger.info(f"Generating editorial insights: {request.query_type}")
        
        insights = []
        
        if request.query_type == "unanswered_gems":
            insights.extend(await _find_unanswered_gems(request))
        elif request.query_type == "trending_topics":
            insights.extend(await _find_trending_topics(request))
        elif request.query_type == "agent_opportunities":
            insights.extend(await _find_agent_opportunities(request))
        else:
            # Run all insight types
            insights.extend(await _find_unanswered_gems(request))
            insights.extend(await _find_trending_topics(request))
            insights.extend(await _find_agent_opportunities(request))
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating editorial insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/semantic/similar", response_model=List[ThreadComment])
async def find_similar_comments(
    comment_text: str,
    article_id: Optional[str] = None,
    similarity_threshold: float = 0.8,
    limit: int = 10,
    cross_article: bool = True
):
    """Find comments semantically similar to given text"""
    try:
        logger.info(f"Finding similar comments to: {comment_text[:50]}...")
        
        # Generate embedding for the query text
        query_vector = await embedding_service.generate_embedding(comment_text)
        if not query_vector:
            logger.warning("Could not generate embedding for query, using default")
            query_vector = [0.1] * settings.vector_dimensions
        
        # Build filters
        entity_filters = {"witnessed_by_includes": ["public"]}
        situation_filters = {"situation_types": ["public_discussion"]}
        
        if article_id and not cross_article:
            situation_filters["contexts"] = [f"Comment thread on {article_id}"]
        
        # Search for similar comments
        similar_results = redis_multi_entity_client.search_memories(
            requesting_entity="public",
            query_vector=query_vector,
            top_k=limit * 2,  # Get more to filter later
            entity_filters=entity_filters,
            situation_filters=situation_filters
        )
        
        # Filter by similarity threshold and convert to ThreadComment
        similar_comments = []
        for result in similar_results:
            if result.get('similarity_score', 0) >= similarity_threshold:
                metadata = result.get('metadata', {})
                content = result.get('content', {})
                
                # Extract author and comment text properly
                speakers = content.get('speakers', {})
                if speakers:
                    author_id = list(speakers.keys())[0]
                    comment_text = speakers[author_id]
                else:
                    author_id = "unknown"
                    # Fallback to extracting from text field (format: "User: comment")
                    text = content.get('text', '')
                    if text.startswith('User: '):
                        comment_text = text[6:]  # Remove "User: " prefix
                    else:
                        comment_text = text
                
                thread_comment = ThreadComment(
                    memory_id=result['memory_id'],
                    author_id=author_id,
                    comment_text=comment_text,
                    timestamp=datetime.fromisoformat(metadata.get('timestamp', datetime.utcnow().isoformat())),
                    resonance_score=metadata.get('resonance_score', 0.5),
                    topic_tags=metadata.get('topic_tags', [])
                )
                similar_comments.append(thread_comment)
        
        return similar_comments[:limit]
        
    except Exception as e:
        logger.error(f"Error finding similar comments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Helper functions
async def _calculate_reply_depth(parent_comment_id: Optional[str]) -> int:
    """Calculate how deep in a reply chain this comment is"""
    if not parent_comment_id:
        return 0
    
    try:
        parent_data = redis_multi_entity_client.get_memory(parent_comment_id, "public")
        if parent_data and parent_data.get('metadata'):
            return parent_data['metadata'].get('reply_chain_depth', 0) + 1
    except:
        pass
    
    return 1  # Default if parent not found


async def _get_or_create_thread_id(parent_comment_id: Optional[str], article_id: str) -> str:
    """Get thread ID from parent comment or create new one"""
    if not parent_comment_id:
        return f"thread-{article_id}-{uuid4().hex[:8]}"
    
    try:
        parent_data = redis_multi_entity_client.get_memory(parent_comment_id, "public")
        if parent_data and parent_data.get('metadata'):
            return parent_data['metadata'].get('thread_id', f"thread-{article_id}-{uuid4().hex[:8]}")
    except:
        pass
    
    return f"thread-{article_id}-{uuid4().hex[:8]}"


async def _calculate_semantic_novelty(memory_id: str, comment_text: str):
    """Background task to calculate how novel this comment is"""
    try:
        # This would compare against existing comments to measure uniqueness
        # For now, just log that we would do this
        logger.info(f"Calculating semantic novelty for comment {memory_id}")
    except Exception as e:
        logger.error(f"Error calculating semantic novelty: {e}")


async def _check_agent_response_opportunity(memory_id: str, request: CommentEngramRequest):
    """Background task to check if this comment should trigger an agent response"""
    try:
        # Check if comment has questions, high resonance, or specific topics
        if request.resonance_score and request.resonance_score > 0.8:
            logger.info(f"High resonance comment {memory_id} - potential agent opportunity")
        
        # Check for question words
        if any(word in request.comment_text.lower() for word in ["?", "how", "why", "what", "when", "where"]):
            logger.info(f"Question detected in comment {memory_id} - potential agent opportunity")
            
    except Exception as e:
        logger.error(f"Error checking agent opportunity: {e}")


async def _find_unanswered_gems(request: EditorialIntelligenceRequest) -> List[EditorialInsight]:
    """Find high-resonance comments without agent responses"""
    # Implementation would search for comments with high resonance but no agent responses
    return [EditorialInsight(
        insight_type="unanswered_gems",
        title="High-Value Unanswered Comments",
        description="Comments with high engagement that haven't received responses",
        comments=[],
        action_suggestions=["Consider agent response", "Feature in newsletter"],
        priority_score=0.8
    )]


async def _find_trending_topics(request: EditorialIntelligenceRequest) -> List[EditorialInsight]:
    """Find trending discussion topics"""
    return [EditorialInsight(
        insight_type="trending_topics", 
        title="Trending Discussion Topics",
        description="Topics generating significant discussion",
        comments=[],
        action_suggestions=["Write follow-up article", "Create topic cluster"],
        priority_score=0.7
    )]


async def _find_agent_opportunities(request: EditorialIntelligenceRequest) -> List[EditorialInsight]:
    """Find opportunities for agent engagement"""
    return [EditorialInsight(
        insight_type="agent_opportunities",
        title="Agent Engagement Opportunities", 
        description="Comments that would benefit from agent responses",
        comments=[],
        action_suggestions=["Deploy agent response", "Add to agent context"],
        priority_score=0.6
    )]