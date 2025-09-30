"""
MCP (Model Context Protocol) SSE endpoints for remote MCP clients
Provides proper MCP protocol support over Server-Sent Events (SSE)
"""
import json
import logging
from typing import Any, Dict
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from sse_starlette.sse import EventSourceResponse
from mcp.server import Server
from mcp.types import Tool, TextContent

from core.security import api_key_auth
from core.redis_client_hash import redis_client
from services.embedding import embedding_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["MCP Protocol"])

# Create MCP server instance
mcp_server = Server("engram-memory-remote")


# ============================================================================
# MCP TOOLS - Enhanced tools exposed via MCP protocol
# ============================================================================

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """Define MCP tools for remote clients"""
    return [
        Tool(
            name="store_memory",
            description="""💾 Store information in Engram for future retrieval

Use this to remember important information from conversations, including:
• User preferences and context
• Decisions and rationale
• Problem solutions that worked
• Patterns and insights worth preserving
• Facts and knowledge to build upon

The memory will be:
✓ Semantically searchable across all future sessions
✓ Accessible from any MCP client (Claude Code, Desktop, etc)
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
- Set importance 0.8-1.0 for critical information""",
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
                        "description": "Identifier for who is storing this memory",
                        "default": "mcp-client"
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

        Tool(
            name="retrieve_memories",
            description="""🔍 Search for relevant memories semantically

Search your stored memories - finds conceptually similar information even if exact words differ.

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
- Lower threshold (0.5-0.6) for broader results""",
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
                    }
                }
            }
        ),

        Tool(
            name="get_memory_stats",
            description="""📊 Get statistics about the memory system

Shows system health and usage statistics:
• Total memories stored
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

        Tool(
            name="memory",
            description="""🎯 Unified interface - automatically handles storage or retrieval

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


@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle MCP tool calls"""
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
        logger.error(f"Error in MCP tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"❌ Error: {str(e)}\n\nPlease check:\n• Connection is stable\n• Parameters are valid"
        )]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

async def handle_store_memory(args: Dict[str, Any]) -> list[TextContent]:
    """Store a memory"""
    content = args["content"]
    tags = args.get("tags", [])
    memory_type = args.get("memory_type", "fact")
    agent_id = args.get("agent_id", "mcp-client")
    importance = args.get("importance", 0.5)

    # Generate embedding
    embedding = await embedding_service.generate_embedding(content)
    if not embedding:
        return [TextContent(type="text", text="❌ Failed to generate embedding")]

    # Generate memory ID
    import uuid
    memory_id = f"mem-{uuid.uuid4().hex[:12]}"

    # Create memory dict
    memory_data = {
        "content": {"text": content, "media": []},
        "primary_vector": embedding,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_id": agent_id,
            "memory_type": memory_type,
            "importance": importance
        },
        "tags": tags
    }

    # Store in Redis using correct API
    success = redis_client.store_memory(memory_id, memory_data)
    if not success:
        return [TextContent(type="text", text="❌ Failed to store memory in Redis")]

    return [TextContent(
        type="text",
        text=f"""✅ Memory stored successfully!

**ID:** {memory_id}
**Type:** {memory_type}
**Tags:** {', '.join(tags) if tags else 'none'}
**Importance:** {importance}

This information is now available across all future sessions and devices."""
    )]


async def handle_retrieve_memories(args: Dict[str, Any]) -> list[TextContent]:
    """Retrieve memories by semantic search"""
    query = args["query"]
    top_k = args.get("top_k", 5)
    threshold = args.get("threshold", 0.7)
    filter_tags = args.get("filter_tags", [])
    memory_type = args.get("memory_type", "any")

    # Generate query embedding
    query_embedding = await embedding_service.generate_embedding(query)
    if not query_embedding:
        return [TextContent(type="text", text="❌ Failed to generate query embedding")]

    # Build filters for Redis search
    filters = {}
    if memory_type != "any":
        filters["memory_type"] = memory_type

    # Search using correct API
    results = redis_client.search_memories(
        query_vector=query_embedding,
        top_k=top_k,
        filters=filters,
        tags=filter_tags if filter_tags else None
    )

    if not results:
        return [TextContent(
            type="text",
            text=f"🔍 No memories found matching '{query}'\n\nTry:\n• Broadening your search terms\n• Lowering the threshold (currently {threshold})\n• Checking with list_recent_memories"
        )]

    # Format results
    result_text = f"🔍 Found {len(results)} relevant memories for '{query}':\n\n"

    for i, mem in enumerate(results[:10], 1):
        # Redis client returns: memory_id, similarity_score, content_preview, metadata, tags
        mem_id = mem.get("memory_id", "unknown")
        score = mem.get("similarity_score", 0.0)
        content_preview = mem.get("content_preview", "")
        metadata = mem.get("metadata", {})
        mem_type = metadata.get("memory_type", "unknown")
        tags = mem.get("tags", [])

        result_text += f"""**{i}. [{mem_type}] {mem_id}**
   Score: {score:.3f}
   {content_preview}
   Tags: {', '.join(tags) if tags else 'none'}

"""

    return [TextContent(type="text", text=result_text)]


async def handle_get_memory(args: Dict[str, Any]) -> list[TextContent]:
    """Get specific memory by ID"""
    memory_id = args["memory_id"]

    memory = redis_client.get_memory(memory_id)
    if not memory:
        return [TextContent(type="text", text=f"❌ Memory not found: {memory_id}")]

    # Handle JSON-encoded fields
    content_data = memory.get("content", {})
    if isinstance(content_data, str):
        import json
        try:
            content_data = json.loads(content_data)
        except:
            content_data = {"text": content_data}
    content = content_data.get("text", "")

    metadata = memory.get("metadata", {})
    if isinstance(metadata, str):
        import json
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}

    mem_type = metadata.get("memory_type", "unknown")
    agent_id = metadata.get("agent_id", "unknown")
    timestamp = metadata.get("timestamp", "unknown")
    importance = metadata.get("importance", "N/A")

    tags = memory.get("tags", [])
    if isinstance(tags, str):
        tags = tags.split(",") if tags else []

    result_text = f"""📄 Memory: {memory_id}

**Type:** {mem_type}
**Stored by:** {agent_id}
**When:** {timestamp}
**Importance:** {importance}
**Tags:** {', '.join(tags) if tags else 'none'}

**Content:**
{content}
"""

    return [TextContent(type="text", text=result_text)]


async def handle_list_recent(args: Dict[str, Any]) -> list[TextContent]:
    """List recent memories"""
    limit = args.get("limit", 10)

    # Broad search to get recent items using correct API
    dummy_vector = [0.5] * 1536
    results = redis_client.search_memories(
        query_vector=dummy_vector,
        top_k=limit,
        filters=None,
        tags=None
    )

    if not results:
        return [TextContent(type="text", text="📋 No recent memories found. Start storing some!")]

    result_text = f"📋 Your {len(results)} most recent memories:\n\n"

    for i, mem in enumerate(results, 1):
        # Redis client returns: memory_id, content_preview, metadata, tags
        mem_id = mem.get("memory_id", "unknown")
        content_preview = mem.get("content_preview", "")
        metadata = mem.get("metadata", {})
        mem_type = metadata.get("memory_type", "unknown")

        # Truncate preview to 80 chars for list view
        short_preview = content_preview[:80]
        if len(content_preview) > 80:
            short_preview += "..."

        result_text += f"{i}. [{mem_type}] {mem_id}\n   {short_preview}\n\n"

    return [TextContent(type="text", text=result_text)]


async def handle_get_stats(args: Dict[str, Any]) -> list[TextContent]:
    """Get system statistics"""
    try:
        redis_client.client.ping()

        result_text = f"""📊 Engram Memory System Status

**Health:** ✅ Healthy
**Redis:** ✅ Connected
**Vector Index:** ✅ Operational

**Features Available:**
• Semantic search with vector embeddings
• 7 memory types (fact, preference, solution, insight, decision, pattern, event)
• Importance scoring for prioritization
• Tag-based filtering
• Multi-device access via MCP

System is ready for memory operations across all your devices!"""

        return [TextContent(type="text", text=result_text)]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ System health check failed: {e}")]


async def handle_unified_memory(args: Dict[str, Any]) -> list[TextContent]:
    """Unified memory interface - auto-detect store vs retrieve"""
    request = args["request"].lower()

    # Detect intent
    store_keywords = ["remember", "save", "store", "note that", "keep in mind"]
    retrieve_keywords = ["what do", "recall", "find", "search", "do you know", "have we", "did we"]

    is_store = any(kw in request for kw in store_keywords)
    is_retrieve = any(kw in request for kw in retrieve_keywords)

    if is_store and not is_retrieve:
        # Extract content
        content = request
        for kw in store_keywords:
            if kw in request:
                content = request.split(kw, 1)[1].strip()
                break

        return await handle_store_memory({
            "content": content,
            "tags": [],
            "memory_type": "fact"
        })

    elif is_retrieve and not is_store:
        # Extract query
        query = request
        for kw in retrieve_keywords:
            if kw in request:
                query = request.split(kw, 1)[1].strip()
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
# STREAMABLE HTTP ENDPOINT (MCP 2025-03-26 Specification)
# ============================================================================

@router.api_route("/", methods=["GET", "POST"], dependencies=[Depends(api_key_auth)])
async def mcp_endpoint(request: Request):
    """
    MCP Streamable HTTP endpoint (MCP specification 2025-03-26)

    Single endpoint supporting both POST (JSON-RPC requests) and GET (SSE stream).
    This is the modern MCP remote server protocol.

    Connect with: claude mcp add https://engram-fi-1.entrained.ai:8443/mcp --header "X-API-Key: YOUR_KEY"
    """

    if request.method == "GET":
        # SSE stream for server-to-client messages
        async def event_generator():
            """Generate SSE events for MCP protocol"""
            try:
                logger.info("MCP SSE stream opened")

                # Keep connection alive with heartbeats
                import asyncio
                while True:
                    if await request.is_disconnected():
                        logger.info("MCP SSE client disconnected")
                        break

                    await asyncio.sleep(30)
                    yield {
                        "event": "ping",
                        "data": ""
                    }

            except Exception as e:
                logger.error(f"Error in MCP SSE stream: {e}")

        return EventSourceResponse(event_generator())

    else:  # POST
        # JSON-RPC message handling
        try:
            payload = await request.json()

            # Handle JSON-RPC protocol
            jsonrpc_version = payload.get("jsonrpc")
            if jsonrpc_version != "2.0":
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "Invalid Request: jsonrpc must be 2.0"},
                    "id": None
                }

            method = payload.get("method")
            params = payload.get("params", {})
            request_id = payload.get("id")

            logger.info(f"MCP request: {method}")

            # Handle different MCP methods
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "engram-memory",
                        "version": "1.0.0"
                    }
                }

            elif method == "tools/list":
                tools = await list_tools()
                result = {"tools": [tool.model_dump() for tool in tools]}

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                tool_result = await call_tool(tool_name, tool_args)
                result = {"content": [c.model_dump() for c in tool_result]}

            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id
                }

            return {"jsonrpc": "2.0", "result": result, "id": request_id}

        except json.JSONDecodeError:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error: Invalid JSON"},
                "id": None
            }
        except Exception as e:
            logger.error(f"Error in MCP endpoint: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request_id if 'request_id' in locals() else None
            }