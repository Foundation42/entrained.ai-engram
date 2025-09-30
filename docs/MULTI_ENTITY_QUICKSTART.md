# Multi-Entity Memory System Quick Start

## Entity ID Format

Entity IDs are flexible but should follow a consistent pattern:

### Recommended Format
```
type-name-identifier
```

Examples:
- `human-christian-12345678-90ab-cdef-ghij-klmnopqrstuv`
- `agent-claude-abc123def456`
- `human-alice-kindhare`
- `bot-assistant-7890`

### Important Notes
1. **Hyphens are automatically removed internally** for Redis TAG compatibility
2. All these formats work:
   - `human-christian-uuid-with-hyphens`
   - `human-christian-uuidwithouthyphens`
   - `humanchristianuuid` (no hyphens at all)
3. Be consistent with your entity IDs across sessions

## Simple Store Example

```python
import httpx
import asyncio

async def store_memory():
    memory = {
        "witnessed_by": ["human-alice-123", "agent-bob-456"],
        "situation_type": "conversation",
        "content": {
            "text": "Alice: Hello! Bob: Hi there!",
            "speakers": {
                "human-alice-123": "Hello!",
                "agent-bob-456": "Hi there!"
            },
            "summary": "Friendly greeting"
        },
        "primary_vector": [0.1] * 768,  # Replace with real embedding
        "metadata": {
            "timestamp": "2025-07-30T12:00:00Z",
            "situation_duration_minutes": 5,
            "interaction_quality": 0.9,
            "topic_tags": ["greeting", "social"]
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://46.62.130.230:8000/cam/multi/store",
            json=memory
        )
        print(response.json())

asyncio.run(store_memory())
```

## Simple Retrieve Example

```python
async def retrieve_memories():
    request = {
        "requesting_entity": "human-alice-123",
        "resonance_vectors": [{
            "vector": [0.1] * 768,  # Replace with real embedding
            "weight": 1.0
        }],
        "retrieval_options": {
            "top_k": 10,
            "similarity_threshold": 0.5
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://46.62.130.230:8000/cam/multi/retrieve", 
            json=request
        )
        result = response.json()
        print(f"Found {len(result['memories'])} memories")

asyncio.run(retrieve_memories())
```

## Debugging Tips

1. **Check server health**: `curl http://46.62.130.230:8000/health`
2. **Verify API is running**: `curl http://46.62.130.230:8000/`
3. **Use consistent entity IDs** - if you use `human-alice-123` to store, use the same to retrieve
4. **Embeddings must be exactly 768 dimensions** of float values
5. **Timestamps must end with 'Z'**: `2025-07-30T12:00:00Z`

## Common Issues

### "NEGOTIATION" Error
- Usually a client-side networking issue
- Check your HTTP client timeout settings
- Verify you're using the correct URL and port

### No Memories Found
- Verify entity ID matches exactly what was used to store
- Check similarity threshold (try 0.0 for testing)
- Ensure the requesting entity was in the `witnessed_by` list

### 500 Errors
- Check all required fields are present
- Verify vector is exactly 768 floats
- Ensure timestamp format is correct with 'Z' suffix