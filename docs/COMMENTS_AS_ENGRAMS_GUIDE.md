# Comments-as-Engrams Integration Guide

The Engram Memory System now supports **Comments-as-Engrams** - treating website comments, chat messages, and discussions as semantic memories that can be intelligently threaded, searched, and curated.

## Overview

Comments-as-Engrams transforms traditional comment systems by:

- **Semantic Threading**: Comments are connected by meaning, not just chronology
- **Agent Participation**: AI agents can participate naturally in discussions
- **Editorial Intelligence**: Automatic content curation and moderation
- **Cross-Article Discovery**: Find related discussions across your entire platform
- **Memory Persistence**: Comments become searchable institutional knowledge

## Quick Start

### 1. Store a Comment

```bash
curl -X POST "http://your-engram-server:8000/cam/comments/store" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "author_id": "user-123",
    "article_id": "article-456", 
    "comment_text": "This is a fascinating article about AI memory systems.",
    "comment_type": "root_comment"
  }'
```

**Response:**
```json
{
  "memory_id": "mem-abc123",
  "status": "stored",
  "witnessed_by": ["user-123", "public", "agent-claude-prime"],
  "situation_id": "article-article-456-comments",
  "timestamp": "2025-08-05T08:55:29.401039",
  "comment_type": "root_comment",
  "thread_id": "thread-article-456-xyz789",
  "reply_depth": 0
}
```

### 2. Reconstruct Thread

```bash
curl -X GET "http://your-engram-server:8000/cam/comments/article/article-456/thread" \
  -H "X-API-Key: your-api-key"
```

### 3. Semantic Search

```bash
curl -X POST "http://your-engram-server:8000/cam/comments/semantic/similar?comment_text=AI%20memory%20systems&limit=5" \
  -H "X-API-Key: your-api-key"
```

## API Endpoints

### Core Comment Operations

#### `POST /cam/comments/store`
Store a new comment as an engram.

**Request Body:**
```json
{
  "author_id": "string",       // Required: User identifier
  "article_id": "string",      // Required: Article/page identifier  
  "comment_text": "string",    // Required: Comment content
  "comment_type": "root_comment|reply|agent_response", // Optional
  "parent_comment_id": "string", // Optional: For replies
  "metadata": {                // Optional: Additional context
    "user_agent": "string",
    "ip_address": "string",
    "platform": "web|mobile|api"
  }
}
```

**Response:**
- `memory_id`: Unique identifier for the stored comment
- `witnessed_by`: Entities that can access this comment
- `situation_id`: Grouping identifier for the discussion
- `thread_id`: Semantic thread identifier
- `reply_depth`: How deep in the conversation thread

#### `GET /cam/comments/article/{article_id}/thread`
Reconstruct the comment thread for an article using semantic similarity.

**Query Parameters:**
- `include_agents`: Include AI agent responses (default: false)
- `max_depth`: Maximum reply depth (default: 5)
- `sort_by`: "timestamp" or "relevance" (default: "timestamp")

#### `POST /cam/comments/semantic/similar`
Find semantically similar comments across all articles.

**Query Parameters:**
- `comment_text`: Text to find similar comments for
- `similarity_threshold`: Minimum similarity score (0.0-1.0, default: 0.7)
- `limit`: Maximum results (default: 10)
- `cross_article`: Search across articles (default: true)

### Agent Integration

#### `POST /cam/comments/agent/respond`
Generate an AI agent response to a comment thread.

```json
{
  "article_id": "string",
  "agent_id": "agent-claude-prime", 
  "context_comments": 5,
  "response_style": "helpful|editorial|conversational"
}
```

### Moderation & Curation

#### `GET /cam/comments/moderation/queue`
Get comments flagged for moderation review.

#### `POST /cam/comments/moderate`
Apply moderation actions to comments.

```json
{
  "memory_id": "string",
  "action": "approve|reject|edit|flag",
  "reason": "string",
  "moderator_id": "string"
}
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Comments-as-Engrams Configuration
ENABLE_COMMENT_ENGRAMS=true
COMMENT_MAX_LENGTH=10000
COMMENT_MIN_LENGTH=10
ENABLE_AGENT_RESPONSES=true
DEFAULT_AGENT_ID=agent-claude-prime

# Semantic Threading
THREAD_SIMILARITY_THRESHOLD=0.6
MAX_THREAD_DEPTH=10
ENABLE_CROSS_ARTICLE_THREADING=true

# Moderation
ENABLE_AUTO_MODERATION=true
TOXICITY_THRESHOLD=0.8
SPAM_DETECTION_ENABLED=true
```

### OpenAI Embeddings

The system uses OpenAI's `text-embedding-3-small` model (1536 dimensions):

```bash
# Required for semantic functionality
OPENAI_API_KEY=your-openai-api-key
VECTOR_DIMENSIONS=1536
```

## Data Models

### Comment Engram Structure

Comments are stored as multi-entity memories with this structure:

```json
{
  "memory_id": "mem-unique-id",
  "witnessed_by": ["author-id", "public", "agent-id"],
  "situation_type": "public_discussion",
  "situation_id": "article-{article_id}-comments",
  "content": {
    "text": "User: {comment_text}\nAgent: {optional_response}",
    "content_type": "comment_thread",
    "comment_metadata": {
      "author_id": "string",
      "article_id": "string", 
      "comment_type": "root_comment|reply|agent_response",
      "parent_comment_id": "string",
      "reply_depth": 0,
      "thread_id": "string"
    }
  },
  "primary_vector": [1536-dim embedding],
  "timestamp": "ISO-8601",
  "co_participants": ["author-id", "agent-id"]
}
```

### Access Control

Comments use witness-based access control:

- **Public Comments**: Witnessed by `["author-id", "public", "agent-id"]`
- **Private Messages**: Witnessed by specific users only
- **Moderated Comments**: Include moderator in witness list
- **Agent Responses**: Always include the responding agent

## Integration Examples

### React/JavaScript Frontend

```javascript
class EngramComments {
  constructor(apiKey, baseUrl) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async storeComment(articleId, authorId, commentText) {
    const response = await fetch(`${this.baseUrl}/cam/comments/store`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      },
      body: JSON.stringify({
        article_id: articleId,
        author_id: authorId,
        comment_text: commentText
      })
    });
    return response.json();
  }

  async getThread(articleId) {
    const response = await fetch(
      `${this.baseUrl}/cam/comments/article/${articleId}/thread`,
      { headers: { 'X-API-Key': this.apiKey } }
    );
    return response.json();
  }

  async findSimilar(commentText, limit = 5) {
    const params = new URLSearchParams({
      comment_text: commentText,
      limit: limit.toString()
    });
    const response = await fetch(
      `${this.baseUrl}/cam/comments/semantic/similar?${params}`,
      { 
        method: 'POST',
        headers: { 'X-API-Key': this.apiKey } 
      }
    );
    return response.json();
  }
}

// Usage
const comments = new EngramComments('your-api-key', 'http://localhost:8000');

// Store comment
await comments.storeComment('article-123', 'user-456', 'Great article!');

// Get semantic thread
const thread = await comments.getThread('article-123');

// Find similar discussions
const similar = await comments.findSimilar('artificial intelligence');
```

### Python Backend Integration

```python
import httpx
from typing import List, Dict, Optional

class EngramCommentsClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    async def store_comment(
        self, 
        article_id: str, 
        author_id: str, 
        comment_text: str,
        comment_type: str = "root_comment",
        parent_comment_id: Optional[str] = None
    ) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/cam/comments/store",
                json={
                    "article_id": article_id,
                    "author_id": author_id,
                    "comment_text": comment_text,
                    "comment_type": comment_type,
                    "parent_comment_id": parent_comment_id
                },
                headers=self.headers
            )
            return response.json()
    
    async def get_thread(self, article_id: str) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/cam/comments/article/{article_id}/thread",
                headers=self.headers
            )
            return response.json()
    
    async def semantic_search(
        self, 
        comment_text: str, 
        limit: int = 10,
        cross_article: bool = True
    ) -> List[Dict]:
        params = {
            "comment_text": comment_text,
            "limit": limit,
            "cross_article": cross_article
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/cam/comments/semantic/similar",
                params=params,
                headers=self.headers
            )
            return response.json()

# Usage
client = EngramCommentsClient("your-api-key", "http://localhost:8000")

# Store and thread comments
await client.store_comment("article-123", "user-456", "Great insights!")
thread = await client.get_thread("article-123")
similar = await client.semantic_search("machine learning trends")
```

## Best Practices

### 1. Content Moderation

- Enable auto-moderation for toxic content detection
- Use semantic search to find related policy violations
- Implement escalation workflows for complex cases

### 2. Thread Management

- Set appropriate similarity thresholds for your community
- Use cross-article threading to surface related discussions
- Consider reply depth limits for readability

### 3. Agent Integration

- Configure agent personalities for your brand voice
- Use context-aware responses based on thread history
- Implement agent response approval workflows

### 4. Performance Optimization

- Batch comment storage for high-volume sites
- Cache frequently accessed threads
- Use pagination for large comment threads

### 5. Privacy & Compliance

- Implement proper access controls for private comments
- Support comment deletion and right-to-be-forgotten requests
- Audit witness lists for sensitive discussions

## Troubleshooting

### Common Issues

**Comments not threading properly:**
- Check similarity threshold settings
- Verify OpenAI API key is configured
- Ensure vector dimensions are set to 1536

**Semantic search returning no results:**
- Lower the similarity threshold
- Check that embeddings are being generated
- Verify cross-article search is enabled

**Agent responses not generating:**
- Confirm agent is included in witness list
- Check agent configuration and API keys
- Review response generation logs

### Health Checks

Use the admin endpoints to monitor system health:

```bash
# Check system status
curl -X GET "http://localhost:8000/api/v1/admin/status" \
  -H "X-API-Key: your-api-key" \
  -u "admin:your-admin-password"

# Recreate indexes if needed
curl -X POST "http://localhost:8000/api/v1/admin/recreate/indexes" \
  -H "X-API-Key: your-api-key" \
  -u "admin:your-admin-password"
```

## Migration Guide

### From Traditional Comments

1. **Export existing comments** to JSON format
2. **Map comment fields** to engram structure
3. **Batch import** using the store endpoint
4. **Rebuild threads** using semantic reconstruction
5. **Update frontend** to use new API endpoints

### Schema Mapping

```
Traditional Comment -> Comment Engram
===================   ==============
id                 -> memory_id
user_id            -> author_id  
post_id            -> article_id
content            -> comment_text
parent_id          -> parent_comment_id
created_at         -> timestamp
```

## Support & Community

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Full API reference available
- **Examples**: Sample integrations in `/examples` directory
- **Community**: Join our discussions for best practices

---

*Comments-as-Engrams represents a new paradigm in community discussion, where conversations become searchable knowledge and AI agents participate naturally in human discourse.*