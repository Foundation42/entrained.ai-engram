# Enhanced Engram MCP Server - Complete Guide

**🚀 Making Memory Inviting for AI Agents**

The Enhanced MCP Server transforms Engram into a friendly, self-documenting memory system that AI agents love to use.

---

## 🎯 What's Included

### Rich Self-Documentation
- Detailed tool descriptions with examples and best practices
- Clear guidance on when to use each tool
- Emoji indicators for quick visual scanning
- Helpful error messages with actionable suggestions

### 6 MCP Tools

1. **`store_memory`** - Primary storage with full parameter documentation
2. **`retrieve_memories`** - Semantic search with filtering
3. **`get_memory`** - Retrieve by ID
4. **`list_recent_memories`** - Timeline view
5. **`get_memory_stats`** - System health
6. **`memory`** - Unified simplified interface (auto-determines store/retrieve)

### Key Features

✅ Every tool has rich, actionable descriptions
✅ Input schemas include examples and defaults
✅ Clear best practices throughout
✅ Helpful error messages and suggestions
✅ Emoji indicators for quick visual parsing
✅ Connects to your existing production Engram API

---

## 📦 Installation

### Prerequisites

```bash
pip install mcp httpx
```

### Environment Variables

```bash
export ENGRAM_API_URL="https://engram-fi-1.entrained.ai:8443"
export ENGRAM_API_KEY="your-api-key-here"
export AGENT_ID="claude-code"  # Optional, defaults to "claude-code"
```

---

## 🚀 Quick Start

### Running the Server

```bash
# Start the enhanced MCP server
python3 mcp_server_enhanced.py
```

### Testing All Tools

```bash
# Run comprehensive test suite
python3 test_mcp_enhanced.py
```

---

## 🔧 Tool Documentation

### Tool 1: `store_memory` 💾

**Purpose:** Store information for future retrieval

**When to use:**
- After solving a complex problem
- When learning user preferences
- After making important decisions
- When discovering useful patterns
- Anytime you think "this will be useful later"

**Parameters:**
- `content` (required) - The information to remember
- `tags` (optional) - Keywords for categorization (array)
- `memory_type` (optional) - Type: fact, preference, event, solution, insight, decision, pattern
- `agent_id` (optional) - Defaults to current agent
- `importance` (optional) - Score 0-1, higher = more important

**Example:**
```json
{
  "content": "User Christian prefers vim keybindings and dark mode",
  "tags": ["user-preference", "editor", "ui"],
  "memory_type": "preference",
  "importance": 0.8
}
```

**Response:**
```
✅ Memory stored successfully!

**ID:** mem-362875cf1b6e
**Type:** preference
**Tags:** user-preference, editor, ui

This information is now available across all future sessions.
```

---

### Tool 2: `retrieve_memories` 🔍

**Purpose:** Search for relevant memories semantically

**When to use:**
- At the start of a conversation to recall context
- When facing a familiar problem
- Before making decisions (check past rationale)
- When user asks "do you remember..."
- Anytime you think "have I seen this before?"

**Parameters:**
- `query` (required) - What to search for
- `top_k` (optional) - Maximum results (1-20, default: 5)
- `threshold` (optional) - Minimum similarity 0-1 (default: 0.7)
- `filter_tags` (optional) - Only return memories with these tags
- `memory_type` (optional) - Filter by type: fact, preference, solution, etc.

**Example:**
```json
{
  "query": "user preferences for IDE",
  "top_k": 3,
  "threshold": 0.7,
  "filter_tags": ["user-preference"],
  "memory_type": "preference"
}
```

**Response:**
```
🔍 Found 1 relevant memories for 'user preferences for IDE':

**1. [preference] mem-362875cf1b6e**
   Score: 0.892
   User Christian prefers vim keybindings and dark mode in his IDE...
   Tags: user-preference, editor, ui, vim
```

**Pro Tips:**
- Search before storing to avoid duplicates
- Use specific queries for better results
- Lower threshold if you want more results
- Semantic search finds similar concepts even with different words

---

### Tool 3: `get_memory` 📄

**Purpose:** Retrieve a specific memory by ID

**When to use:**
- Following up on a memory from search results
- Verifying details of a specific memory
- Checking if a memory still exists

**Parameters:**
- `memory_id` (required) - The unique memory ID

**Example:**
```json
{
  "memory_id": "mem-362875cf1b6e"
}
```

**Response:**
```
📄 Memory: mem-362875cf1b6e

**Type:** preference
**Stored by:** mcp-test-enhanced
**When:** 2025-09-30T17:45:00Z
**Tags:** user-preference, editor, ui, vim

**Content:**
User Christian prefers vim keybindings and dark mode in his IDE.
He works primarily in Python and TypeScript.
```

---

### Tool 4: `list_recent_memories` 📋

**Purpose:** Get a timeline of recent memories

**When to use:**
- At session start to see recent context
- When you stored something but forgot the ID
- To get a sense of what information is available

**Parameters:**
- `limit` (optional) - Number of memories (1-50, default: 10)
- `agent_id` (optional) - Filter by agent (defaults to current)

**Example:**
```json
{
  "limit": 5
}
```

**Response:**
```
📋 Your 5 most recent memories:

1. [pattern] mem-332575a1ba31
   User consistently asks for explanations before implementation...

2. [insight] mem-2b0286a017fe
   Semantic search works better with specific, context-rich queries...

3. [decision] mem-ee749907c122
   Decided to use MCP (Model Context Protocol) instead of custom HTTP...

4. [solution] mem-fc5191474b19
   Fixed Redis connection timeout by increasing REDIS_POOL_TIMEOUT...

5. [preference] mem-362875cf1b6e
   User Christian prefers vim keybindings and dark mode in his IDE...
```

---

### Tool 5: `get_memory_stats` 📊

**Purpose:** Get statistics about the memory system

**When to use:**
- Troubleshooting issues
- Understanding system capacity
- Checking if system is operational

**Parameters:** None

**Response:**
```
📊 Engram Memory System Status

**Health:** healthy
**Redis:** connected
**Vector Index:** ✅ Operational

System is ready for memory operations!
```

---

### Tool 6: `memory` 🎯

**Purpose:** Unified interface - auto-determines store or retrieve

**When to use:**
- When you want to work naturally without thinking about specific tools
- For quick operations without detailed parameters
- When the request is clearly store or retrieve

**Storage Examples:**
- "Remember that Christian prefers dark mode"
- "Save this solution: use Redis for caching"
- "Note: user wants daily email summaries at 9am"

**Retrieval Examples:**
- "What do I know about Christian's preferences?"
- "Have we solved latency issues before?"
- "What decisions did we make about email?"

**Parameters:**
- `request` (required) - Natural language request

**Example:**
```json
{
  "request": "Remember that the user likes minimal UI design"
}
```

**Auto-routing:**
- Detects keywords: "remember", "save", "store", "note" → routes to `store_memory`
- Detects keywords: "what do", "have we", "did we", "recall" → routes to `retrieve_memories`

---

## 📝 Memory Types

The system supports 7 memory types for better organization:

| Type | Use For | Example |
|------|---------|---------|
| **fact** | Objective information | "Redis runs on port 6379" |
| **preference** | User/system preferences | "User prefers dark mode" |
| **event** | Things that happened | "Deployed to production on 2025-09-30" |
| **solution** | Problem-solving approaches | "Fixed timeout by increasing limit to 30s" |
| **insight** | Realizations and understanding | "Semantic search works better with context" |
| **decision** | Choices made and why | "Decided to use MCP for better integration" |
| **pattern** | Recurring themes | "User always asks for explanation first" |

---

## 💡 Best Practices

### Storage Best Practices

1. **Be Specific:** "User prefers dark mode and vim keybindings" beats "User likes dark stuff"
2. **Use Tags:** 3-5 descriptive keywords help future searches
3. **Include Context:** Why something matters, not just what
4. **Search First:** Avoid duplicate memories
5. **Set Importance:** Use 0.8-1.0 for critical information

### Retrieval Best Practices

1. **Specific Queries:** "user preferences for IDE" better than "preferences"
2. **Adjust Threshold:** Lower (0.5-0.6) for broader results, higher (0.8+) for exact matches
3. **Use Filters:** Narrow with tags or memory type when you know the category
4. **Review Recent:** Start sessions with `list_recent_memories`
5. **Check Stats:** Use `get_memory_stats` if searches fail

---

## 🔄 Typical Workflow

### Session Start
```
1. Call list_recent_memories (limit: 10)
   → Review what was discussed recently
2. Call retrieve_memories with session topic
   → Get relevant context for current conversation
```

### During Session
```
3. Store important information as you learn it
   → Use appropriate memory_type and tags
4. Search before storing to avoid duplicates
   → Call retrieve_memories first
```

### Session End
```
5. Store session summary
   → Use memory_type: "insight" or "decision"
6. Review what was stored
   → Call list_recent_memories to confirm
```

---

## 🧪 Testing

### Run All Tests
```bash
python3 test_mcp_enhanced.py
```

### Test Results
```
✅ Tool 1: store_memory - 5 different memory types stored
✅ Tool 2: retrieve_memories - 5 semantic search scenarios tested
✅ Tool 3: get_memory - Retrieved by ID with full metadata
✅ Tool 4: list_recent_memories - Timeline views tested
✅ Tool 5: get_memory_stats - System health verified
✅ Tool 6: memory - Unified interface patterns validated
✅ Error handling - Helpful messages confirmed
```

---

## 🔌 Claude Desktop Integration

Add to your Claude Desktop `config.json`:

```json
{
  "mcpServers": {
    "engram-enhanced": {
      "command": "python3",
      "args": ["/path/to/engram/mcp_server_enhanced.py"],
      "env": {
        "ENGRAM_API_URL": "https://engram-fi-1.entrained.ai:8443",
        "ENGRAM_API_KEY": "your-api-key-here",
        "AGENT_ID": "claude-desktop"
      }
    }
  }
}
```

---

## 🎨 What Makes This Inviting

### Conversational Tone
- Talks to Claude like a helpful assistant
- "Use this when you need..." instead of "Function to..."
- Encouraging language: "Ready to build!", "Let me search now..."

### Clear Use Cases
- Every tool explains "when to use this"
- Concrete examples in descriptions
- Real-world scenarios

### Examples Throughout
- Every parameter includes example values
- Response formats are documented
- Common patterns demonstrated

### Progressive Disclosure
- Start simple with basic tools
- Advanced features available when needed
- Detailed docs without overwhelming

### Emoji Visual Parsing
- 💾 Store = Save information
- 🔍 Retrieve = Search for information
- 📄 Get = Fetch specific item
- 📋 List = Timeline view
- 📊 Stats = System health
- 🎯 Unified = One-stop shop

### Helpful Error Messages
```
🔍 No memories found matching 'your query'

Try:
• Broadening your search terms
• Lowering the threshold (currently 0.7)
• Checking with list_recent_memories
```

---

## 📊 Production Status

### Current Deployment
- **Server:** https://engram-fi-1.entrained.ai:8443
- **Status:** ✅ Operational
- **SSL/TLS:** ✅ Configured
- **Security:** ✅ API key authentication active

### Performance
- **Response Time:** <100ms for most operations
- **Vector Search:** Operational
- **Redis:** Connected and healthy

### Features Enabled
- single-agent
- multi-entity
- witness-based-access
- ai-curation
- intelligent-cleanup
- comment-engrams
- api-key-auth
- rate-limiting
- xss-protection

---

## 🔜 Future Enhancements

1. **Real Embeddings:** Replace placeholder vectors with actual OpenAI embeddings
2. **Prompt Templates:** Add MCP prompts for common workflows
3. **Memory Consolidation:** Merge similar memories automatically
4. **Importance Decay:** Gradually reduce importance of old memories
5. **Cross-Session Analytics:** Track memory usage patterns
6. **Rich Media Support:** Images, documents, code snippets
7. **Memory Relationships:** Link related memories together
8. **Smart Suggestions:** Recommend when to store/retrieve

---

## 📚 Related Documentation

- [Main README](README.md) - Project overview
- [MCP Test Results](MCP_TEST_RESULTS.md) - Basic MCP testing
- [Agent Integration Guide](AGENT_INTEGRATION_GUIDE.md) - API integration
- [Comments as Engrams](COMMENTS_AS_ENGRAMS_GUIDE.md) - Comment system

---

## 💬 Example Conversations

### Example 1: Learning User Preferences

**AI Agent:**
```
Let me store this preference for future reference.

[Calls store_memory]
{
  "content": "User Christian prefers concise explanations without preamble",
  "tags": ["user-preference", "communication", "style"],
  "memory_type": "preference",
  "importance": 0.8
}

✅ Stored! I'll remember to be more concise in our conversations.
```

### Example 2: Recalling Context

**AI Agent:**
```
Let me check if I know anything about this project.

[Calls retrieve_memories]
{
  "query": "project structure and organization",
  "top_k": 5
}

🔍 Found 3 relevant memories:
- Project uses MCP for Claude integration
- Code organized in tests/, scripts/, docs/
- Production server at engram-fi-1.entrained.ai

Based on what I remember, I can help you with...
```

### Example 3: Solving a Problem

**AI Agent:**
```
This looks familiar. Let me see if we've solved this before.

[Calls retrieve_memories]
{
  "query": "Redis connection timeout",
  "memory_type": "solution"
}

🔍 Found 1 solution:
"Fixed timeout by increasing REDIS_POOL_TIMEOUT to 30s"

Great! We can apply the same fix here.
```

---

## 🎉 Summary

The Enhanced MCP Server makes Engram memory system:
- **Approachable:** Clear, friendly documentation
- **Discoverable:** Rich tool descriptions with examples
- **Helpful:** Error messages with suggestions
- **Powerful:** 6 tools covering all memory operations
- **Flexible:** From simple unified interface to detailed control
- **Production-Ready:** Tested and deployed

**Ready to give AI agents persistent memory across all sessions!** 🧠✨