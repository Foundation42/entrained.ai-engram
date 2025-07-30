"""
AI-Powered Memory Curation Service

This service analyzes conversation turns and makes intelligent decisions about
what information should be stored, how it should be categorized, and how long
it should be retained.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from openai import OpenAI

from models.memory_curation import (
    MemoryDecision, MemoryCurationRequest, CurationPreferences,
    StorageType, RetentionPolicy, PrivacySensitivity,
    MemoryCleanupAction, RetrievalIntent, CuratedMemoryMetadata
)
from core.config import settings

logger = logging.getLogger(__name__)


class MemoryCurator:
    """AI-powered memory curation system"""
    
    def __init__(self, openai_api_key: str = None):
        # Get OpenAI API key from settings, environment, or parameter
        api_key = openai_api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No OpenAI API key provided - memory curation will use fallback decisions")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        
        self.model_name = settings.openai_curation_model
        self.curation_version = "1.0"
        
    async def analyze_memory_worthiness(self, request: MemoryCurationRequest) -> MemoryDecision:
        """Analyze whether a conversation turn should be stored as memory"""
        try:
            # Build the analysis prompt based on agent preferences
            prompt = self._build_curation_prompt(request)
            
            # Get LLM analysis
            response = await self._call_openai(prompt)
            
            if not response:
                # Fallback: conservative storage decision
                return self._fallback_decision(request)
            
            # Parse and validate the response
            decision = self._parse_curation_response(response, request)
            
            logger.info(f"Memory curation decision: store={decision.should_store}, type={decision.storage_type}")
            return decision
            
        except Exception as e:
            logger.error(f"Error in memory curation analysis: {e}")
            return self._fallback_decision(request)
    
    def _build_curation_prompt(self, request: MemoryCurationRequest) -> str:
        """Build the LLM prompt for memory curation"""
        
        # Agent preferences context
        prefs_context = ""
        if request.curation_preferences:
            prefs = request.curation_preferences
            prefs_context = f"""
Agent Preferences:
- Priority topics: {', '.join(prefs.priority_topics)}
- Retention bias: {prefs.retention_bias}
- Privacy sensitivity: {prefs.privacy_sensitivity}
- Agent personality: {prefs.agent_personality}
"""
        
        # Context about existing memories
        memory_context = ""
        if request.existing_memory_count > 0:
            memory_context = f"Note: User already has {request.existing_memory_count} stored memories."
        
        return f"""You are an AI memory curation specialist. Analyze this conversation turn and decide what to remember.

{prefs_context}

Conversation Turn:
User: {request.user_input}
Assistant: {request.agent_response}

{memory_context}

Context: {request.conversation_context or "No additional context"}

Your job is to be like Detective Columbo - observe and note EVERYTHING, no matter how small or seemingly unimportant. Extract every piece of information that could potentially be remembered, and score each observation.

For each piece of information, analyze:

1. **What exactly was observed** (be specific and precise)
2. **Type of information** (facts, preferences, context, temporary, skills, relationships)
3. **Confidence in accuracy** (how sure are you this information is correct?)
4. **Ephemerality score** (how quickly will this become outdated? 0.0=permanent, 1.0=expires immediately)
5. **Privacy sensitivity** (how sensitive is this information?)
6. **Contextual value** (how useful for future conversations?)

Like Columbo, note EVERYTHING - even seemingly mundane details might be important later. Don't filter or decide what to keep - just observe and score.

Storage Types:
- facts: Permanent factual information (name, location, job, family)
- preferences: User preferences and patterns (likes, dislikes, working style)
- context: Project/conversation context (current work, goals, recent topics)
- temporary: Short-term information (today's weather, current mood)
- skills: User capabilities and expertise (programming languages, professional skills)
- relationships: Social connections and dynamics (team members, family, friends)

Retention Policies:
- permanent: Keep indefinitely (core facts)
- long_term: Keep 1 year (important context)
- medium_term: Keep 30 days (project context)
- short_term: Keep 7 days (temporary context)
- session_only: Keep 4 hours (very temporary)

Privacy Levels:
- public: Can be shared broadly
- personal: Personal but not sensitive
- private: Sensitive personal information
- confidential: Highly sensitive

Like Columbo making detailed notes, observe and record EVERYTHING you notice.

Respond with valid JSON only:
{{
    "observations": [
        {{
            "memory_type": "facts|preferences|context|temporary|skills|relationships",
            "content": "Christian lives in Liversedge, West Yorkshire",
            "confidence_score": 0.95,
            "ephemerality_score": 0.0,
            "privacy_sensitivity": "personal",
            "contextual_value": 0.9,
            "tags": ["location", "personal_info"],
            "reasoning": "User stated their location clearly"
        }},
        {{
            "memory_type": "temporary",
            "content": "It's raining today",
            "confidence_score": 1.0,
            "ephemerality_score": 0.95,
            "privacy_sensitivity": "public",
            "contextual_value": 0.1,
            "tags": ["weather", "casual"],
            "reasoning": "Weather observation - highly ephemeral but clearly stated"
        }}
    ],
    "overall_reasoning": "Observed both lasting facts and ephemeral details",
    "consolidation_candidates": []
}}"""

    async def _call_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI for LLM analysis"""
        if not self.client:
            logger.warning("OpenAI client not initialized - using fallback decision")
            return None
            
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI memory curation specialist. Always respond with valid JSON only, no additional text."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent decisions
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI JSON response: {e}")
                logger.error(f"Raw response: {response_text}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}")
            return None
    
    def _parse_curation_response(self, response: Dict[str, Any], request: MemoryCurationRequest) -> MemoryDecision:
        """Parse and validate the LLM curation response - Columbo observation format"""
        try:
            from models.memory_curation import MemoryObservation
            
            # Parse observations 
            observations = []
            raw_observations = response.get("observations", [])
            
            for obs_data in raw_observations:
                try:
                    observation = MemoryObservation(
                        memory_type=StorageType(obs_data.get("memory_type", "context")),
                        content=obs_data.get("content", ""),
                        confidence_score=max(0.0, min(1.0, obs_data.get("confidence_score", 0.5))),
                        ephemerality_score=max(0.0, min(1.0, obs_data.get("ephemerality_score", 0.5))),
                        privacy_sensitivity=PrivacySensitivity(obs_data.get("privacy_sensitivity", "personal")),
                        contextual_value=max(0.0, min(1.0, obs_data.get("contextual_value", 0.5))),
                        tags=obs_data.get("tags", []),
                        reasoning=obs_data.get("reasoning", "Observed information")
                    )
                    observations.append(observation)
                except Exception as e:
                    logger.warning(f"Skipping invalid observation: {e}")
                    continue
            
            # Create decision object
            decision = MemoryDecision(
                observations=observations,
                overall_reasoning=response.get("overall_reasoning", "Columbo-style observation analysis"),
                consolidation_candidates=response.get("consolidation_candidates", [])
            )
            
            # Apply business logic to get storage-worthy observations
            storage_worthy = decision.storage_worthy_observations
            
            # Create legacy fields from storage-worthy observations for backward compatibility
            if storage_worthy:
                first_worthy = storage_worthy[0]
                storage_type = first_worthy.memory_type
                retention_policy = first_worthy.retention_policy
                privacy_sensitivity = first_worthy.privacy_sensitivity
                confidence_score = sum(obs.confidence_score for obs in storage_worthy) / len(storage_worthy)
                key_information = [obs.content for obs in storage_worthy]
                tags = list(set(tag for obs in storage_worthy for tag in obs.tags))
            else:
                # Fallback for no storage-worthy observations
                storage_type = StorageType.TEMPORARY
                retention_policy = RetentionPolicy.SESSION_ONLY
                privacy_sensitivity = PrivacySensitivity.PUBLIC
                confidence_score = 0.1
                key_information = []
                tags = []
            
            # Add legacy fields
            decision.storage_type = storage_type
            decision.key_information = key_information
            decision.retention_policy = retention_policy
            decision.privacy_sensitivity = privacy_sensitivity
            decision.confidence_score = confidence_score
            decision.reasoning = decision.overall_reasoning
            decision.tags = tags
            decision.consolidation_candidate = len(decision.consolidation_candidates) > 0
            
            return decision
            
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing curation response: {e}")
            logger.error(f"Raw response: {response}")
            return self._fallback_decision(request)
    
    def _fallback_decision(self, request: MemoryCurationRequest) -> MemoryDecision:
        """Fallback decision when LLM analysis fails"""
        # Conservative approach: store as temporary context with medium retention
        return MemoryDecision(
            should_store=True,  # Better to store and clean up later than lose important info
            storage_type=StorageType.CONTEXT,
            key_information=[],
            retention_policy=RetentionPolicy.MEDIUM_TERM,
            privacy_sensitivity=PrivacySensitivity.PERSONAL,
            confidence_score=0.3,
            reasoning="Fallback decision due to analysis failure - conservative storage",
            tags=["fallback", "needs_review"],
            consolidation_candidate=False,
            requires_review=True
        )
    
    async def analyze_retrieval_intent(self, query: str, context: str = "") -> RetrievalIntent:
        """Analyze what type of memories should be retrieved for a query"""
        
        prompt = f"""Analyze this query to determine what type of memories should be retrieved.

Query: {query}
Context: {context}

Determine:
1. What is the user really asking for?
2. What types of stored information would be most helpful?
3. Should we focus on recent memories or all-time?
4. How confident should we be in relevance matching?

Intent Types:
- facts: User wants factual information about themselves or others
- preferences: User wants to know about preferences or patterns  
- context: User wants to continue previous conversations/projects
- skills: User wants to know about capabilities or expertise
- relationships: User wants to know about people and connections
- mixed: Query needs multiple types of information

Storage Types to Search:
- facts, preferences, context, temporary, skills, relationships

Temporal Focus:
- recent: Focus on last 7 days
- all_time: Search all memories
- specific_period: Focus on particular time range

Respond with valid JSON:
{{
    "intent_type": "facts|preferences|context|skills|relationships|mixed",
    "storage_types_needed": ["facts", "preferences"],
    "temporal_focus": "recent|all_time|specific_period", 
    "confidence_threshold": 0.0-1.0,
    "max_results": 5-20,
    "reasoning": "explanation of analysis"
}}"""

        try:
            response = await self._call_openai(prompt)
            
            if response:
                return RetrievalIntent(
                    intent_type=response.get("intent_type", "mixed"),
                    storage_types_needed=[StorageType(t) for t in response.get("storage_types_needed", ["context"])],
                    temporal_focus=response.get("temporal_focus", "all_time"),
                    confidence_threshold=max(0.0, min(1.0, response.get("confidence_threshold", 0.7))),
                    max_results=max(1, min(50, response.get("max_results", 10))),
                    reasoning=response.get("reasoning", "Automated intent analysis")
                )
            else:
                # Fallback: search everything with medium confidence
                return RetrievalIntent(
                    intent_type="mixed",
                    storage_types_needed=[StorageType.FACTS, StorageType.CONTEXT, StorageType.PREFERENCES],
                    temporal_focus="all_time",
                    confidence_threshold=0.6,
                    max_results=10,
                    reasoning="Fallback analysis - search multiple types"
                )
                
        except Exception as e:
            logger.error(f"Error in retrieval intent analysis: {e}")
            return RetrievalIntent(
                intent_type="mixed",
                storage_types_needed=[StorageType.CONTEXT],
                temporal_focus="all_time", 
                confidence_threshold=0.5,
                max_results=10,
                reasoning=f"Error fallback: {str(e)}"
            )
    
    async def suggest_cleanup_actions(self, memories: List[Dict[str, Any]]) -> List[MemoryCleanupAction]:
        """Analyze memories and suggest cleanup actions"""
        
        if not memories:
            return []
        
        # Group memories by type and analyze for cleanup opportunities
        cleanup_actions = []
        
        # Find expired memories
        now = datetime.utcnow()
        for memory in memories:
            metadata = memory.get('metadata', {})
            expires_at = metadata.get('expires_at')
            
            if expires_at and datetime.fromisoformat(expires_at.replace('Z', '+00:00')) < now:
                cleanup_actions.append(MemoryCleanupAction(
                    action_type="delete",
                    memory_ids=[memory.get('memory_id')],
                    reasoning="Memory has expired based on retention policy",
                    priority="medium"
                ))
        
        # Find potential duplicates/consolidation candidates
        fact_memories = [m for m in memories if m.get('metadata', {}).get('storage_type') == 'facts']
        
        if len(fact_memories) > 5:
            # Suggest consolidation if many fact memories exist
            cleanup_actions.append(MemoryCleanupAction(
                action_type="consolidate",
                memory_ids=[m.get('memory_id') for m in fact_memories],
                reasoning="Multiple fact memories could be consolidated for efficiency",
                priority="low"
            ))
        
        return cleanup_actions


# Global memory curator instance  
def get_memory_curator():
    """Get a memory curator instance with fresh configuration"""
    return MemoryCurator()

memory_curator = get_memory_curator()