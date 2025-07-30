# 🧠 AI-Powered Memory Curation Guide for Agent Teams

## 🎯 Overview

Engram now features **AI-powered memory curation** using OpenAI's GPT-4.1-nano-2025-04-14 model that intelligently decides what to remember, how to categorize it, and when to clean it up. This transforms the basic "store everything" approach into a sophisticated memory management system.

## 🚀 Key Benefits

✅ **Quality over Quantity**: Only meaningful information gets stored  
✅ **Privacy by Design**: AI evaluates what's appropriate to remember  
✅ **Self-Maintaining**: Automatic cleanup of outdated/contradictory info  
✅ **Context-Aware**: Retrieval matches conversation intent  
✅ **Agent-Customizable**: Each agent can have unique curation preferences  
✅ **Performance**: Centralized processing with no agent-side latency  

---

## 📡 New API Endpoints

### 1. Curated Memory Storage
**POST** `/cam/curated/store`

Enhanced storage with AI-powered curation analysis:

```json
{
  "witnessed_by": ["human-christian-kind-hare"],
  "situation_id": "conversation-123",
  "situation_type": "casual_chat",
  "content": {
    "text": "I live in Liversedge and work on AI systems",
    "content_type": "factual_statement"
  },
  "primary_vector": [0.1, 0.2, ...],
  "user_input": "I live in Liversedge and work on AI systems",
  "agent_response": "Great! I'll remember that you live in Liversedge.",
  "conversation_context": "Getting to know user preferences",
  "curation_preferences": {
    "priority_topics": ["location", "profession", "technical_details"],
    "retention_bias": "balanced",
    "privacy_sensitivity": "personal",
    "agent_personality": "helpful_assistant"
  }
}
```

**Response includes curation decision:**
```json
{
  "memory_id": "mem_abc123",
  "status": "stored",
  "curation_decision": {
    "storage_type": "facts",
    "retention_policy": "permanent",
    "confidence_score": 0.92,
    "key_information": ["location: Liversedge", "profession: AI systems"],
    "reasoning": "High-value factual information about user"
  }
}
```

### 2. Intelligent Memory Retrieval
**POST** `/cam/curated/retrieve`

Context-aware retrieval with intent analysis:

```json
{
  "requesting_entity": "human-christian-kind-hare",
  "resonance_vectors": [{"vector": [...], "weight": 1.0}],
  "query_text": "Where do I live?",
  "conversation_context": "User asking about their location",
  "retrieval_options": {
    "top_k": 5,
    "similarity_threshold": 0.0,
    "exclude_denials": true
  }
}
```

**Response includes intent analysis:**
```json
{
  "memories": [...],
  "retrieval_analysis": {
    "intent_type": "facts",
    "storage_types_searched": ["facts", "context"],
    "confidence_threshold_used": 0.8,
    "reasoning": "User asking for factual location information"
  }
}
```

### 3. Memory Analysis (Optional)
**POST** `/cam/curated/analyze`

Analyze conversation turns without storing:

```json
{
  "user_input": "It's raining today",
  "agent_response": "That's unfortunate about the weather.",
  "conversation_context": "Casual weather comment",
  "curation_preferences": {...}
}
```

**Response:**
```json
{
  "should_store": false,
  "storage_type": "temporary",
  "retention_policy": "session_only",
  "confidence_score": 0.3,
  "reasoning": "Temporary weather information, low long-term value"
}
```

---

## 🏗️ Memory Categories

### 📊 Storage Types

| Type | Description | Examples | Retention |
|------|-------------|----------|-----------|
| **facts** | Permanent factual information | Name, location, job, family | Permanent |
| **preferences** | User preferences and patterns | Likes, dislikes, working style | Long-term |
| **context** | Project/conversation context | Current work, goals, topics | Medium-term |
| **temporary** | Short-term information | Weather, current mood | Short-term |
| **skills** | User capabilities | Programming languages, expertise | Long-term |
| **relationships** | Social connections | Team members, family, friends | Long-term |

### ⏰ Retention Policies

- **permanent**: Keep indefinitely (core facts)
- **long_term**: Keep 1 year (important context)  
- **medium_term**: Keep 30 days (project context)
- **short_term**: Keep 7 days (temporary context)
- **session_only**: Keep 4 hours (very temporary)

### 🔒 Privacy Levels

- **public**: Can be shared broadly
- **personal**: Personal but not sensitive  
- **private**: Sensitive personal information
- **confidential**: Highly sensitive, strict access

---

## 🎛️ Agent Preferences Configuration

Each agent can customize curation behavior:

```json
{
  "curation_preferences": {
    "priority_topics": ["technical_details", "programming", "AI"],
    "retention_bias": "conservative",  // "conservative" | "balanced" | "aggressive"
    "privacy_sensitivity": "personal",
    "agent_personality": "technical_specialist",
    "custom_filters": {
      "store_code_snippets": true,
      "ignore_weather": true
    },
    "context_window_priority": ["current_project", "user_goals"]
  }
}
```

### Agent Personality Types
- `general_assistant` - Balanced approach to all information
- `technical_specialist` - Prioritizes technical/code information  
- `personal_assistant` - Focuses on personal preferences and schedules
- `project_manager` - Emphasizes project context and deadlines
- `research_assistant` - Values facts, references, and research data

---

## 🔄 Migration from Existing System

### Option 1: Gradual Migration (Recommended)
```python
# Use curated endpoints for new memories
await store_curated_memory(enhanced_request)

# Keep using existing endpoints for simple cases
await store_multi_entity_memory(basic_request)
```

### Option 2: Hybrid Approach
```python
# Analyze first, then decide
decision = await analyze_memory_worthiness(curation_request)

if decision.should_store and decision.confidence_score > 0.7:
    await store_curated_memory(request)
else:
    # Skip storage or use basic storage
    pass
```

### Option 3: Force Storage (Bypass Curation)
```python
request.force_storage = True  # Skips AI analysis
await store_curated_memory(request)
```

---

## 🧹 Automatic Cleanup

The system includes automatic cleanup that runs:

- **Daily (2 AM)**: Remove expired memories
- **Weekly (Sunday 3 AM)**: Analyze consolidation opportunities  
- **Monthly (1st 4 AM)**: Comprehensive cleanup and optimization

### Manual Cleanup
```bash
# Analyze cleanup opportunities
POST /cam/curated/cleanup/analyze?entity_id=user123

# Execute cleanup actions  
POST /cam/curated/cleanup/execute
```

---

## 📊 Monitoring and Statistics

### Get Curation Stats
```bash
GET /cam/curated/stats/human-christian-kind-hare
```

**Response:**
```json
{
  "total_memories": 127,
  "storage_type_breakdown": {
    "facts": 23,
    "preferences": 15,
    "context": 67,
    "skills": 12
  },
  "average_confidence_score": 0.84,
  "average_access_count": 3.2
}
```

---

## 🚨 Error Handling

### Curation Analysis Failures
If AI analysis fails, the system defaults to conservative storage:
- Storage type: `context`
- Retention: `medium_term`
- Confidence: `0.3`
- Requires review: `true`

### Fallback Behavior
```python
# If curation service is down, use existing endpoints
try:
    result = await store_curated_memory(request)
except CurationServiceUnavailable:
    result = await store_multi_entity_memory(basic_request)
```

---

## 🧪 Testing Your Integration

Use the comprehensive test suite:

```bash
python test_memory_curation.py
```

This tests:
- ✅ Memory analysis decisions
- ✅ Curated storage with different agent preferences
- ✅ Intelligent retrieval with intent analysis
- ✅ Cleanup analysis and statistics
- ✅ Agent preference configurations

---

## 💡 Best Practices

### 1. **Configure Agent Preferences**
Each agent should have tailored curation preferences:

```python
technical_agent_prefs = {
    "priority_topics": ["code", "technical_specs", "debugging"],
    "retention_bias": "aggressive",  # Keep more technical info
    "agent_personality": "technical_specialist"
}

personal_assistant_prefs = {
    "priority_topics": ["schedules", "preferences", "personal_info"],
    "retention_bias": "balanced",
    "privacy_sensitivity": "private"  # Higher privacy standards
}
```

### 2. **Use Query Text for Better Retrieval**
Include the actual user query for intelligent retrieval:

```python
retrieval_request = {
    "requesting_entity": entity_id,
    "resonance_vectors": [{"vector": embedding, "weight": 1.0}],
    "query_text": user_query,  # ← This enables intent analysis
    "conversation_context": broader_context
}
```

### 3. **Monitor Curation Performance**
Regularly check curation statistics:

```python
# Monitor weekly
stats = await get_curation_stats(entity_id)
if stats.average_confidence_score < 0.6:
    # Review and adjust agent preferences
    adjust_curation_preferences()
```

### 4. **Handle Privacy Appropriately**
Set privacy sensitivity based on information type:

```python
if contains_sensitive_data(user_input):
    preferences.privacy_sensitivity = "confidential"
    preferences.retention_bias = "conservative"
```

---

## 🎉 Expected Results

With proper integration, you should see:

- **90%+ relevant memories** in retrieval results
- **Zero denial responses** ("I don't know your name") 
- **Automatic fact consolidation** (no duplicated information)
- **Privacy-appropriate storage** (sensitive data handled correctly)
- **Efficient cleanup** (expired memories automatically removed)

---

## 🆘 Support

If you need help integrating the memory curation system:

1. **Run the test suite**: `python test_memory_curation.py`
2. **Check the working examples**: `python agent_team_debug_query.py`  
3. **Review curation statistics**: `GET /cam/curated/stats/{entity_id}`
4. **Analyze curation decisions**: `POST /cam/curated/analyze`

The memory curation system is production-ready and will dramatically improve your agent's memory quality! 🚀