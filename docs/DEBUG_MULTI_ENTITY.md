# Debug Guide for Multi-Entity AttributeError

## The Issue

You're getting an AttributeError when trying to access `situation.situation_type`. This happens because the request format doesn't match what the API expects.

## Correct Request Format

The `/cam/multi/store` endpoint expects `situation_type` as a **TOP-LEVEL** field, not nested inside a `situation` object:

### ❌ WRONG Format (causes AttributeError):
```json
{
    "witnessed_by": ["human-alice-123", "agent-bob-456"],
    "situation": {  // ❌ NO! Don't nest situation
        "situation_type": "conversation",
        "situation_id": "sit-123"
    },
    "content": {...},
    "primary_vector": [...],
    "metadata": {...}
}
```

### ✅ CORRECT Format:
```json
{
    "witnessed_by": ["human-alice-123", "agent-bob-456"],
    "situation_type": "conversation",  // ✅ YES! Top-level field
    "situation_id": "sit-123",         // ✅ Optional, also top-level
    "content": {
        "text": "Full conversation text",
        "speakers": {
            "human-alice-123": "What she said",
            "agent-bob-456": "What he said"
        },
        "summary": "Brief summary"
    },
    "primary_vector": [0.1, 0.2, ...],  // 768 floats
    "metadata": {
        "timestamp": "2025-07-30T14:00:00Z",
        "situation_duration_minutes": 30,
        "interaction_quality": 0.9,  // Goes in metadata!
        "topic_tags": ["conversation", "ai"]
    }
}
```

## Complete Working Example

```python
import httpx
import asyncio
from datetime import datetime

async def store_multi_entity_memory():
    memory = {
        # Top-level witness list
        "witnessed_by": [
            "human-christian-123",
            "agent-claude-456"
        ],
        
        # Top-level situation fields (NOT nested!)
        "situation_type": "conversation",
        "situation_id": None,  # Optional, will be auto-generated
        
        # Content with speakers breakdown
        "content": {
            "text": "Christian: Hi Claude! Claude: Hello Christian!",
            "speakers": {
                "human-christian-123": "Hi Claude!",
                "agent-claude-456": "Hello Christian!"
            },
            "summary": "Friendly greeting exchange"
        },
        
        # Embedding vector
        "primary_vector": [0.1] * 768,  # Replace with real embedding
        
        # Metadata (with interaction_quality here!)
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "situation_duration_minutes": 5,
            "interaction_quality": 0.95,  # HERE, not in situation!
            "topic_tags": ["greeting", "social"]
        },
        
        # Optional fields
        "causality": None,
        "access_control": None  # Will default to participants_only
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://46.62.130.230:8000/cam/multi/store",
            json=memory,
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Memory ID: {result['memory_id']}")
        else:
            print(f"Error {response.status_code}: {response.text}")

asyncio.run(store_multi_entity_memory())
```

## Key Points

1. **No nested `situation` object** - `situation_type` is a top-level field
2. **`interaction_quality` goes in metadata**, not situation
3. **All timestamps must end with 'Z'**
4. **Vectors must be exactly 768 floats**
5. **`witnessed_by` must have at least one entity**

## Testing Your Fix

After fixing your request format, you should see in the logs:
```
INFO: Storing multi-entity memory witnessed by 2 entities
INFO: Stored multi-entity memory mem-xxx witnessed by 2 entities
```

Instead of AttributeError!