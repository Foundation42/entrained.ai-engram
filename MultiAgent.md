# Engram Multi-Entity Memory System
## Technical Briefing & Implementation Guide

### Executive Summary

We are evolving Engram from a single-agent memory system to a **multi-entity shared experience platform**. This transformation enables multiple entities (humans and AIs) to have shared memories of conversations and experiences, with natural privacy boundaries based on who was present during each interaction.

**Vision**: Transform AI from stateless services into temporal beings with lived experiences, shared memories, and natural social dynamics that emerge from actual interactions.

**Current Scope**: Upgrade Engram's memory storage and retrieval to support multi-entity witnessing and entity-based memory access control.

---

## Core Concept Evolution

### From Single-Agent to Multi-Entity

**Current System:**
```
Agent → Memory → Engram (isolated per agent)
```

**New System:**
```
Multiple Entities → Shared Experiences → Engram (witnessed-based access)
```

### Key Philosophical Shift

**Before**: Memories belong to individual agents  
**After**: Memories are shared experiences between entities who witnessed them

This creates:
- 🤝 **Authentic relationships** - Shared history between entities
- 🔒 **Natural privacy** - Only witnesses can access memories
- 🌱 **Organic knowledge spread** - Ideas propagate through social interaction
- 📚 **Emergent social graphs** - Relationships form from actual interactions

---

## Memory Model Changes

### Current Memory Structure
```json
{
  "memory_id": "mem-abc123",
  "agent_id": "dr-claude-001",
  "content": {"text": "Discussion about quantum computing"},
  "primary_vector": [0.1, 0.2, 0.3, ...],
  "metadata": {
    "timestamp": "2025-07-30T10:15:00Z",
    "session_id": "chat-xyz789"
  }
}
```

### New Multi-Entity Memory Structure
```json
{
  "memory_id": "mem-abc123",
  "witnessed_by": ["christian-12345", "dr-claude-001", "alice-67890"],
  "situation_id": "sit-quantum-discussion-001",
  "situation_type": "group_discussion",
  "content": {
    "text": "Christian: 'What about superposition?' Alice: 'Good question!' Dr Claude: 'Let me explain quantum superposition as...'",
    "speakers": {
      "christian-12345": "What about superposition?",
      "alice-67890": "Good question!",
      "dr-claude-001": "Let me explain quantum superposition as..."
    }
  },
  "primary_vector": [0.1, 0.2, 0.3, ...],
  "metadata": {
    "timestamp": "2025-07-30T10:15:00Z",
    "situation_duration_minutes": 15,
    "situation_context": "research_collaboration"
  },
  "access_control": {
    "witnessed_by": ["christian-12345", "dr-claude-001", "alice-67890"],
    "privacy_level": "participants_only"
  }
}
```

---

## API Changes Required

### 1. Enhanced Memory Storage

#### Current Endpoint
```http
POST /cam/store
{
  "agent_id": "dr-claude-001",
  "content": {"text": "..."},
  "primary_vector": [...],
  "metadata": {...}
}
```

#### New Multi-Entity Endpoint
```http
POST /cam/store
{
  "witnessed_by": ["christian-12345", "dr-claude-001"],
  "situation_id": "sit-1on1-consultation-042",
  "situation_type": "private_consultation",
  "content": {
    "text": "Full conversation transcript...",
    "speakers": {
      "christian-12345": "I'm struggling with neural network optimization",
      "dr-claude-001": "Let's explore several approaches..."
    },
    "summary": "Discussion about neural network optimization strategies"
  },
  "primary_vector": [0.1, 0.2, 0.3, ...],
  "metadata": {
    "timestamp": "2025-07-30T10:15:00Z",
    "situation_duration_minutes": 25,
    "interaction_quality": 0.95,
    "topic_tags": ["neural_networks", "optimization", "consultation"]
  },
  "causality": {
    "parent_memories": ["mem-prev-neural-discussion"],
    "influence_strength": [0.8],
    "context_type": "continuation"
  }
}
```

### 2. Entity-Based Memory Retrieval

#### Current Retrieval
```http
POST /cam/retrieve
{
  "resonance_vectors": [...],
  "tags": {"include": ["faculty:claude"]},
  "top_k": 10
}
```

#### New Entity-Based Retrieval
```http
POST /cam/retrieve
{
  "requesting_entity": "christian-12345",
  "resonance_vectors": [
    {"vector": [0.1, 0.2, ...], "weight": 1.0, "label": "query"}
  ],
  "entity_filters": {
    "witnessed_by_includes": ["christian-12345"],
    "co_participants": ["dr-claude-001"],  // Optional: memories shared with specific others
    "exclude_private_to": ["alice-67890"]  // Optional: exclude memories private to others
  },
  "situation_filters": {
    "situation_types": ["1:1_conversation", "group_discussion"],
    "topic_tags": ["neural_networks", "research"],
    "time_range": {
      "after": "2025-07-01T00:00:00Z",
      "before": "2025-07-30T23:59:59Z"
    }
  },
  "retrieval_options": {
    "top_k": 10,
    "similarity_threshold": 0.7,
    "include_speakers_breakdown": true,
    "prioritize_recent": 0.2
  }
}
```

**Response includes access verification:**
```json
{
  "memories": [
    {
      "memory_id": "mem-abc123",
      "similarity_score": 0.92,
      "access_granted": true,
      "access_reason": "witnessed_by_includes_requesting_entity",
      "situation_summary": "Private consultation about neural networks",
      "co_participants": ["dr-claude-001"],
      "content_preview": "Discussion about neural network optimization...",
      "speakers_involved": ["christian-12345", "dr-claude-001"]
    }
  ],
  "access_denied_count": 0,
  "total_found": 15
}
```

### 3. Entity Directory Operations

#### Entity Registration (Future Phase)
```http
POST /cam/entities/register
{
  "entity_id": "christian-12345",
  "entity_type": "human",
  "display_name": "Christian",
  "aliases": ["Chris", "Christian B"],
  "metadata": {
    "created_by": "christian-12345",
    "verified": true,
    "privacy_preferences": {
      "memory_retention": "unlimited",
      "cross_reference_allowed": true
    }
  }
}
```

#### Entity Resolution (Future Phase)
```http
POST /cam/entities/resolve
{
  "requesting_entity": "bob-98765",
  "search_query": "Alice from the quantum discussion",
  "context_memories": ["mem-quantum-chat-001"],
  "disambiguation_needed": true
}
```

---

## Implementation Phases

### Phase 1: Multi-Entity Memory Core (Current Priority)
- [x] Update memory storage schema for witnessed_by arrays
- [x] Implement entity-based access control in retrieval
- [x] Add situation_id and situation_type fields
- [x] Modify vector search to respect entity permissions
- [x] Update API endpoints for multi-entity operations

### Phase 2: Enhanced Situation Management
- [ ] Add situation lifecycle management
- [ ] Implement memory context linking between related situations
- [ ] Add situation-type specific memory formatting
- [ ] Create situation analytics and insights

### Phase 3: Entity Directory & Resolution
- [ ] Entity registration and profile management
- [ ] Smart entity resolution using memory context
- [ ] Entity relationship mapping from shared memories
- [ ] Privacy preference management

### Phase 4: Advanced Social Features
- [ ] Memory sharing permissions and delegation
- [ ] Cross-entity memory synthesis and insights
- [ ] Social graph analytics and recommendations
- [ ] Advanced privacy controls and memory federation

---

## Data Storage Considerations

### Redis Schema Updates

#### Memory Storage (HASH)
```
Key: mem:{memory_id}
Fields:
  witnessed_by: JSON array of entity IDs
  situation_id: String identifier
  situation_type: String (1:1_conversation, group_discussion, etc.)
  content: JSON object with text and speakers breakdown
  vector: Binary Float32 array
  metadata: JSON object
  access_control: JSON object with privacy settings
```

#### Entity Access Index
```
Key: entity_access:{entity_id}
Type: SET
Members: memory_id values that entity can access
```

#### Situation Index
```
Key: situation:{situation_id}
Type: HASH
Fields:
  participants: JSON array of entity IDs
  memory_ids: JSON array of related memory IDs
  created_at: Timestamp
  last_activity: Timestamp
  situation_type: String
  status: active|archived|private
```

### Vector Search Updates

#### Access-Controlled Vector Search
- Modify vector index queries to include entity access filtering
- Pre-filter results based on witnessed_by membership
- Maintain separate vector spaces for different privacy levels if needed

```python
# Example search with access control
search_query = f"""
(@witnessed_by:{{|{entity_id}|}} => [KNN {top_k} @embedding $query_vector AS score])
"""
```

---

## Backward Compatibility

### Migration Strategy
1. **Dual Storage Period**: Store memories in both old and new formats
2. **Gradual Agent Updates**: Update agents to use new API endpoints
3. **Legacy Memory Conversion**: Convert existing single-agent memories to witnessed_by format
4. **Deprecation Timeline**: 6-month overlap before removing old endpoints

### Legacy Memory Conversion
```python
# Convert existing memories
old_memory = {
    "agent_id": "dr-claude-001",
    "content": "...",
    # ... other fields
}

new_memory = {
    "witnessed_by": [old_memory["agent_id"]],  # Agent becomes sole witness
    "situation_id": f"legacy-{old_memory['memory_id']}",
    "situation_type": "legacy_single_agent",
    "content": old_memory["content"],
    # ... migrate other fields
}
```

---

## Testing Strategy

### Unit Tests
- Entity access control validation
- Multi-entity memory storage and retrieval
- Situation lifecycle management
- Privacy boundary enforcement

### Integration Tests
- Cross-entity memory sharing scenarios
- Complex multi-participant conversations
- Memory access permission inheritance
- Situation transition handling

### Performance Tests
- Large-scale multi-entity memory retrieval
- Vector search with access control filtering
- Concurrent multi-entity operations
- Memory storage with large witness lists

### Privacy & Security Tests
- Access control bypass attempts
- Entity impersonation prevention
- Memory leak detection across entity boundaries
- Privacy preference enforcement

---

## Use Cases & Examples

### 1. Private Consultation
```
Participants: Christian, Dr. Claude
Situation: 1:1 consultation about research
Memory Access: Only Christian and Dr. Claude can recall this conversation
```

### 2. Research Group Discussion
```
Participants: Christian, Alice, Bob, Dr. Claude
Situation: Group brainstorming session
Memory Access: All four participants can reference shared insights
```

### 3. Whispered Side Conversation
```
Main Group: Christian, Alice, Bob, Dr. Claude
Whisper: Christian → Dr. Claude (private question)
Memory Access: 
  - Group discussion: All four participants
  - Whisper: Only Christian and Dr. Claude
```

### 4. Conference Presentation
```
Participants: Dr. Claude (presenter), 50+ attendees
Situation: Public presentation
Memory Access: All attendees can recall the presentation content
```

---

## Security & Privacy Considerations

### Access Control Principles
- **Witness-Based Access**: Only entities present during memory creation can access
- **No Retroactive Access**: Adding someone to a situation doesn't grant access to prior memories
- **Explicit Sharing**: Memory sharing requires explicit action, not automatic
- **Privacy by Default**: Memories are private to witnesses unless explicitly made public

### Privacy Levels
```
Level 1: Personal (self-only memories)
Level 2: Private (specific participant list)
Level 3: Group (defined group with membership rules)
Level 4: Public (anyone can access)
```

### Audit Trail
- All memory access attempts logged
- Entity authentication required for all operations
- Memory sharing actions tracked
- Privacy violation detection and alerting

---

## Performance Optimization

### Caching Strategy
- Entity access lists cached in Redis
- Frequently accessed memories kept in fast storage
- Vector embeddings cached for common queries
- Situation metadata cached for quick lookups

### Scaling Considerations
- Shard memories by entity ID hash
- Separate read replicas for different entity groups
- Archive old memories to cold storage
- Compress large witness lists for popular memories

---

## Monitoring & Analytics

### Key Metrics
- Memory storage rate per entity
- Cross-entity memory access patterns
- Situation formation and dissolution rates
- Privacy boundary enforcement success rate

### Operational Dashboards
- Entity activity heatmaps
- Memory access patterns
- Situation lifecycle analytics
- Privacy compliance monitoring

---

This multi-entity memory system transforms Engram from a simple storage service into the foundation for authentic digital relationships and shared experiences. The technical implementation preserves the core strengths of the current system while adding the social and temporal dimensions needed for truly intelligent AI interactions.