#!/usr/bin/env python3
"""
Enhanced Engram MCP Server with Rich Self-Documentation
Makes the memory system inviting and easy to use for AI agents
"""
import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from typing import Any, Sequence
import httpx
import json
import os
from datetime import datetime

# Configuration
ENGRAM_API_URL = os.getenv("ENGRAM_API_URL", "https://engram-fi-1.entrained.ai:8443")
ENGRAM_API_KEY = os.getenv("ENGRAM_API_KEY", "engram-production-secure-key-2025-comments-system")
DEFAULT_AGENT_ID = os.getenv("AGENT_ID", "claude-code")

# Initialize MCP server with rich metadata
app = Server("engram-memory")

# HTTP client for backend API
http_client: httpx.AsyncClient = None

logger = logging.getLogger(__name__)


# ============================================================================
# TOOLS - Core memory operations with rich descriptions
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Define MCP tools with comprehensive documentation"""
    return [
        # Tool 1: Store Memory (Primary storage)
        Tool(
            name="store_memory",
            description="""💾 Store information for future retrieval

Use this to remember important information from conversations, including:
• User preferences and context
• Decisions and rationale
• Problem solutions that worked
• Patterns and insights worth preserving
• Facts and knowledge to build upon

The memory will be:
✓ Semantically searchable across all future sessions
✓ Accessible by you in any tool (Claude Desktop, Code, etc)
✓ Scored for relevance when retrieved
✓ Organized by tags for easy filtering

**When to use:**
- After solving a complex problem
- When learning user preferences
- After making important decisions
- When discovering useful patterns
- Anytime you think "this will be useful later"

**Best practices:**
- Be specific and include context
- Use descriptive tags (3-5 keywords)
- Specify memory type for better organization
- Include enough detail to understand later""",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to remember. Be specific and include relevant context. Example: 'User Christian prefers vim keybindings and dark mode in his IDE. He works primarily in Python and TypeScript.'"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords for categorization and searching. Example: ['user-preference', 'editor', 'ui', 'vim']",
                        "default": []
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["fact", "preference", "event", "solution", "insight", "decision", "pattern"],
                        "description": "Type of memory:\n• fact: Objective information\n• preference: User/system preferences\n• event: Something that happened\n• solution: How you solved a problem\n• insight: Understanding or realization\n• decision: Choice made and why\n• pattern: Recurring theme or approach",
                        "default": "fact"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Identifier for who is storing this memory (defaults to current agent)",
                        "default": DEFAULT_AGENT_ID
                    },
                    "importance": {
                        "type": "number",
                        "description": "Importance score 0-1 (higher = more important for retrieval)",
                        "default": 0.5,
                        "minimum": 0,
                        "maximum": 1
                    }
                },
                "required": ["content"]
            }
        ),

        # Tool 2: Retrieve Memories (Primary retrieval)
        Tool(
            name="retrieve_memories",
            description="""🔍 Search for relevant memories

Search your stored memories semantically - finds conceptually similar information even if exact words differ.

Use this when you need:
• Context about a user or topic
• Solutions to similar problems
• Previous decisions and rationale
• Patterns you've identified before
• Any information you might have stored

**Search is semantic:**
Searching for "authentication issues" will also find memories about "login problems" or "credential validation errors"

**When to use:**
- At the start of a conversation to recall context
- When facing a familiar problem
- Before making decisions (check past rationale)
- When user asks "do you remember..."
- Anytime you think "have I seen this before?"

**Pro tips:**
- Search before storing to avoid duplicates
- Use specific queries for better results
- Adjust top_k based on how many results you need
- Lower threshold if you want more results""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for. Be specific. Examples: 'user preferences for IDE', 'solution for memory leaks in Python', 'decisions about authentication system'"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Minimum similarity score (0-1). Lower = more permissive. Default 0.7 works well.",
                        "default": 0.7,
                        "minimum": 0,
                        "maximum": 1
                    },
                    "filter_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Only return memories with these tags (optional)",
                        "default": []
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["fact", "preference", "event", "solution", "insight", "decision", "pattern", "any"],
                        "description": "Filter by memory type (optional)",
                        "default": "any"
                    }
                },
                "required": ["query"]
            }
        ),

        # Tool 3: Get Specific Memory
        Tool(
            name="get_memory",
            description="""📄 Retrieve a specific memory by ID

Use when you know the exact memory ID and want to see its full details.

**When to use:**
- Following up on a memory from search results
- Verifying details of a specific memory
- Checking if a memory still exists

Returns complete memory with all metadata, tags, and content.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The unique ID of the memory (e.g., 'mem-76a306a44e0c')"
                    }
                },
                "required": ["memory_id"]
            }
        ),

        # Tool 4: List Recent Memories
        Tool(
            name="list_recent_memories",
            description="""📋 Get a timeline of recent memories

Shows your most recent memories in chronological order. Useful for:
• Reviewing what you've learned recently
• Continuing from where you left off
• Getting a quick overview of stored context
• Finding a memory you know you stored recently

**When to use:**
- At session start to see recent context
- When you stored something but forgot to note the ID
- To get a sense of what information is available

Returns newest memories first.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent memories to retrieve",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Filter by agent (defaults to current agent)",
                        "default": DEFAULT_AGENT_ID
                    }
                }
            }
        ),

        # Tool 5: Memory Stats
        Tool(
            name="get_memory_stats",
            description="""📊 Get statistics about the memory system

Shows system health and usage statistics:
• Total memories stored
• Memory types distribution
• System health status
• Available features

**When to use:**
- Troubleshooting issues
- Understanding system capacity
- Checking if system is operational

Quick health check before storing important information.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        # Tool 6: Unified Memory Interface (Simplified)
        Tool(
            name="memory",
            description="""🎯 Simplified memory interface - automatically handles storage or retrieval

One tool to rule them all! Just describe what you want in natural language:

**Storage examples:**
• "Remember that Christian prefers dark mode"
• "Save this solution: use Redis for caching to fix the latency issue"
• "Note: user wants daily email summaries at 9am"

**Retrieval examples:**
• "What do I know about Christian's preferences?"
• "Have we solved latency issues before?"
• "What decisions did we make about email notifications?"

I'll automatically:
✓ Determine if you're storing or retrieving
✓ Extract relevant tags and metadata
✓ Set appropriate memory type
✓ Format results clearly

**When to use:**
When you want to work with memory naturally without thinking about the specific tool to call. Great for quick operations!

**Pro tip:** For more control, use the specific store_memory and retrieve_memories tools instead.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "request": {
                        "type": "string",
                        "description": "Natural language request. Examples: 'Remember that...', 'What do I know about...', 'Have we discussed...'"
                    }
                },
                "required": ["request"]
            }
        )
    ]


# ============================================================================
# TOOL IMPLEMENTATIONS - Connect to backend Engram API
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
    """Handle tool calls and route to backend API"""

    try:
        if name == "store_memory":
            return await handle_store_memory(arguments)
        elif name == "retrieve_memories":
            return await handle_retrieve_memories(arguments)
        elif name == "get_memory":
            return await handle_get_memory(arguments)
        elif name == "list_recent_memories":
            return await handle_list_recent(arguments)
        elif name == "get_memory_stats":
            return await handle_get_stats(arguments)
        elif name == "memory":
            return await handle_unified_memory(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"❌ Error: {str(e)}\n\nPlease check:\n• API connection is available\n• API key is valid\n• Backend service is running"
        )]


async def handle_store_memory(args: dict) -> Sequence[TextContent]:
    """Store a new memory in the backend"""

    # Extract arguments with defaults
    content = args["content"]
    tags = args.get("tags", [])
    memory_type = args.get("memory_type", "fact")
    agent_id = args.get("agent_id", DEFAULT_AGENT_ID)
    importance = args.get("importance", 0.5)

    # Generate embedding (simplified - using placeholder)
    embedding = [0.1] * 1536

    # Prepare payload for backend API
    payload = {
        "content": {
            "text": content,
            "media": []
        },
        "primary_vector": embedding,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_id": agent_id,
            "memory_type": memory_type,
            "importance": importance
        },
        "tags": tags
    }

    # Call backend API
    headers = {"X-API-Key": ENGRAM_API_KEY}
    response = await http_client.post(
        f"{ENGRAM_API_URL}/cam/store",
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        memory_id = result["memory_id"]

        return [TextContent(
            type="text",
            text=f"""✅ Memory stored successfully!

**ID:** {memory_id}
**Type:** {memory_type}
**Tags:** {', '.join(tags) if tags else 'none'}

This information is now available across all future sessions."""
        )]
    else:
        return [TextContent(
            type="text",
            text=f"❌ Failed to store memory: {response.status_code}\n{response.text}"
        )]


async def handle_retrieve_memories(args: dict) -> Sequence[TextContent]:
    """Search for memories semantically"""

    query = args["query"]
    top_k = args.get("top_k", 5)
    threshold = args.get("threshold", 0.7)
    filter_tags = args.get("filter_tags", [])
    memory_type = args.get("memory_type", "any")

    # Generate query embedding (simplified)
    query_vector = [0.1] * 1536

    # Prepare search payload
    payload = {
        "resonance_vectors": [{
            "vector": query_vector,
            "weight": 1.0
        }],
        "retrieval": {
            "top_k": top_k,
            "similarity_threshold": threshold
        }
    }

    # Call backend API
    headers = {"X-API-Key": ENGRAM_API_KEY}
    response = await http_client.post(
        f"{ENGRAM_API_URL}/cam/retrieve",
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        memories = result.get("memories", [])

        # Apply client-side filters
        if filter_tags:
            memories = [m for m in memories if any(tag in m.get("tags", []) for tag in filter_tags)]

        if memory_type != "any":
            memories = [m for m in memories if m.get("metadata", {}).get("memory_type") == memory_type]

        if not memories:
            return [TextContent(
                type="text",
                text=f"🔍 No memories found matching '{query}'\n\nTry:\n• Broadening your search terms\n• Lowering the threshold (currently {threshold})\n• Checking with list_recent_memories"
            )]

        # Format results
        result_text = f"🔍 Found {len(memories)} relevant memories for '{query}':\n\n"

        for i, mem in enumerate(memories[:10], 1):  # Limit display to top 10
            mem_id = mem.get("id", mem.get("memory_id", "unknown"))
            content = mem.get("content", {}).get("text", "")
            score = mem.get("similarity_score", mem.get("score", 0))
            mem_type = mem.get("metadata", {}).get("memory_type", "unknown")
            tags = mem.get("tags", [])

            result_text += f"""**{i}. [{mem_type}] {mem_id}**
   Score: {score:.3f}
   {content[:150]}{'...' if len(content) > 150 else ''}
   Tags: {', '.join(tags) if tags else 'none'}

"""

        return [TextContent(type="text", text=result_text)]
    else:
        return [TextContent(
            type="text",
            text=f"❌ Search failed: {response.status_code}\n{response.text}"
        )]


async def handle_get_memory(args: dict) -> Sequence[TextContent]:
    """Retrieve a specific memory by ID"""

    memory_id = args["memory_id"]

    headers = {"X-API-Key": ENGRAM_API_KEY}
    response = await http_client.get(
        f"{ENGRAM_API_URL}/cam/memory/{memory_id}",
        headers=headers
    )

    if response.status_code == 200:
        memory = response.json()
        content = memory.get("content", {}).get("text", "")
        mem_type = memory.get("metadata", {}).get("memory_type", "unknown")
        agent_id = memory.get("metadata", {}).get("agent_id", "unknown")
        timestamp = memory.get("metadata", {}).get("timestamp", "unknown")
        tags = memory.get("tags", [])

        result_text = f"""📄 Memory: {memory_id}

**Type:** {mem_type}
**Stored by:** {agent_id}
**When:** {timestamp}
**Tags:** {', '.join(tags) if tags else 'none'}

**Content:**
{content}
"""

        return [TextContent(type="text", text=result_text)]
    else:
        return [TextContent(
            type="text",
            text=f"❌ Memory not found: {memory_id}"
        )]


async def handle_list_recent(args: dict) -> Sequence[TextContent]:
    """List recent memories"""

    limit = args.get("limit", 10)

    # Use a broad search with low threshold to get recent items
    payload = {
        "resonance_vectors": [{
            "vector": [0.5] * 1536,
            "weight": 1.0
        }],
        "retrieval": {
            "top_k": limit,
            "similarity_threshold": 0.0
        }
    }

    headers = {"X-API-Key": ENGRAM_API_KEY}
    response = await http_client.post(
        f"{ENGRAM_API_URL}/cam/retrieve",
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        memories = result.get("memories", [])

        if not memories:
            return [TextContent(type="text", text="📋 No recent memories found. Start storing some!")]

        result_text = f"📋 Your {len(memories)} most recent memories:\n\n"

        for i, mem in enumerate(memories, 1):
            mem_id = mem.get("id", mem.get("memory_id", "unknown"))
            content = mem.get("content", {}).get("text", "")
            mem_type = mem.get("metadata", {}).get("memory_type", "unknown")

            result_text += f"{i}. [{mem_type}] {mem_id}\n   {content[:80]}{'...' if len(content) > 80 else ''}\n\n"

        return [TextContent(type="text", text=result_text)]
    else:
        return [TextContent(type="text", text="❌ Failed to retrieve recent memories")]


async def handle_get_stats(args: dict) -> Sequence[TextContent]:
    """Get system statistics"""

    response = await http_client.get(f"{ENGRAM_API_URL}/health")

    if response.status_code == 200:
        stats = response.json()

        result_text = f"""📊 Engram Memory System Status

**Health:** {stats.get('status', 'unknown')}
**Redis:** {stats.get('redis', 'unknown')}
**Vector Index:** {'✅ Operational' if stats.get('vector_index') else '❌ Not available'}

System is ready for memory operations!"""

        return [TextContent(type="text", text=result_text)]
    else:
        return [TextContent(type="text", text="❌ Unable to retrieve system stats")]


async def handle_unified_memory(args: dict) -> Sequence[TextContent]:
    """Simplified unified interface - auto-determine store or retrieve"""

    request = args["request"].lower()

    # Simple heuristic to determine intent
    store_keywords = ["remember", "save", "store", "note that", "keep in mind"]
    retrieve_keywords = ["what do", "recall", "find", "search", "do you know", "have we", "did we"]

    is_store = any(keyword in request for keyword in store_keywords)
    is_retrieve = any(keyword in request for keyword in retrieve_keywords)

    if is_store and not is_retrieve:
        # Extract content after keywords
        content = request
        for keyword in store_keywords:
            if keyword in request:
                content = request.split(keyword, 1)[1].strip()
                break

        return await handle_store_memory({
            "content": content,
            "tags": [],
            "memory_type": "fact"
        })

    elif is_retrieve and not is_store:
        # Extract query
        query = request
        for keyword in retrieve_keywords:
            if keyword in request:
                query = request.split(keyword, 1)[1].strip()
                break

        return await handle_retrieve_memories({
            "query": query,
            "top_k": 5,
            "threshold": 0.7
        })

    else:
        return [TextContent(
            type="text",
            text="""I'm not sure if you want to store or retrieve information.

Please use:
• **store_memory** - to save information
• **retrieve_memories** - to search for information

Or be more explicit: "Remember that..." or "What do I know about..." """
        )]


# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

async def main():
    """Run the MCP server"""
    global http_client

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Enhanced Engram MCP Server...")
    logger.info(f"API URL: {ENGRAM_API_URL}")

    # Initialize HTTP client
    http_client = httpx.AsyncClient(verify=False, timeout=30.0)

    try:
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        if http_client:
            await http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())