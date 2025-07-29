# Content Addressable Memory (CAM) System
## Technical Briefing & Implementation Guide

### Executive Summary

The Content Addressable Memory (CAM) system is a foundational microservice designed to provide semantic memory capabilities for AI agents and autonomous systems. It enables storage, retrieval, and relationship tracking of memories using vector embeddings, with support for multimedia content, annotations, and causality chains.

**Vision**: A planetary-scale memory network that enables collaborative intelligence across AI systems, with complete intellectual provenance and idea genealogy tracking.

**Current Scope**: Redis-based microservice API for the entrained.ai faculty system, designed for future scalability.

---

## Core Concepts

### Memory Structure
Each memory is a self-contained unit consisting of:
- **Content**: Text, multimedia links, and metadata
- **Vector Embedding**: Semantic representation for similarity search
- **Stable ID**: Permanent identifier for referencing
- **Causality Links**: Parent/child relationships showing idea evolution
- **Annotations**: Community-added context and relationships

### Key Principles
- **Write-Only**: No memory modification, only creation and annotation
- **Stable IDs**: Once assigned, memory IDs never change
- **Vector-First**: All retrieval based on semantic similarity
- **Causality Tracking**: Automatic attribution and idea genealogy
- **Multimedia Support**: Text, images, websites, documents
- **Microservice Architecture**: Clean API boundaries for scalability

---

## API Specification

### Core Endpoints

#### 1. Memory Storage
```http
POST /cam/store
Content-Type: application/json

{
  "content": {
    "text": "Discussion about neural network efficiency and activation patterns...",
    "media": [
      {
        "type": "image",
        "url": "https://arxiv.org/figures/activation_patterns.png",
        "embedding": [0.1, 0.2, 0.3, ...],
        "description": "Graph showing activation patterns in transformer layers",
        "mime_type": "image/png"
      },
      {
        "type": "website",
        "url": "https://distill.pub/2020/circuits/",
        "title": "Neural Network Interpretability",
        "embedding": [0.3, 0.4, 0.5, ...],
        "preview_text": "Interactive visualizations of neural network internals...",
        "domain": "distill.pub"
      },
      {
        "type": "document",
        "url": "https://arxiv.org/pdf/2301.12345.pdf",
        "title": "Activation-Free Neural Networks",
        "embedding": [0.7, 0.8, 0.9, ...],
        "authors": ["Smith, J.", "Johnson, K."],
        "abstract": "We present a novel approach..."
      }
    ]
  },
  "primary_vector": [0.1, 0.2, 0.3, ...],  // 1536-dim embedding
  "metadata": {
    "timestamp": "2025-07-29T14:30:00Z",
    "agent_id": "claude-faculty-001",
    "memory_type": "conversation",
    "participants": ["claude", "prof.sorbel@berlin.edu"],
    "thread_id": "email-thread-12345",
    "domain": "machine_learning",
    "confidence": 0.95
  },
  "tags": ["faculty:claude", "domain:ml", "collaboration", "efficiency"],
  "causality": {
    "parent_memories": ["mem-445", "mem-672"],
    "influence_strength": [0.8, 0.6],
    "synthesis_type": "cross_domain_connection",
    "reasoning": "Combines energy efficiency concepts with neural architecture insights"
  },
  "retention": {
    "ttl": null,
    "importance": 0.85,
    "decay_function": "logarithmic"
  }
}
```

**Response:**
```json
{
  "memory_id": "mem-789",
  "status": "stored",
  "timestamp": "2025-07-29T14:30:15Z",
  "vector_dimensions": 1536
}
```

#### 2. Memory Retrieval
```http
POST /cam/retrieve
Content-Type: application/json

{
  "resonance_vectors": [
    {
      "vector": [0.1, 0.2, 0.3, ...],
      "weight": 1.0,
      "label": "primary_query",
      "description": "Main search concept"
    },
    {
      "vector": [0.3, 0.4, 0.5, ...],
      "weight": 0.7,
      "label": "context",
      "description": "Background context from conversation"
    }
  ],
  "tags": {
    "include": ["faculty:claude", "domain:ml"],
    "exclude": ["draft", "private", "archived"]
  },
  "filters": {
    "timestamp_range": {
      "after": "2024-01-01T00:00:00Z",
      "before": "2025-12-31T23:59:59Z"
    },
    "memory_types": ["conversation", "fact", "insight"],
    "agent_ids": ["claude-faculty-001", "gpt4-faculty-002"],
    "confidence_threshold": 0.7,
    "domains": ["machine_learning", "cognitive_science"]
  },
  "retrieval": {
    "top_k": 10,
    "similarity_threshold": 0.75,
    "diversity_lambda": 0.5,
    "boost_recent": 0.1
  },
  "ordering": [
    {"field": "similarity", "direction": "desc", "weight": 0.7},
    {"field": "recency", "direction": "desc", "weight": 0.2},
    {"field": "importance", "direction": "desc", "weight": 0.1}
  ]
}
```

**Response:**
```json
{
  "memories": [
    {
      "memory_id": "mem-789",
      "similarity_score": 0.92,
      "content_preview": "Discussion about neural network efficiency...",
      "metadata": {
        "timestamp": "2025-07-29T14:30:00Z",
        "agent_id": "claude-faculty-001",
        "memory_type": "conversation",
        "domain": "machine_learning"
      },
      "tags": ["faculty:claude", "domain:ml", "efficiency"],
      "media_count": 2,
      "annotation_count": 3
    }
  ],
  "total_found": 45,
  "search_time_ms": 23,
  "query_vector_dims": 1536
}
```

#### 3. Memory Details
```http
GET /cam/memory/{memory_id}
```

**Response:**
```json
{
  "memory_id": "mem-789",
  "content": {
    "text": "Full memory content...",
    "media": [...]
  },
  "primary_vector": [0.1, 0.2, ...],
  "metadata": {...},
  "tags": [...],
  "causality": {...},
  "created_at": "2025-07-29T14:30:00Z",
  "storage_backend": "redis",
  "compression": "gzip"
}
```

#### 4. Annotations
```http
POST /cam/memory/{memory_id}/annotate

{
  "annotator_id": "research-assistant-007",
  "annotation": {
    "type": "relevance_boost",
    "content": "This directly relates to the energy efficiency discussion from last week",
    "vector": [0.5, 0.6, 0.7, ...],
    "confidence": 0.9,
    "tags": ["cross-reference", "energy-efficiency"],
    "evidence_links": ["mem-445", "mem-672"]
  }
}
```

```http
GET /cam/memory/{memory_id}/annotations
```

#### 5. Causality Chains
```http
GET /cam/causality-chain/{memory_id}?depth=5&min_influence=0.3

{
  "target_memory": "mem-789",
  "chain": [
    {
      "memory_id": "mem-445",
      "influence_strength": 0.8,
      "generation": 1,
      "synthesis_type": "refinement",
      "connection_reasoning": "Built upon efficiency concepts"
    },
    {
      "memory_id": "mem-220",
      "influence_strength": 0.9,
      "generation": 2,
      "synthesis_type": "foundation",
      "connection_reasoning": "Original energy efficiency insight"
    }
  ],
  "convergence_points": ["mem-445"],
  "breakthrough_moments": ["mem-672"],
  "influence_tree": {...}
}
```

#### 6. Resonance Graph (Advanced)
```http
GET /cam/resonance-graph?memory_ids=123,456,789&depth=2&threshold=0.6

{
  "nodes": [
    {
      "memory_id": "mem-123",
      "vector": [0.1, 0.2, ...],
      "resonance_strength": 0.95,
      "centrality": 0.8,
      "domain": "machine_learning"
    }
  ],
  "edges": [
    {
      "from": "mem-123",
      "to": "mem-456",
      "similarity": 0.82,
      "relationship_type": "conceptual_extension",
      "weight": 0.9
    }
  ],
  "clusters": [
    {
      "cluster_id": "efficiency_cluster",
      "members": ["mem-123", "mem-456"],
      "centroid": [0.5, 0.6, ...],
      "coherence": 0.87
    }
  ]
}
```

---

## Technical Implementation

### Technology Stack
- **Backend**: Python (FastAPI framework)
- **Storage**: Redis with RedisJSON and RediSearch modules
- **Vector Operations**: Redis Vector Similarity Search (VSS)
- **Deployment**: Docker containers
- **API Documentation**: OpenAPI/Swagger auto-generation

### Redis Schema Design

#### Memory Storage
```
Key: mem:{memory_id}
Type: JSON
Structure:
{
  "id": "mem-789",
  "content": {...},
  "vector": [...],
  "metadata": {...},
  "tags": [...],
  "causality": {...},
  "created_at": "2025-07-29T14:30:00Z"
}
```

#### Vector Index
```
Index: memories_vector_index
Type: HNSW (Hierarchical Navigable Small World)
Vector Dimension: 1536
Distance Metric: COSINE
```

#### Tag Index
```
Index: memories_tag_index
Fields: tags[], metadata.agent_id, metadata.domain, metadata.memory_type
```

#### Annotations
```
Key: annotations:{memory_id}
Type: LIST of JSON objects
```

#### Causality Relations
```
Key: causality:{memory_id}:parents
Key: causality:{memory_id}:children
Type: SET
```

### Performance Considerations

#### Vector Search Optimization
- Use HNSW algorithm for approximate nearest neighbor search
- Batch vector operations where possible
- Implement vector quantization for large-scale deployment
- Cache frequently accessed embeddings

#### Memory Management
- Implement TTL for temporary memories
- Use Redis memory optimization settings
- Consider data compression for large content
- Implement memory tier strategies (hot/warm/cold)

#### Scalability Patterns
- Horizontal sharding by memory ID hash
- Read replicas for query distribution
- Async annotation processing
- Rate limiting and backpressure handling

---

## Development Phases

### Phase 1: Core MVP (Week 1)
- [x] Basic memory storage and retrieval
- [x] Vector similarity search
- [x] Tag-based filtering
- [x] Simple metadata handling
- [x] Docker containerization

### Phase 2: Enhanced Features (Week 2)
- [ ] Multimedia content support
- [ ] Advanced filtering and ordering
- [ ] Memory detail endpoints
- [ ] Basic annotation system
- [ ] API documentation

### Phase 3: Causality System (Week 3)
- [ ] Causality chain tracking
- [ ] Influence strength calculation
- [ ] Chain traversal algorithms
- [ ] Attribution reporting

### Phase 4: Advanced Analytics (Week 4)
- [ ] Resonance graph generation
- [ ] Cluster analysis
- [ ] Usage analytics
- [ ] Performance optimization

---

## Usage Examples

### Email Faculty Integration
```python
# Incoming email processing
email_content = "Discussion about activation-free networks..."
email_vector = embedding_service.encode(email_content)

# Retrieve relevant memories
relevant_memories = cam_client.retrieve(
    resonance_vectors=[{"vector": email_vector, "weight": 1.0}],
    tags={"include": ["faculty:claude", "domain:ml"]},
    top_k=5
)

# Generate response with context
context = "\n".join([mem["content_preview"] for mem in relevant_memories])
response = ai_service.generate_response(
    prompt=f"Context: {context}\n\nQuestion: {email_content}"
)

# Store the interaction
cam_client.store({
    "content": {"text": f"Q: {email_content}\nA: {response}"},
    "primary_vector": response_vector,
    "metadata": {
        "agent_id": "claude-faculty-001",
        "memory_type": "conversation",
        "participants": ["claude", "prof.sorbel@berlin.edu"]
    },
    "causality": {
        "parent_memories": [mem["memory_id"] for mem in relevant_memories],
        "influence_strength": [0.8, 0.6, 0.5, 0.3, 0.2]
    }
})
```

---

## Security & Privacy

### Access Control
- API key authentication for service access
- Agent-based permissions for memory access
- Tag-based content filtering
- Rate limiting per agent/service

### Data Privacy
- Optional content encryption at rest
- Configurable data retention policies
- Memory anonymization capabilities
- GDPR compliance considerations

### Audit Trail
- All API calls logged with timestamps
- Memory access tracking
- Causality relationship audit
- Performance metrics collection

---

## Testing Strategy

### Unit Tests
- Vector similarity calculations
- Tag filtering logic
- Causality chain algorithms
- Memory serialization/deserialization

### Integration Tests
- Redis storage operations
- API endpoint functionality
- Cross-service communication
- Performance benchmarks

### Load Testing
- Concurrent memory storage
- High-volume vector searches
- Memory retrieval under load
- Annotation system stress testing

---

## Monitoring & Operations

### Health Checks
- Redis connectivity
- Vector index integrity
- Memory storage capacity
- API response times

### Metrics Collection
- Memory storage rate
- Query response times
- Vector search accuracy
- Causality chain depth distribution

### Alerting
- Storage capacity warnings
- Query performance degradation
- Vector index corruption
- Unusual access patterns

---

## Future Enhancements

### Planetary Scale Considerations
- Distributed vector indices
- Cross-cluster memory replication
- Global causality tracking
- Federated search capabilities

### Advanced Features
- Temporal memory decay
- Concept drift detection
- Automated memory consolidation
- Multi-modal embedding support

### AI Integration
- Memory importance prediction
- Automatic tagging
- Causality relationship inference
- Content summarization

---

This system will serve as the foundational memory layer for the entrained.ai faculty system and future AI collaboration platforms.