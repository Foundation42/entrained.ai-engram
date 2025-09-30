#!/usr/bin/env python3
"""
Test MCP functionality against production Engram API
Uses the HTTP API as the backend instead of local Redis
"""
import httpx
import asyncio
import json
from datetime import datetime

# Production server configuration
PROD_URL = "https://engram-fi-1.entrained.ai:8443"
API_KEY = "engram-production-secure-key-2025-comments-system"


class EngramMCPClient:
    """MCP-style client for Engram that uses HTTP API backend"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def store_memory(self, text: str, agent_id: str, memory_type: str,
                          tags: list = None, session_id: str = None) -> dict:
        """Store a memory (MCP tool: store_memory)"""
        headers = {"X-API-Key": self.api_key}

        # First get embedding from the API's embedding service
        # For now, use a dummy vector - in production you'd call embedding service
        dummy_vector = [0.1] * 1536

        payload = {
            "content": {
                "text": text,
                "media": []
            },
            "primary_vector": dummy_vector,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": agent_id,
                "memory_type": memory_type,
                "session_id": session_id
            },
            "tags": tags or []
        }

        response = await self.client.post(
            f"{self.base_url}/cam/store",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to store memory: {response.status_code} - {response.text}")

    async def retrieve_memories(self, query: str, top_k: int = 5,
                               similarity_threshold: float = 0.7,
                               agent_id: str = None, session_id: str = None) -> dict:
        """Retrieve memories by semantic similarity (MCP tool: retrieve_memories)"""
        headers = {"X-API-Key": self.api_key}

        # Use dummy vector for now
        dummy_vector = [0.1] * 1536

        payload = {
            "resonance_vectors": [
                {
                    "vector": dummy_vector,
                    "weight": 1.0
                }
            ],
            "retrieval": {
                "top_k": top_k,
                "similarity_threshold": similarity_threshold
            }
        }

        response = await self.client.post(
            f"{self.base_url}/cam/retrieve",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to retrieve memories: {response.status_code} - {response.text}")

    async def get_memory(self, memory_id: str) -> dict:
        """Get a specific memory by ID (MCP tool: get_memory)"""
        headers = {"X-API-Key": self.api_key}

        response = await self.client.get(
            f"{self.base_url}/cam/memory/{memory_id}",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get memory: {response.status_code} - {response.text}")

    async def get_stats(self) -> dict:
        """Get system statistics (MCP tool: get_stats)"""
        response = await self.client.get(f"{self.base_url}/health")

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get stats: {response.status_code} - {response.text}")


async def test_mcp_operations():
    """Test all MCP-style operations against production API"""
    print("🧪 Testing MCP Operations Against Production Engram\n")
    print("=" * 60)

    client = EngramMCPClient(PROD_URL, API_KEY)

    try:
        # Test 1: Get Stats
        print("\n1️⃣  MCP Tool: get_stats")
        print("-" * 60)
        stats = await client.get_stats()
        print(f"✅ Status: {stats['status']}")
        print(f"✅ Redis: {stats['redis']}")
        print(f"✅ Vector Index: {stats['vector_index']}")

        # Test 2: Store Memory
        print("\n2️⃣  MCP Tool: store_memory")
        print("-" * 60)
        memory_result = await client.store_memory(
            text="Testing MCP client connectivity to production Engram server",
            agent_id="mcp-test-client",
            memory_type="test",
            tags=["mcp", "test", "production"]
        )
        memory_id = memory_result["memory_id"]
        print(f"✅ Memory stored: {memory_id}")

        # Test 3: Get Memory
        print("\n3️⃣  MCP Tool: get_memory")
        print("-" * 60)
        memory = await client.get_memory(memory_id)
        print(f"✅ Memory ID: {memory['id']}")
        print(f"✅ Content: {memory['content']['text'][:60]}...")
        print(f"✅ Agent: {memory['metadata']['agent_id']}")
        print(f"✅ Tags: {', '.join(memory['tags'])}")

        # Test 4: Retrieve Similar Memories
        print("\n4️⃣  MCP Tool: retrieve_memories")
        print("-" * 60)
        results = await client.retrieve_memories(
            query="production testing",
            top_k=3,
            similarity_threshold=0.5
        )
        memories = results.get('memories', [])
        print(f"✅ Found {len(memories)} similar memories")
        for i, mem in enumerate(memories[:3], 1):
            mem_id = mem.get('id') or mem.get('memory_id', 'unknown')
            score = mem.get('similarity_score', mem.get('score', 0))
            print(f"   {i}. {mem_id} - Score: {score:.3f}")

        print("\n" + "=" * 60)
        print("✅ All MCP operations completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


async def interactive_demo():
    """Interactive demo showing MCP capabilities"""
    print("\n🎯 Interactive MCP Demo")
    print("=" * 60)

    client = EngramMCPClient(PROD_URL, API_KEY)

    try:
        # Simulate a conversation being stored as memories
        conversation = [
            ("user", "What is the capital of France?"),
            ("assistant", "The capital of France is Paris."),
            ("user", "What is Paris known for?"),
            ("assistant", "Paris is known for the Eiffel Tower, the Louvre Museum, and French cuisine."),
        ]

        print("\n📝 Storing conversation as memories...")
        stored_ids = []
        for role, text in conversation:
            result = await client.store_memory(
                text=text,
                agent_id=f"demo-{role}",
                memory_type="conversation",
                tags=["demo", "conversation", role]
            )
            stored_ids.append(result["memory_id"])
            print(f"   ✅ Stored {role}: {result['memory_id']}")

        print(f"\n🔍 Retrieving conversation memories...")
        results = await client.retrieve_memories(
            query="France and Paris",
            top_k=5,
            similarity_threshold=0.5
        )

        memories = results.get('memories', [])
        print(f"\n📊 Found {len(memories)} related memories:")
        for i, mem in enumerate(memories, 1):
            agent_id = mem.get('metadata', {}).get('agent_id', 'unknown')
            role = agent_id.split('-')[1] if '-' in agent_id else 'unknown'
            score = mem.get('similarity_score', mem.get('score', 0))
            text = mem.get('content', {}).get('text', 'N/A')
            print(f"\n   {i}. [{role.upper()}] Score: {score:.3f}")
            print(f"      {text[:80]}...")

        print("\n" + "=" * 60)
        print("✅ Interactive demo completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    import sys

    print("""
╔════════════════════════════════════════════════════════════╗
║      Engram MCP Client - Production Test Suite            ║
║                                                            ║
║  Testing MCP operations against production API at:        ║
║  https://engram-fi-1.entrained.ai:8443                    ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Run basic tests
    asyncio.run(test_mcp_operations())

    # Run interactive demo
    if "--demo" in sys.argv:
        asyncio.run(interactive_demo())
        print("\n💡 Tip: Run with --demo flag to see interactive conversation demo")
    else:
        print("\n💡 Tip: Run with --demo flag to see interactive conversation demo")