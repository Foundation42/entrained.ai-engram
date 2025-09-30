# Engram Integration Guide for Agents

> **🎉 NEW**: Engram now supports **Multi-Entity Memory System** with witness-based access control! See the [Multi-Entity Integration](#multi-entity-integration) section below.

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

## Session Isolation

Engram supports session isolation to prevent memory leaks between different conversations or contexts. Always include a `session_id` when storing memories:

```python
memory = {
    "content": {
        "text": "Private conversation content",
        "media": []
    },
    "primary_vector": embedding,
    "metadata": {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_id": "my-agent-001",
        "memory_type": "conversation",
        "session_id": "unique-session-123",  # IMPORTANT: Session isolation
        "domain": "private-chat",
        "participants": ["alice", "bob"],  # Optional: Track participants
        "thread_id": "thread-456"  # Optional: Thread tracking
    },
    "tags": ["private", "session-123"]
}
```

## Retrieving with Filters

Use filters to retrieve only relevant memories:

```python
# Retrieve only from specific session
search_request = {
    "resonance_vectors": [{
        "vector": query_embedding,
        "weight": 1.0
    }],
    "retrieval": {
        "top_k": 10,
        "similarity_threshold": 0.75
    },
    "filters": {
        "session_ids": ["unique-session-123"],  # Session isolation
        "agent_ids": ["my-agent-001"],
        "domains": ["private-chat"],
        "participants": ["alice"],  # Find memories with Alice
        "confidence_threshold": 0.8,  # Min confidence
        "timestamp_range": {
            "after": "2025-07-29T00:00:00Z",
            "before": "2025-07-30T00:00:00Z"
        }
    }
}
```

## Complete Working Example

```python
import httpx
import asyncio
from datetime import datetime
import uuid

async def store_memory_with_session():
    # Generate or obtain your embedding vector (768 dimensions)
    embedding = [0.1] * 768  # Replace with actual embedding
    
    # Create a unique session ID for isolation
    session_id = str(uuid.uuid4())
    
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
            "session_id": session_id,  # Session isolation
            "domain": "machine-learning",
            "confidence": 0.95,
            "participants": ["researcher-1", "researcher-2"],
            "thread_id": "research-thread-001"
        },
        "tags": ["neural-networks", "deep-learning"],
        "causality": {  # Optional
            "parent_memories": ["parent-id-1", "parent-id-2"],
            "influence_strength": [0.8, 0.6]
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Store the memory
        response = await client.post(
            "http://your-engram-server:8000/cam/store",
            json=memory
        )
        
        if response.status_code == 200:
            result = response.json()
            memory_id = result['memory_id']
            print(f"Success! Memory ID: {memory_id}")
            
            # Retrieve only from this session
            search_request = {
                "resonance_vectors": [{
                    "vector": embedding,
                    "weight": 1.0
                }],
                "retrieval": {
                    "top_k": 5,
                    "similarity_threshold": 0.5
                },
                "filters": {
                    "session_ids": [session_id]  # Only this session
                }
            }
            
            response = await client.post(
                "http://your-engram-server:8000/cam/retrieve",
                json=search_request
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"Found {results['total_found']} memories in session")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

# Run the example
asyncio.run(store_memory_with_session())
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

## Multi-Entity Integration

The Multi-Entity Memory System allows multiple agents and humans to share experiences with natural privacy boundaries. Only entities who witnessed an experience can access its memory.

### Key Concepts

1. **Witness-Based Access**: Only entities present during an experience can access the memory
2. **Situation Context**: Memories are organized by situation (e.g., consultation, group discussion)
3. **Natural Privacy**: Private conversations remain private, group discussions are accessible to all participants
4. **Co-Participant Filtering**: Find memories with specific other entities

### Storing Multi-Entity Memories

```python
# Store a private consultation between two entities
consultation_memory = {
    "witnessed_by": [
        "agent-claude-123",
        "human-alice-456"
    ],
    "situation_type": "consultation_1to1",  # Type of interaction
    "content": {
        "text": "Alice: How do I optimize this algorithm? Claude: Let me explain...",
        "speakers": {
            "human-alice-456": "How do I optimize this algorithm?",
            "agent-claude-123": "Let me explain the optimization approach..."
        },
        "summary": "Algorithm optimization consultation"
    },
    "primary_vector": embedding,  # 768-dimensional vector
    "metadata": {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "situation_duration_minutes": 25,
        "interaction_quality": 0.95,
        "topic_tags": ["algorithms", "optimization", "consultation"]
    }
}

# Store via POST to /cam/multi/store
response = await client.post(
    "http://your-engram-server:8000/cam/multi/store",
    json=consultation_memory
)
```

### Storing Group Experiences

```python
# Store a group research discussion
group_memory = {
    "witnessed_by": [
        "agent-claude-123",
        "human-alice-456", 
        "human-bob-789",
        "agent-gpt-321"
    ],
    "situation_type": "group_discussion",
    "content": {
        "text": "Full discussion transcript here...",
        "speakers": {
            "human-alice-456": "What about quantum computing?",
            "human-bob-789": "I've been researching quantum algorithms",
            "agent-claude-123": "Let me explain the current state...",
            "agent-gpt-321": "Building on Claude's point..."
        },
        "summary": "Group discussion on quantum computing applications"
    },
    "primary_vector": embedding,
    "metadata": {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "situation_duration_minutes": 45,
        "interaction_quality": 0.88,
        "topic_tags": ["quantum", "research", "algorithms"]
    }
}
```

### Retrieving Multi-Entity Memories

```python
# Retrieve memories as a specific entity
retrieval_request = {
    "requesting_entity": "human-alice-456",  # Who is requesting
    "resonance_vectors": [{
        "vector": query_embedding,
        "weight": 1.0
    }],
    "retrieval_options": {
        "top_k": 10,
        "similarity_threshold": 0.7,
        "include_speakers_breakdown": True
    }
}

# Alice will only see memories she witnessed
response = await client.post(
    "http://your-engram-server:8000/cam/multi/retrieve",
    json=retrieval_request
)
```

### Advanced Filtering

```python
# Find memories with specific co-participants
retrieval_with_filters = {
    "requesting_entity": "agent-claude-123",
    "resonance_vectors": [{
        "vector": query_embedding,
        "weight": 1.0
    }],
    "entity_filters": {
        "co_participants": ["human-alice-456"]  # Only memories with Alice
    },
    "situation_filters": {
        "situation_types": ["consultation_1to1"],  # Only consultations
        "topic_tags": ["algorithms"],
        "time_range": {
            "after": "2025-07-25T00:00:00Z",
            "before": "2025-07-30T00:00:00Z"
        }
    },
    "retrieval_options": {
        "top_k": 5,
        "similarity_threshold": 0.6
    }
}
```

### Get Entity's Situation History

```python
# Get all situations an entity has participated in
response = await client.get(
    f"http://your-engram-server:8000/cam/multi/situations/{entity_id}"
)

# Returns:
{
    "entity_id": "human-alice-456",
    "situations": [
        {
            "situation_id": "sit-abc123",
            "situation_type": "group_discussion",
            "participants": ["human-alice-456", "agent-claude-123", ...],
            "created_at": "2025-07-30T10:00:00Z",
            "memory_count": 3
        }
    ],
    "total_situations": 5
}
```

### Privacy and Access Control

1. **Witness-Only Access**: An entity can only retrieve memories they witnessed
2. **No Backdoors**: Even system admins cannot access private memories they didn't witness
3. **Natural Boundaries**: The system enforces real-world privacy expectations
4. **Access Denial Tracking**: The API reports how many memories were blocked

### Multi-Entity Response Format

```python
{
    "memories": [
        {
            "memory_id": "mem-xyz789",
            "similarity_score": 0.92,
            "access_granted": true,
            "access_reason": "witnessed_by_includes_requesting_entity",
            "situation_summary": "Algorithm optimization consultation",
            "situation_type": "consultation_1to1",
            "co_participants": ["agent-claude-123"],  # Other witnesses
            "content_preview": "Alice: How do I optimize...",
            "speakers_involved": ["human-alice-456", "agent-claude-123"],
            "metadata": {...}
        }
    ],
    "access_denied_count": 2,  # Memories you couldn't access
    "total_found": 3,
    "search_time_ms": 45,
    "entity_verification": {
        "requesting_entity": "human-alice-456",
        "access_granted_count": 1,
        "search_scope": "witnessed_memories_only"
    }
}
```

### Complete Multi-Entity Example

```python
import httpx
import asyncio
from datetime import datetime
import uuid

async def multi_entity_memory_example():
    # Entity IDs (in practice, these would be persistent)
    alice_id = f"human-alice-{uuid.uuid4()}"
    claude_id = f"agent-claude-{uuid.uuid4()}"
    bob_id = f"human-bob-{uuid.uuid4()}"
    
    # Generate embedding (replace with actual embedding service)
    embedding = [0.1] * 768
    
    async with httpx.AsyncClient() as client:
        # 1. Store a private consultation
        private_memory = {
            "witnessed_by": [alice_id, claude_id],
            "situation_type": "consultation_1to1",
            "content": {
                "text": "Alice: I need help with neural networks. Claude: Let's start with...",
                "speakers": {
                    alice_id: "I need help with neural networks",
                    claude_id: "Let's start with the basics..."
                },
                "summary": "Neural network fundamentals consultation"
            },
            "primary_vector": embedding,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "situation_duration_minutes": 30,
                "interaction_quality": 0.9,
                "topic_tags": ["neural-networks", "machine-learning"]
            }
        }
        
        resp = await client.post(
            "http://localhost:8000/cam/multi/store",
            json=private_memory
        )
        print(f"Stored private consultation: {resp.json()}")
        
        # 2. Store a group discussion
        group_memory = {
            "witnessed_by": [alice_id, claude_id, bob_id],
            "situation_type": "group_discussion",
            "content": {
                "text": "Group discussion about AI ethics...",
                "speakers": {
                    alice_id: "What about bias in AI?",
                    bob_id: "Great question!",
                    claude_id: "Let me explain..."
                },
                "summary": "AI ethics group discussion"
            },
            "primary_vector": embedding,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "situation_duration_minutes": 60,
                "interaction_quality": 0.85,
                "topic_tags": ["ai-ethics", "bias", "fairness"]
            }
        }
        
        resp = await client.post(
            "http://localhost:8000/cam/multi/store",
            json=group_memory
        )
        print(f"Stored group discussion: {resp.json()}")
        
        # 3. Bob tries to retrieve memories
        bob_request = {
            "requesting_entity": bob_id,
            "resonance_vectors": [{
                "vector": embedding,
                "weight": 1.0
            }],
            "retrieval_options": {
                "top_k": 10,
                "similarity_threshold": 0.0
            }
        }
        
        resp = await client.post(
            "http://localhost:8000/cam/multi/retrieve",
            json=bob_request
        )
        results = resp.json()
        
        print(f"\nBob can access {len(results['memories'])} memories:")
        for mem in results['memories']:
            print(f"- {mem['situation_summary']}")
        print(f"Access denied to {results['access_denied_count']} private memories")
        
        # Bob will only see the group discussion, not the private consultation!

asyncio.run(multi_entity_memory_example())
```

### Migration from Single-Agent

Existing single-agent memories remain accessible through the original `/cam/store` and `/cam/retrieve` endpoints. To migrate memories to multi-entity format:

1. Retrieve existing memories using filters
2. Transform to multi-entity format (add `witnessed_by` list)
3. Store using `/cam/multi/store`
4. Update your agents to use multi-entity endpoints

### Best Practices

1. **Entity ID Format**: Use consistent, meaningful IDs like `human-alice-uuid` or `agent-claude-uuid`
2. **Situation Types**: Use clear types like `consultation_1to1`, `group_discussion`, `public_presentation`
3. **Speaker Attribution**: Always include speaker breakdown for multi-party conversations
4. **Privacy First**: Default to `participants_only` privacy level
5. **Embedding Quality**: Use high-quality embeddings that capture the essence of the shared experience

## Need Help?

- API Documentation: http://your-engram-server:8000/docs
- Health Check: http://your-engram-server:8000/health
- Single-Agent Examples: See `/tests/test_comprehensive.py`
- Multi-Entity Examples: See `/tests/test_multi_entity.py`