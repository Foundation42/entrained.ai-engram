# Engram Integration Guide for Agents

## Common Integration Issues and Solutions

### Error: "A tuple item must be str, int, float or bytes"

This error occurs when sending improperly formatted data to the Engram API. The API has strict validation requirements.

## Correct Memory Format

```python
# CORRECT format for storing a memory
memory_request = {
    "content": {
        "text": "Your memory text here",  # Required, must be string
        "media": []  # Optional, but must be a list (not None)
    },
    "primary_vector": [0.1, 0.2, ...],  # Required, 768-dimensional float array
    "metadata": {
        "timestamp": "2025-07-29T10:30:00Z",  # Required, ISO format with Z
        "agent_id": "your-agent-id",  # Required, string
        "memory_type": "insight",  # Required, string (not None)
        "domain": "general",  # Optional, but if included must be string
        "confidence": 0.95  # Optional, float between 0-1
    },
    "tags": ["tag1", "tag2"]  # Optional, but must be list of strings (not None)
}
```

## Common Mistakes to Avoid

### 1. None Values
```python
# ❌ WRONG - None values not allowed
{
    "content": {
        "text": "Test",
        "media": None  # ERROR: Must be empty list []
    },
    "metadata": {
        "memory_type": None,  # ERROR: Must be a string
        ...
    },
    "tags": None  # ERROR: Must be empty list []
}

# ✅ CORRECT - Use empty values instead
{
    "content": {
        "text": "Test",
        "media": []  # Correct: empty list
    },
    "metadata": {
        "memory_type": "general",  # Correct: default string
        ...
    },
    "tags": []  # Correct: empty list
}
```

### 2. Missing Required Fields
```python
# ❌ WRONG - Missing required metadata fields
{
    "content": {"text": "Test"},
    "primary_vector": [...],
    "metadata": {
        "agent_id": "test"
        # ERROR: Missing timestamp and memory_type
    }
}

# ✅ CORRECT - All required fields included
{
    "content": {"text": "Test"},
    "primary_vector": [...],
    "metadata": {
        "timestamp": "2025-07-29T10:30:00Z",
        "agent_id": "test",
        "memory_type": "general"
    }
}
```

### 3. Media Items Format
```python
# ❌ WRONG - Incomplete media item
{
    "content": {
        "text": "Test",
        "media": [
            {"type": "image"}  # ERROR: Missing required 'url' field
        ]
    }
}

# ✅ CORRECT - Proper media item
{
    "content": {
        "text": "Test",
        "media": [
            {
                "type": "image",
                "url": "https://example.com/image.jpg"
            }
        ]
    }
}
```

### 4. Invalid Tag Values
```python
# ❌ WRONG - Tags must be strings
{
    "tags": [None, "tag1", True, 123]  # ERROR: Only strings allowed
}

# ✅ CORRECT - All tags are strings
{
    "tags": ["tag1", "tag2", "123"]  # All strings
}
```

## Complete Working Example

```python
import httpx
import asyncio
from datetime import datetime

async def store_memory_correctly():
    # Generate or obtain your embedding vector (768 dimensions)
    embedding = [0.1] * 768  # Replace with actual embedding
    
    memory = {
        "content": {
            "text": "This is an important insight about neural networks",
            "media": []  # Empty list if no media
        },
        "primary_vector": embedding,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_id": "my-agent-001",
            "memory_type": "insight",
            "domain": "machine-learning",  # Optional
            "confidence": 0.95  # Optional
        },
        "tags": ["neural-networks", "deep-learning"],  # Optional
        "causality": {  # Optional
            "parent_memories": ["parent-id-1", "parent-id-2"],
            "influence_strength": [0.8, 0.6]
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://your-engram-server:8000/cam/store",
            json=memory
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Memory ID: {result['memory_id']}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

# Run the example
asyncio.run(store_memory_correctly())
```

## Data Validation Rules

1. **Required Fields**:
   - `content.text`: Must be a non-empty string
   - `primary_vector`: Must be a list of 768 floats
   - `metadata.timestamp`: ISO format datetime with 'Z' suffix
   - `metadata.agent_id`: Non-empty string
   - `metadata.memory_type`: Non-empty string

2. **Optional Fields** (if included, must follow type rules):
   - `content.media`: List of MediaItem objects (each with 'type' and 'url')
   - `tags`: List of strings
   - `causality`: Object with parent_memories (list of strings)
   - All other metadata fields: Appropriate types (no None values)

3. **Type Conversions**:
   - Convert None to empty string "" or empty list []
   - Convert booleans to strings: "true" or "false"
   - Ensure all numbers are int or float
   - Complex objects should be serialized to JSON strings if needed

## Debugging Tips

1. **Check Your Data Types**:
   ```python
   # Before sending, validate your data
   assert isinstance(memory["content"]["text"], str)
   assert isinstance(memory["primary_vector"], list)
   assert len(memory["primary_vector"]) == 768
   assert all(isinstance(x, (int, float)) for x in memory["primary_vector"])
   ```

2. **Use the API Docs**:
   Visit `http://your-engram-server:8000/docs` for interactive API documentation

3. **Start Simple**:
   First test with minimal required fields, then add optional fields

## Need Help?

- API Documentation: http://your-engram-server:8000/docs
- Health Check: http://your-engram-server:8000/health
- Example Scripts: See `/tests` directory in the Engram repository