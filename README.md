# entrained.ai-engram - Content Addressable Memory System

A Redis-based semantic memory system for AI agents, enabling storage, retrieval, and relationship tracking of memories using vector embeddings.

## Features

- **Vector Similarity Search**: Store and retrieve memories based on semantic similarity using OpenAI embeddings
- **Multi-Entity Memory System** 🎉: Revolutionary witness-based access control for shared experiences
- **Comments-as-Engrams** 🆕: Transform website comments into semantic, searchable memories with intelligent threading
- **Natural Privacy Boundaries**: Private conversations stay private, group discussions are accessible to participants
- **Enterprise Security**: API key authentication, rate limiting, XSS protection, and content validation
- **Agent Participation**: AI agents can naturally participate in comment threads and discussions
- **Semantic Threading**: Comments connected by meaning, not just chronology
- **Cross-Article Discovery**: Find related discussions across your entire platform
- **Multimedia Support**: Handle text, images, websites, and documents
- **Causality Tracking**: Track relationships between memories and idea evolution
- **Annotation System**: Add context and relationships to existing memories
- **High Performance**: Built on Redis with vector search capabilities
- **RESTful API**: Clean, well-documented API endpoints for both single-agent and multi-entity operations

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- OpenAI API key (for embeddings) - **Required for production**

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd entrained.ai-engram
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env to add your OpenAI API key and security settings
```

Required environment variables:
```bash
# OpenAI Embeddings (Required)
OPENAI_API_KEY=your-openai-api-key-here
VECTOR_DIMENSIONS=1536

# Security (Required for production)
ENGRAM_API_SECRET_KEY=your-secure-api-key-here
ENGRAM_ENABLE_API_AUTH=true

# Optional: Comments-as-Engrams
ENABLE_COMMENT_ENGRAMS=true
ENABLE_AGENT_RESPONSES=true
```

3. Start entrained.ai-engram with Docker Compose:
```bash
docker-compose up -d
```

This will start:
- Redis Stack with vector search capabilities (port 6379)
- RedisInsight UI (port 8001)
- entrained.ai-engram API (port 8000)

### API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Comments-as-Engrams 🆕

Transform your website comments into intelligent, searchable memories with semantic threading and AI agent participation.

### Quick Example

```bash
# Store a comment
curl -X POST "http://localhost:8000/cam/comments/store" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "author_id": "user-123",
    "article_id": "article-456", 
    "comment_text": "This article brilliantly explains the future of AI memory systems."
  }'

# Get semantic thread
curl -X GET "http://localhost:8000/cam/comments/article/article-456/thread" \
  -H "X-API-Key: your-api-key"

# Find similar discussions across all articles
curl -X POST "http://localhost:8000/cam/comments/semantic/similar?comment_text=AI%20memory%20systems&limit=5" \
  -H "X-API-Key: your-api-key"
```

### Key Benefits

- **Semantic Threading**: Comments connected by meaning, not just reply chains
- **Cross-Article Discovery**: Find related discussions across your entire platform  
- **Agent Participation**: AI agents can contribute naturally to discussions
- **Editorial Intelligence**: Automatic content curation and quality scoring
- **Memory Persistence**: Comments become searchable institutional knowledge

📖 **[Read the full Comments-as-Engrams Integration Guide](COMMENTS_AS_ENGRAMS_GUIDE.md)**

### Example Usage

```python
import httpx
import asyncio

async def store_memory():
    async with httpx.AsyncClient() as client:
        # Store a memory
        memory = {
            "content": {
                "text": "Important insight about neural networks..."
            },
            "primary_vector": [0.1, 0.2, ...],  # 1536-dim vector from OpenAI embedding
            "metadata": {
                "timestamp": "2025-07-29T14:30:00Z",
                "agent_id": "claude-001",
                "memory_type": "insight"
            },
            "tags": ["ml", "neural-networks"]
        }
        
        response = await client.post("http://localhost:8000/cam/store", json=memory)
        memory_id = response.json()["memory_id"]
        
        # Retrieve similar memories
        retrieval = {
            "resonance_vectors": [{
                "vector": [0.1, 0.2, ...],  # Query vector
                "weight": 1.0
            }],
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.75
            }
        }
        
        response = await client.post("http://localhost:8000/cam/retrieve", json=retrieval)
        similar_memories = response.json()["memories"]
```

## Development

### Local Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run locally:
```bash
python main.py
```

### Running Tests

```bash
# Start services
docker-compose up -d

# Run test suite
python tests/test_example.py
python tests/comprehensive_test.py
python tests/advanced_test_suite.py
```

## Architecture

- **FastAPI**: Modern web framework for building APIs
- **Redis Stack**: Data storage with vector similarity search using HASH storage for optimal performance
- **Docker**: Containerized deployment
- **OpenAI**: Production-grade embedding generation (text-embedding-3-small model with 1536 dimensions)

## API Endpoints

### Single-Agent Memory Operations
- `POST /cam/store` - Store a new memory
- `POST /cam/retrieve` - Retrieve memories by similarity
- `GET /cam/memory/{memory_id}` - Get memory details
- `POST /cam/memory/{memory_id}/annotate` - Add annotation to existing memory
- `GET /cam/memory/{memory_id}/annotations` - Get all annotations for a memory

### Multi-Entity Memory Operations (NEW!)
- `POST /cam/multi/store` - Store shared experience with witness list
- `POST /cam/multi/retrieve` - Retrieve memories with entity-based access control
- `GET /cam/multi/memory/{memory_id}` - Get memory with witness verification
- `GET /cam/multi/situations/{entity_id}` - Get entity's situation history

### System Endpoints
- `GET /health` - Health check with Redis and vector index status
- `GET /` - API info and version

### Admin Endpoints (🔐 Protected)
- `POST /api/v1/admin/flush/memories` - Safely flush all memories (preserves indexes)
- `POST /api/v1/admin/recreate/indexes` - Recreate missing vector indexes
- `GET /api/v1/admin/status` - Detailed system health monitoring

**Admin Authentication:** HTTP Basic Auth with username `admin` and password `engram-admin-2025`

See [AGENT_INTEGRATION_GUIDE.md](AGENT_INTEGRATION_GUIDE.md) for detailed integration examples including the new multi-entity features.

## Configuration

Environment variables (prefix with `ENGRAM_`):

- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `VECTOR_DIMENSIONS` - Embedding dimensions (default: 1536 for OpenAI)
- `OPENAI_API_KEY` - OpenAI API key for embeddings (required)
- `DEBUG` - Enable debug mode (default: false)

## 🔐 Enterprise Security

Production-ready security features for enterprise deployments:

### Authentication & Authorization
- **API Key Authentication**: Required for all endpoints in production
- **Multi-method Support**: X-API-Key header, Authorization Bearer, or query parameter
- **Constant-time Validation**: Protection against timing attacks

### Rate Limiting & Protection
- **Per-IP Rate Limiting**: 60 requests/minute, 1000 requests/hour
- **Automatic IP Blocking**: Temporary blocks for excessive requests
- **XSS Protection**: Content validation and HTML entity escaping
- **Input Validation**: Length limits and dangerous pattern detection

### Content Security
- **Comment Validation**: Length limits, toxicity detection, spam prevention
- **Content Sanitization**: HTML escaping and dangerous script removal
- **Moderation Workflows**: Built-in flagging and review systems

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` for HTTPS enforcement

### Configuration
```bash
# Enable security features
ENGRAM_ENABLE_API_AUTH=true
ENGRAM_API_SECRET_KEY=your-production-secret-key

# Rate limiting (optional customization)
ENGRAM_MAX_REQUESTS_PER_MINUTE=60
ENGRAM_MAX_REQUESTS_PER_HOUR=1000
```

## 🕵️ Built-in Witness Protection 🕵️

Engram comes with the world's most advanced **Witness Protection Program**:

- **No Backdoors**: Even system admins can't access memories they didn't witness
- **Natural Privacy Boundaries**: If you weren't there, you can't see it
- **Tamper-Proof Testimony**: Vector-based memory storage prevents witness tampering
- **Anonymous Witnesses**: Support for `anonymous-witness-uuid` entity IDs
- **Cross-Examination Resistance**: No central authority can override witness permissions
- **Memory Relocation**: Witnesses can change entity IDs without losing access
- **Safe House Storage**: Isolated Redis indexes protect sensitive memories

*"The only memory system where witnesses are truly protected!"* 🛡️

## Future Enhancements

- Causality chain visualization
- Temporal memory decay
- Distributed deployment
- Multi-modal embeddings
- Memory consolidation
- **Witness Protection Dashboard** 🔍 (coming soon!)

## License

[Your License Here]