# Engram MCP Integration Guide

**Complete guide for integrating Engram memory system with AI clients via Model Context Protocol (MCP)**

---

## 🚀 Quick Start

### For Claude Code Users

Add Engram to Claude Code in one command:

```bash
claude mcp add --transport http engram https://engram-fi-1.entrained.ai:8443/mcp/ \
  --header "X-API-Key: your-api-key-here"
```

Verify connection:
```bash
claude mcp list
```

You should see:
```
✓ engram: https://engram-fi-1.entrained.ai:8443/mcp/ (HTTP) - Connected
```

### For Claude Desktop Users

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "engram": {
      "type": "http",
      "url": "https://engram-fi-1.entrained.ai:8443/mcp/",
      "headers": {
        "X-API-Key": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop.

---

## 🛠️ Available Tools

Engram provides **6 MCP tools** for persistent memory across all your AI sessions:

| Tool | Purpose | Key Features |
|------|---------|--------------|
| **store_memory** | Save information | 7 memory types, importance scoring, tags |
| **retrieve_memories** | Semantic search | Tag filtering, type filtering, similarity threshold |
| **get_memory** | Fetch by ID | Full memory details with metadata |
| **list_recent_memories** | Timeline view | Most recent memories first |
| **get_memory_stats** | System status | Health check, feature list |
| **memory** | Unified interface | Auto-detects store vs retrieve |

---

## 📝 Usage Examples

### 1. Storing Memories

**Store a user preference:**
```json
{
  "name": "store_memory",
  "arguments": {
    "content": "User Christian prefers concise answers without preamble",
    "tags": ["user-preference", "communication-style"],
    "memory_type": "preference",
    "importance": 0.8
  }
}
```

**Store a solution:**
```json
{
  "name": "store_memory",
  "arguments": {
    "content": "Fixed Redis timeout by increasing socket_timeout to 5s and adding retry logic",
    "tags": ["redis", "timeout", "solution"],
    "memory_type": "solution",
    "importance": 0.9
  }
}
```

**Store a fact:**
```json
{
  "name": "store_memory",
  "arguments": {
    "content": "The Engram project uses Redis Stack for vector storage and FastAPI for the API",
    "tags": ["engram", "architecture", "tech-stack"],
    "memory_type": "fact",
    "importance": 0.7
  }
}
```

### 2. Retrieving Memories

**Basic semantic search:**
```json
{
  "name": "retrieve_memories",
  "arguments": {
    "query": "how does the user prefer to communicate",
    "top_k": 5
  }
}
```

**Search with type filter:**
```json
{
  "name": "retrieve_memories",
  "arguments": {
    "query": "solutions for Redis connection problems",
    "memory_type": "solution",
    "top_k": 3
  }
}
```

**Search with tag filter:**
```json
{
  "name": "retrieve_memories",
  "arguments": {
    "query": "system architecture details",
    "filter_tags": ["architecture", "engram"],
    "top_k": 5
  }
}
```

**Adjust similarity threshold:**
```json
{
  "name": "retrieve_memories",
  "arguments": {
    "query": "anything about Redis",
    "threshold": 0.5,
    "top_k": 10
  }
}
```

### 3. Getting Specific Memories

**Fetch by ID:**
```json
{
  "name": "get_memory",
  "arguments": {
    "memory_id": "mem-572c55c67943"
  }
}
```

### 4. Listing Recent Memories

**Get recent timeline:**
```json
{
  "name": "list_recent_memories",
  "arguments": {
    "limit": 10
  }
}
```

### 5. System Health Check

**Check status:**
```json
{
  "name": "get_memory_stats",
  "arguments": {}
}
```

### 6. Unified Interface (Natural Language)

**Auto-detect store:**
```json
{
  "name": "memory",
  "arguments": {
    "request": "Remember that Christian successfully deployed the MCP server"
  }
}
```

**Auto-detect retrieve:**
```json
{
  "name": "memory",
  "arguments": {
    "request": "What do I know about MCP deployment?"
  }
}
```

---

## 🎯 Memory Types

Choose the appropriate type for better organization:

| Type | Use For | Example |
|------|---------|---------|
| **fact** | Objective information | "Redis Stack supports vector search" |
| **preference** | User/system preferences | "User prefers dark mode" |
| **event** | Things that happened | "Deployed MCP server on 2025-09-30" |
| **solution** | Problem-solving approaches | "Fixed timeout by increasing limit" |
| **insight** | Realizations and understanding | "Vector embeddings enable semantic search" |
| **decision** | Choices made and why | "Decided to use MCP instead of REST" |
| **pattern** | Recurring themes | "Authentication issues often relate to tokens" |

---

## ⭐ Importance Scoring

Rate memories 0-1 for retrieval priority:

- **0.9-1.0**: Critical (solutions, key decisions, essential facts)
- **0.7-0.8**: Important (user preferences, major insights)
- **0.5-0.6**: Useful (general facts, helpful context)
- **0.3-0.4**: Nice to have (minor details, optional info)

---

## 🏷️ Tagging Best Practices

**Good tags:**
- Specific: `redis`, `authentication`, `user-preference`
- Searchable: `solution`, `bug-fix`, `performance`
- Hierarchical: `engram`, `engram-api`, `engram-mcp`

**Use 3-5 tags per memory:**
```json
["redis", "timeout", "solution", "docker"]
```

---

## 🔌 Direct API Usage

### HTTP Endpoint

**URL:** `https://engram-fi-1.entrained.ai:8443/mcp/`
**Protocol:** MCP Streamable HTTP (2025-03-26 spec)
**Authentication:** API key via `X-API-Key` header

### Initialize Connection

**Request:**
```bash
curl -k -X POST https://engram-fi-1.entrained.ai:8443/mcp/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "my-client", "version": "1.0.0"}
    }
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}},
    "serverInfo": {
      "name": "engram-memory",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### List Tools

**Request:**
```bash
curl -k -X POST https://engram-fi-1.entrained.ai:8443/mcp/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "store_memory",
        "description": "💾 Store information in Engram...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "content": {"type": "string"},
            "tags": {"type": "array"},
            "memory_type": {"type": "string", "enum": ["fact", "preference", ...]},
            "importance": {"type": "number", "minimum": 0, "maximum": 1}
          },
          "required": ["content"]
        }
      }
      // ... 5 more tools
    ]
  },
  "id": 2
}
```

### Call Tool

**Request:**
```bash
curl -k -X POST https://engram-fi-1.entrained.ai:8443/mcp/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "store_memory",
      "arguments": {
        "content": "Test memory from API",
        "tags": ["test"],
        "memory_type": "fact",
        "importance": 0.5
      }
    }
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "✅ Memory stored successfully!\n\n**ID:** mem-abc123\n**Type:** fact\n**Tags:** test\n**Importance:** 0.5\n\nThis information is now available across all future sessions and devices."
      }
    ]
  },
  "id": 3
}
```

---

## 🧪 Testing

### Run Test Suite

```bash
pytest tests/test_mcp_endpoints.py -v
```

**Coverage:**
- ✅ Initialize handshake
- ✅ Tool discovery
- ✅ Store operations
- ✅ Retrieve with filters
- ✅ Memory types
- ✅ Error handling
- ✅ Performance

### Manual Testing

**Python:**
```python
import httpx
import json

client = httpx.Client(verify=False)
url = "https://engram-fi-1.entrained.ai:8443/mcp/"
headers = {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
}

# Store memory
response = client.post(url, headers=headers, json={
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "store_memory",
        "arguments": {
            "content": "Testing from Python",
            "tags": ["test", "python"],
            "memory_type": "fact"
        }
    }
})

print(response.json())
```

**JavaScript:**
```javascript
const response = await fetch('https://engram-fi-1.entrained.ai:8443/mcp/', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'retrieve_memories',
      arguments: {
        query: 'testing',
        top_k: 5
      }
    }
  })
});

const result = await response.json();
console.log(result);
```

---

## 🔧 Advanced Configuration

### Adjusting Search Sensitivity

**Strict matching (high threshold):**
```json
{
  "query": "exact topic",
  "threshold": 0.8,
  "top_k": 3
}
```

**Broad matching (low threshold):**
```json
{
  "query": "general area",
  "threshold": 0.5,
  "top_k": 10
}
```

### Combining Filters

**Tag + Type + Threshold:**
```json
{
  "query": "Redis problems",
  "filter_tags": ["redis", "bug-fix"],
  "memory_type": "solution",
  "threshold": 0.6,
  "top_k": 5
}
```

### Importance-Based Storage

**Critical information:**
```json
{
  "content": "Production database credentials must be rotated monthly",
  "memory_type": "decision",
  "importance": 1.0
}
```

**Background context:**
```json
{
  "content": "Redis was released in 2009",
  "memory_type": "fact",
  "importance": 0.3
}
```

---

## 🐛 Troubleshooting

### Connection Issues

**Problem:** `Failed to connect`

**Solutions:**
1. Verify API key is correct
2. Check URL has trailing slash: `/mcp/`
3. Ensure network can reach server

### No Results Found

**Problem:** Retrieving memories returns nothing

**Solutions:**
1. Lower threshold: Try 0.5 instead of 0.7
2. Broaden query terms
3. Check with `list_recent_memories` to verify storage
4. Wait a moment for indexing (usually instant)

### Slow Performance

**Problem:** Requests taking >2 seconds

**Solutions:**
1. Check network latency to server
2. Reduce `top_k` parameter
3. Use more specific queries
4. Contact administrator about server load

---

## 📊 Performance Characteristics

- **Storage:** ~0.5s per memory
- **Retrieval:** ~0.3s for top-5 results
- **Embedding:** OpenAI text-embedding-3-small (1536 dimensions)
- **Distance Metric:** Cosine similarity
- **Index:** Redis FT.SEARCH with HNSW

---

## 🔒 Security

- **Authentication:** API key required in `X-API-Key` header
- **Transport:** HTTPS/TLS encryption
- **Isolation:** Memories are agent-scoped (future: multi-entity support)
- **Validation:** Input sanitization and XSS protection

---

## 🚀 Production Deployment

### Server Setup

1. Clone repository
2. Configure `.env` with API keys
3. Generate SSL certificates
4. Deploy with Docker Compose
5. Configure volume mounts for live reload

See `README.md` for detailed deployment instructions.

### Monitoring

**Health endpoint:**
```bash
curl -k https://engram-fi-1.entrained.ai:8443/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "redis": "connected",
  "vector_index": true
}
```

---

## 📚 Further Reading

- **MCP Specification:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Redis Stack:** [redis.io/docs/stack](https://redis.io/docs/stack/)
- **Vector Search:** [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

---

## 🤝 Support

**Issues:** Open issue on GitHub repository
**Questions:** Contact project maintainers
**Updates:** Follow repository for new features

---

**Built with ❤️ using MCP, Redis Stack, and FastAPI**