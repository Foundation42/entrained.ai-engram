# Migration Guide: Single-Agent to Multi-Entity System

## Important: Two Separate Systems!

The Engram server has **TWO separate memory systems**:

1. **Single-Agent System** (original)
   - Store: `POST /cam/store`
   - Retrieve: `POST /cam/retrieve`
   - Uses `engram_vector_idx` index

2. **Multi-Entity System** (new)
   - Store: `POST /cam/multi/store`
   - Retrieve: `POST /cam/multi/retrieve`
   - Uses `engram_vector_idx_multi` index

**⚠️ CRITICAL**: Memories stored in one system are NOT accessible from the other!

## Why Your Multi-Entity Retrieval Returns 0 Results

From the logs, you're:
1. Storing memories using `/cam/store` (single-agent system)
2. Trying to retrieve using `/cam/multi/retrieve` (multi-entity system)
3. Result: 0 memories found because they're in different systems!

## Solution: Use Multi-Entity Endpoints

### Correct Multi-Entity Store Format

```python
# CORRECT: Store to multi-entity system
memory = {
    "witnessed_by": ["human-christian-123", "agent-claude-456"],
    "situation_type": "conversation",  # Required
    "content": {
        "text": "Christian: What did I tell you about my work? Claude: You mentioned you love working on AI systems.",
        "speakers": {
            "human-christian-123": "What did I tell you about my work?",
            "agent-claude-456": "You mentioned you love working on AI systems."
        },
        "summary": "Christian asks about previous work discussion"
    },
    "primary_vector": embedding,  # 768 dimensions
    "metadata": {
        "timestamp": "2025-07-30T13:35:00Z",  # Required, must end with Z
        "situation_duration_minutes": 5,
        "interaction_quality": 0.85,  # THIS GOES IN METADATA, NOT SITUATION!
        "topic_tags": ["work", "ai-systems", "memory-recall"]
    }
}

# Store to MULTI-ENTITY endpoint
response = await client.post(
    "http://46.62.130.230:8000/cam/multi/store",  # NOT /cam/store!
    json=memory
)
```

### Correct Multi-Entity Retrieve Format

```python
# CORRECT: Retrieve from multi-entity system
retrieval = {
    "requesting_entity": "agent-claude-456",  # Who is asking
    "resonance_vectors": [{
        "vector": query_embedding,  # 768 dimensions
        "weight": 1.0
    }],
    "retrieval_options": {
        "top_k": 10,
        "similarity_threshold": 0.5
    }
}

# Retrieve from MULTI-ENTITY endpoint
response = await client.post(
    "http://46.62.130.230:8000/cam/multi/retrieve",  # NOT /cam/retrieve!
    json=retrieval
)
```

## Field Locations Reference

### SituationInfo fields:
- `situation_id` (auto-generated if not provided)
- `situation_type` (REQUIRED: e.g., "conversation", "consultation")
- `duration_minutes` (optional)
- `location` (optional)
- `context` (optional)

### Metadata fields:
- `timestamp` (REQUIRED)
- `situation_duration_minutes` (optional)
- **`interaction_quality`** (optional, 0-1 score) ← GOES HERE, NOT IN SITUATION!
- `topic_tags` (optional list)
- `situation_context` (optional)
- `entity_roles` (optional dict)

## Quick Test

To verify multi-entity is working:

```python
import httpx
import asyncio

async def test_multi_entity():
    # 1. Store a memory
    store_response = await client.post(
        "http://46.62.130.230:8000/cam/multi/store",
        json={
            "witnessed_by": ["test-entity-1"],
            "situation_type": "test",
            "content": {
                "text": "This is a test",
                "speakers": {"test-entity-1": "This is a test"},
                "summary": "Test memory"
            },
            "primary_vector": [0.1] * 768,
            "metadata": {
                "timestamp": "2025-07-30T14:00:00Z",
                "interaction_quality": 0.9  # Correct location!
            }
        }
    )
    print(f"Store result: {store_response.status_code}")
    
    # 2. Retrieve it
    retrieve_response = await client.post(
        "http://46.62.130.230:8000/cam/multi/retrieve",
        json={
            "requesting_entity": "test-entity-1",
            "resonance_vectors": [{"vector": [0.1] * 768, "weight": 1.0}],
            "retrieval_options": {"top_k": 10, "similarity_threshold": 0.0}
        }
    )
    result = retrieve_response.json()
    print(f"Found {len(result['memories'])} memories")
```

## Migration Steps

If you have existing memories in single-agent system:

1. Retrieve them using `/cam/retrieve`
2. Transform to multi-entity format (add `witnessed_by` list)
3. Store using `/cam/multi/store`
4. Update your code to use multi-entity endpoints exclusively