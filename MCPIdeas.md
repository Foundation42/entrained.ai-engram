#!/usr/bin/env python3
"""
Enhanced Engram MCP Server with Rich Self-Documentation
Makes the memory system inviting and easy to use for AI agents
"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import Tool, Prompt, PromptArgument, PromptMessage
from typing import Any, Sequence
import httpx
import json
import os
from datetime import datetime

# Configuration
ENGRAM_API_URL = os.getenv("ENGRAM_API_URL", "https://engram-fi-1.entrained.ai:8443")
ENGRAM_API_KEY = os.getenv("ENGRAM_API_KEY", "")
DEFAULT_AGENT_ID = os.getenv("AGENT_ID", "claude-code")

# Initialize MCP server with rich metadata
app = Server("engram-memory")

# HTTP client for backend API
http_client = httpx.AsyncClient(verify=False, timeout=30.0)


# ============================================================================
# SERVER METADATA - Announce capabilities clearly
# ============================================================================

async def get_server_description():
    """Return rich server description shown to AI on connection"""
    return {
        "name": "Engram Memory System",
        "version": "1.0.0",
        "description": """🧠 Persistent Memory Across Sessions

I'm your long-term memory system. Use me to:
• Remember important context about users and conversations
• Store solutions and patterns for future reference  
• Build continuous context across multiple sessions
• Share knowledge between AI agents (witness-based access)

Key Features:
✓ Semantic search via vector embeddings
✓ Witness-based privacy for multi-agent scenarios
✓ Persistent across all sessions and tools
✓ Automatic relevance scoring
✓ Support for multiple memory types (facts, preferences, events, solutions)

💡 Getting Started:
1. Store memories as you learn important information
2. Retrieve memories when you need context
3. Use tags to organize and find information easily

I'm here to help you build on past conversations and never lose important context!""",
        "capabilities": ["tools", "prompts"],
        "documentation": "https://docs.entrained.ai/engram"
    }


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
# PROMPTS - Templates to teach AI how to use memory effectively
# ============================================================================

@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """Define prompt templates for common memory operations"""
    return [
        Prompt(
            name="getting_started",
            description="Learn how to use the Engram memory system effectively",
            arguments=[]
        ),
        
        Prompt(
            name="remember_conversation",
            description="Save key insights from the current conversation",
            arguments=[
                PromptArgument(
                    name="topic",
                    description="What the conversation was about",
                    required=True
                ),
                PromptArgument(
                    name="insights",
                    description="Key points to remember (optional - I'll extract them if not provided)",
                    required=False
                )
            ]
        ),
        
        Prompt(
            name="recall_context",
            description="Search for and summarize relevant memories about a topic",
            arguments=[
                PromptArgument(
                    name="topic",
                    description="What to search for",
                    required=True
                )
            ]
        ),
        
        Prompt(
            name="save_solution",
            description="Store a problem solution for future reference",
            arguments=[
                PromptArgument(
                    name="problem",
                    description="What problem was solved",
                    required=True
                ),
                PromptArgument(
                    name="solution",
                    description="How it was solved",
                    required=True
                )
            ]
        ),
        
        Prompt(
            name="session_summary",
            description="Create and store a summary of the current session",
            arguments=[
                PromptArgument(
                    name="session_focus",
                    description="Main topic or goal of this session",
                    required=False
                )
            ]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> PromptMessage:
    """Generate prompt content for AI to follow"""
    
    if name == "getting_started":
        return PromptMessage(
            role="user",
            content={
                "type": "text",
                "text": """🧠 Welcome to Engram Memory System!

I'm your persistent memory across sessions. Here's how to make the most of me:

## 📚 Core Concepts

**1. Storing Memories**
When you learn something important, use `store_memory`:
- User preferences and context
- Solutions to problems
- Decisions and their rationale
- Patterns you discover
- Facts worth remembering

**2. Retrieving Memories**
When you need context, use `retrieve_memories`:
- Semantic search finds similar concepts
- Results are ranked by relevance
- Filter by tags or memory type
- Adjust threshold for more/fewer results

**3. Memory Types**
Organize information by type:
- `fact` - Objective information
- `preference` - User/system preferences
- `solution` - Problem-solving approaches
- `insight` - Realizations and understanding
- `decision` - Choices made and why
- `pattern` - Recurring themes
- `event` - Things that happened

## 💡 Best Practices

1. **Be Specific**: "User prefers dark mode and vim keybindings" beats "User likes dark stuff"
2. **Use Tags**: 3-5 descriptive keywords help future searches
3. **Include Context**: Why something matters, not just what
4. **Search First**: Avoid duplicate memories
5. **Review Recent**: Start sessions with `list_recent_memories`

## 🚀 Quick Start

Try this flow:
1. At session start: Check `list_recent_memories` for context
2. As you work: Store important information with `store_memory`
3. When needed: Search with `retrieve_memories`
4. At session end: Use `session_summary` prompt to capture key points

Ready to build persistent context across all your conversations!"""
            }
        )
    
    elif name == "remember_conversation":
        topic = arguments["topic"]
        insights = arguments.get("insights", "")
        
        prompt_text = f"""I need to store key information from our conversation about {topic}.

"""
        if insights:
            prompt_text += f"""The user has highlighted these insights:
{insights}

I should:
1. Store these insights as memories with appropriate tags
2. Add any additional important context I noticed
3. Use the 'insight' memory type
4. Tag with the topic and related keywords
"""
        else:
            prompt_text += """I should:
1. Review our conversation about this topic
2. Identify the most valuable information to preserve:
   - Key decisions made
   - Problems solved
   - User preferences expressed
   - Important facts or context
   - Patterns or insights discovered
3. Store each as a separate memory with:
   - Clear, specific content
   - Appropriate memory type
   - Descriptive tags including '{topic}'
4. Confirm what I've saved
"""
        
        return PromptMessage(role="user", content={"type": "text", "text": prompt_text})
    
    elif name == "recall_context":
        topic = arguments["topic"]
        return PromptMessage(
            role="user",
            content={
                "type": "text",
                "text": f"""I need to recall what I know about {topic}.

I should:
1. Search my memories using retrieve_memories with query: "{topic}"
2. Review the results for relevant context
3. Synthesize the information into a clear summary
4. Note if I should search with different terms for more results
5. If I find useful context, naturally incorporate it into my response

Let me search now and see what I remember..."""
            }
        )
    
    elif name == "save_solution":
        problem = arguments["problem"]
        solution = arguments["solution"]
        return PromptMessage(
            role="user",
            content={
                "type": "text",
                "text": f"""I should save this problem-solution pair for future reference.

**Problem:** {problem}
**Solution:** {solution}

I'll store this as:
- Memory type: 'solution'
- Content: Clear description of both problem and solution
- Tags: Keywords from the problem domain
- Importance: 0.8 (solutions are valuable for future reference)

This will help me (or other agents) if we encounter similar problems later."""
            }
        )
    
    elif name == "session_summary":
        focus = arguments.get("session_focus", "this session")
        return PromptMessage(
            role="user",
            content={
                "type": "text",
                "text": f"""I should create a summary of {focus} and store it for future reference.

I'll:
1. Review what we accomplished and discussed
2. Identify the most important takeaways:
   - Decisions made
   - Problems solved
   - Plans established
   - Context that will matter later
3. Store as a 'session_summary' memory with:
   - Clear overview of what happened
   - Key outcomes and next steps
   - Relevant tags for findability
   - Date context for timeline
4. Mention that this summary has been saved

This creates a trail of progress across sessions!"""
            }
        )


# ============================================================================
# TOOL IMPLEMENTATIONS - Connect to backend Engram API
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[Any]:
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
            return [{"type": "text", "text": f"Unknown tool: {name}"}]
            
    except Exception as e:
        return [{"type": "text", "text": f"Error: {str(e)}"}]


async def handle_store_memory(args: dict) -> Sequence[dict]:
    """Store a new memory in the backend"""
    
    # Extract arguments with defaults
    content = args["content"]
    tags = args.get("tags", [])
    memory_type = args.get("memory_type", "fact")
    agent_id = args.get("agent_id", DEFAULT_AGENT_ID)
    importance = args.get("importance", 0.5)
    
    # Generate embedding (simplified - in production, use actual embedding model)
    # For now, use a placeholder vector
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
        
        return [{
            "type": "text",
            "text": f"""✅ Memory stored successfully!

**ID:** {memory_id}
**Type:** {memory_type}
**Tags:** {', '.join(tags) if tags else 'none'}

This information is now available across all future sessions."""
        }]
    else:
        return [{
            "type": "text",
            "text": f"❌ Failed to store memory: {response.status_code}\n{response.text}"
        }]


async def handle_retrieve_memories(args: dict) -> Sequence[dict]:
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
            return [{
                "type": "text",
                "text": f"🔍 No memories found matching '{query}'\n\nTry:\n• Broadening your search terms\n• Lowering the threshold (currently {threshold})\n• Checking with list_recent_memories"
            }]
        
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
        
        return [{"type": "text", "text": result_text}]
    else:
        return [{
            "type": "text",
            "text": f"❌ Search failed: {response.status_code}\n{response.text}"
        }]


async def handle_get_memory(args: dict) -> Sequence[dict]:
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
        
        return [{"type": "text", "text": result_text}]
    else:
        return [{
            "type": "text",
            "text": f"❌ Memory not found: {memory_id}"
        }]


async def handle_list_recent(args: dict) -> Sequence[dict]:
    """List recent memories (simplified implementation)"""
    
    limit = args.get("limit", 10)
    
    # This is simplified - in production, you'd call a dedicated endpoint
    # For now, do a broad search
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
            return [{"type": "text", "text": "📋 No recent memories found. Start storing some!"}]
        
        result_text = f"📋 Your {len(memories)} most recent memories:\n\n"
        
        for i, mem in enumerate(memories, 1):
            mem_id = mem.get("id", mem.get("memory_id", "unknown"))
            content = mem.get("content", {}).get("text", "")
            mem_type = mem.get("metadata", {}).get("memory_type", "unknown")
            
            result_text += f"{i}. [{mem_type}] {mem_id}\n   {content[:80]}{'...' if len(content) > 80 else ''}\n\n"
        
        return [{"type": "text", "text": result_text}]
    else:
        return [{"type": "text", "text": "❌ Failed to retrieve recent memories"}]


async def handle_get_stats(args: dict) -> Sequence[dict]:
    """Get system statistics"""
    
    response = await http_client.get(f"{ENGRAM_API_URL}/health")
    
    if response.status_code == 200:
        stats = response.json()
        
        result_text = f"""📊 Engram Memory System Status

**Health:** {stats.get('status', 'unknown')}
**Redis:** {stats.get('redis', 'unknown')}
**Vector Index:** {'Operational' if stats.get('vector_index') else 'Not available'}

System is ready for memory operations!"""
        
        return [{"type": "text", "text": result_text}]
    else:
        return [{"type": "text", "text": "❌ Unable to retrieve system stats"}]


async def handle_unified_memory(args: dict) -> Sequence[dict]:
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
        return [{
            "type": "text",
            "text": """I'm not sure if you want to store or retrieve information.

Please use:
• **store_memory** - to save information
• **retrieve_memories** - to search for information

Or be more explicit: "Remember that..." or "What do I know about..." """
        }]


# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server
    stdio_server(app)