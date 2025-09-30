"""
MCP (Model Context Protocol) Server for Engram
Exposes Engram memory operations through MCP for integration with Claude and other AI tools
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    raise ImportError(
        "MCP SDK not installed. Install with: pip install mcp"
    )

from core.config import settings
from core.redis_client_hash import redis_client
from services.embedding import embedding_service
from models.memory import Memory, MemoryContent, MemoryMetadata
from models.retrieval import ResonanceVector, RetrievalRequest, RetrievalConfig

logger = logging.getLogger(__name__)

# Create MCP server instance
app = Server("engram-mcp-server")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available Engram tools for MCP clients"""
    return [
        Tool(
            name="store_memory",
            description="Store a new memory in Engram with semantic vector embedding",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The memory text content to store"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "ID of the agent storing this memory"
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "Type of memory (e.g., conversation, insight, fact)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to categorize the memory",
                        "default": []
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for isolation",
                        "default": None
                    }
                },
                "required": ["text", "agent_id", "memory_type"]
            }
        ),
        Tool(
            name="retrieve_memories",
            description="Retrieve semantically similar memories from Engram",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query text to find similar memories"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of memories to retrieve",
                        "default": 5
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score (0-1)",
                        "default": 0.7
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Filter by agent ID",
                        "default": None
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Filter by session ID",
                        "default": None
                    },
                    "memory_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by memory types",
                        "default": None
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_memory",
            description="Get a specific memory by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The ID of the memory to retrieve"
                    }
                },
                "required": ["memory_id"]
            }
        ),
        Tool(
            name="search_by_tags",
            description="Search memories by tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to search for"
                    },
                    "match_all": {
                        "type": "boolean",
                        "description": "Whether all tags must match (AND) or any tag (OR)",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10
                    }
                },
                "required": ["tags"]
            }
        ),
        Tool(
            name="get_stats",
            description="Get statistics about stored memories",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Filter stats by agent ID",
                        "default": None
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls from MCP clients"""
    
    try:
        if name == "store_memory":
            return await store_memory_tool(arguments)
        elif name == "retrieve_memories":
            return await retrieve_memories_tool(arguments)
        elif name == "get_memory":
            return await get_memory_tool(arguments)
        elif name == "search_by_tags":
            return await search_by_tags_tool(arguments)
        elif name == "get_stats":
            return await get_stats_tool(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def store_memory_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Store a memory through MCP"""
    try:
        # Generate embedding for the text
        embedding = await embedding_service.generate_embedding(args["text"])
        if not embedding:
            return [TextContent(type="text", text="Error: Failed to generate embedding")]
        
        # Create memory object
        content = MemoryContent(text=args["text"], media=[])
        metadata = MemoryMetadata(
            timestamp=datetime.utcnow(),
            agent_id=args["agent_id"],
            memory_type=args["memory_type"],
            session_id=args.get("session_id")
        )
        
        memory = Memory(
            content=content,
            primary_vector=embedding,
            metadata=metadata,
            tags=args.get("tags", [])
        )
        
        # Store in Redis
        redis_client.store_memory(memory)
        
        return [TextContent(
            type="text",
            text=f"Memory stored successfully with ID: {memory.id}"
        )]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error storing memory: {str(e)}")]


async def retrieve_memories_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Retrieve memories through MCP"""
    try:
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(args["query"])
        if not query_embedding:
            return [TextContent(type="text", text="Error: Failed to generate query embedding")]
        
        # Build retrieval request
        resonance_vector = ResonanceVector(vector=query_embedding, weight=1.0)
        config = RetrievalConfig(
            top_k=args.get("top_k", 5),
            similarity_threshold=args.get("similarity_threshold", 0.7)
        )
        
        # Retrieve memories from Redis
        results = redis_client.search_similar_memories(
            query_vector=query_embedding,
            top_k=config.top_k,
            similarity_threshold=config.similarity_threshold,
            session_id=args.get("session_id"),
            agent_id=args.get("agent_id")
        )
        
        # Format results
        if not results:
            return [TextContent(type="text", text="No matching memories found")]
        
        response_text = f"Found {len(results)} matching memories:\n\n"
        for i, mem in enumerate(results, 1):
            response_text += f"{i}. [Score: {mem.get('similarity_score', 0):.3f}]\n"
            response_text += f"   ID: {mem.get('id', 'unknown')}\n"
            response_text += f"   Content: {mem.get('content', {}).get('text', 'N/A')[:200]}...\n"
            response_text += f"   Agent: {mem.get('metadata', {}).get('agent_id', 'unknown')}\n\n"
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error retrieving memories: {str(e)}")]


async def get_memory_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Get a specific memory by ID through MCP"""
    try:
        memory = redis_client.get_memory(args["memory_id"])
        if not memory:
            return [TextContent(type="text", text=f"Memory not found: {args['memory_id']}")]
        
        response_text = f"Memory ID: {memory.get('id')}\n"
        response_text += f"Content: {memory.get('content', {}).get('text', 'N/A')}\n"
        response_text += f"Agent: {memory.get('metadata', {}).get('agent_id', 'unknown')}\n"
        response_text += f"Type: {memory.get('metadata', {}).get('memory_type', 'unknown')}\n"
        response_text += f"Tags: {', '.join(memory.get('tags', []))}\n"
        response_text += f"Created: {memory.get('metadata', {}).get('timestamp', 'unknown')}\n"
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting memory: {str(e)}")]


async def search_by_tags_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Search memories by tags through MCP"""
    try:
        results = redis_client.search_by_tags(
            tags=args["tags"],
            match_all=args.get("match_all", False),
            limit=args.get("limit", 10)
        )
        
        if not results:
            return [TextContent(type="text", text="No memories found with those tags")]
        
        response_text = f"Found {len(results)} memories:\n\n"
        for i, mem in enumerate(results, 1):
            response_text += f"{i}. ID: {mem.get('id')}\n"
            response_text += f"   Content: {mem.get('content', {}).get('text', 'N/A')[:150]}...\n"
            response_text += f"   Tags: {', '.join(mem.get('tags', []))}\n\n"
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error searching by tags: {str(e)}")]


async def get_stats_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Get memory statistics through MCP"""
    try:
        stats = redis_client.get_stats(agent_id=args.get("agent_id"))
        
        response_text = "Engram Memory Statistics\n"
        response_text += "=" * 40 + "\n"
        response_text += f"Total memories: {stats.get('total_memories', 0)}\n"
        response_text += f"Vector index: {'Active' if stats.get('vector_index_active') else 'Inactive'}\n"
        
        if args.get("agent_id"):
            response_text += f"Agent ID filter: {args['agent_id']}\n"
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting stats: {str(e)}")]


async def main():
    """Run the MCP server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Engram MCP server...")
    
    # Initialize Redis connection
    redis_client.connect()
    logger.info("Connected to Redis")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
