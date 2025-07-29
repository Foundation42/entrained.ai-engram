# entrained.ai-engram - Content Addressable Memory System

A Redis-based semantic memory system for AI agents, enabling storage, retrieval, and relationship tracking of memories using vector embeddings.

## Features

- **Vector Similarity Search**: Store and retrieve memories based on semantic similarity
- **Multimedia Support**: Handle text, images, websites, and documents
- **Causality Tracking**: Track relationships between memories and idea evolution
- **Annotation System**: Add context and relationships to existing memories
- **High Performance**: Built on Redis with vector search capabilities
- **RESTful API**: Clean, well-documented API endpoints

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- Ollama with `nomic-embed-text:latest` model (for embeddings)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd entrained.ai-engram
```

2. Start Ollama (if not running):
```bash
ollama pull nomic-embed-text:latest
ollama serve
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
            "primary_vector": [0.1, 0.2, ...],  # 768-dim vector from embedding
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
- **Ollama**: Local embedding generation (nomic-embed-text model with 768 dimensions)

## API Endpoints

- `POST /cam/store` - Store a new memory
- `POST /cam/retrieve` - Retrieve memories by similarity
- `GET /cam/memory/{memory_id}` - Get memory details
- `POST /cam/memory/{memory_id}/annotate` - Add annotation to existing memory
- `GET /cam/memory/{memory_id}/annotations` - Get all annotations for a memory
- `GET /health` - Health check with Redis and vector index status
- `GET /` - API info and version

## Configuration

Environment variables (prefix with `ENGRAM_`):

- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `VECTOR_DIMENSIONS` - Embedding dimensions (default: 768)
- `OLLAMA_BASE_URL` - Ollama API URL (default: http://localhost:11434)
- `DEBUG` - Enable debug mode (default: false)

## Future Enhancements

- Causality chain visualization
- Temporal memory decay
- Distributed deployment
- Multi-modal embeddings
- Memory consolidation

## License

[Your License Here]