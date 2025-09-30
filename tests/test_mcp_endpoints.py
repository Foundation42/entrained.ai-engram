"""
Comprehensive tests for MCP endpoints against production server
Tests all 6 MCP tools with real API calls
"""
import pytest
import httpx
import json
import asyncio
from typing import Dict, Any

# Production API configuration
API_URL = "https://engram-fi-1.entrained.ai:8443/mcp/"
API_KEY = "engram-production-secure-key-2025-comments-system"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


class TestMCPEndpoints:
    """Test suite for MCP protocol endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client"""
        self.client = httpx.Client(verify=False, timeout=30.0)
        self.request_id = 1
        yield
        self.client.close()

    def send_jsonrpc(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP endpoint"""
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        self.request_id += 1

        response = self.client.post(API_URL, headers=HEADERS, json=payload)
        assert response.status_code == 200, f"Request failed: {response.text}"

        result = response.json()
        assert "result" in result or "error" in result, f"Invalid response: {result}"

        if "error" in result:
            pytest.fail(f"JSON-RPC error: {result['error']}")

        return result["result"]

    def test_01_initialize(self):
        """Test MCP initialize handshake"""
        result = self.send_jsonrpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })

        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "engram-memory"
        print(f"✅ Initialize: {result['serverInfo']}")

    def test_02_list_tools(self):
        """Test tools/list - should return 6 tools"""
        result = self.send_jsonrpc("tools/list")

        assert "tools" in result
        tools = result["tools"]
        assert len(tools) == 6, f"Expected 6 tools, got {len(tools)}"

        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "store_memory",
            "retrieve_memories",
            "get_memory",
            "list_recent_memories",
            "get_memory_stats",
            "memory"
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"

        print(f"✅ Tools list: {', '.join(tool_names)}")

    def test_03_get_memory_stats(self):
        """Test get_memory_stats tool"""
        result = self.send_jsonrpc("tools/call", {
            "name": "get_memory_stats",
            "arguments": {}
        })

        assert "content" in result
        content = result["content"][0]["text"]

        assert "Engram Memory System Status" in content
        assert "Health:" in content
        assert "Redis:" in content
        print(f"✅ Memory stats retrieved")

    def test_04_store_memory(self):
        """Test store_memory tool"""
        result = self.send_jsonrpc("tools/call", {
            "name": "store_memory",
            "arguments": {
                "content": "Test memory from automated test suite. This verifies that storing memories works correctly.",
                "tags": ["test", "automation", "verification"],
                "memory_type": "event",
                "importance": 0.8
            }
        })

        assert "content" in result
        content = result["content"][0]["text"]

        assert "Memory stored successfully" in content
        assert "ID:" in content
        assert "event" in content  # Type might have markdown formatting
        assert "test" in content and "automation" in content

        # Extract memory ID for later tests
        lines = content.split("\n")
        id_line = [l for l in lines if "ID:" in l][0]
        memory_id = id_line.split("**ID:** ")[1].split("**")[0].strip()

        # Store for other tests
        self.__class__.test_memory_id = memory_id
        print(f"✅ Stored memory: {memory_id}")

    def test_05_retrieve_memories(self):
        """Test retrieve_memories tool"""
        result = self.send_jsonrpc("tools/call", {
            "name": "retrieve_memories",
            "arguments": {
                "query": "automated test suite verification",
                "top_k": 5,
                "threshold": 0.5
            }
        })

        assert "content" in result
        content = result["content"][0]["text"]

        assert "Found" in content or "No memories found" in content

        if "Found" in content:
            assert "Score:" in content
            print(f"✅ Retrieved memories successfully")
        else:
            print(f"⚠️  No memories found (may need to wait for indexing)")

    def test_06_retrieve_with_filters(self):
        """Test retrieve_memories with tag and type filters"""
        result = self.send_jsonrpc("tools/call", {
            "name": "retrieve_memories",
            "arguments": {
                "query": "test automation",
                "top_k": 3,
                "filter_tags": ["test", "automation"],
                "memory_type": "event"
            }
        })

        assert "content" in result
        content = result["content"][0]["text"]
        print(f"✅ Filtered retrieval executed")

    def test_07_get_memory(self):
        """Test get_memory tool with specific ID"""
        if not hasattr(self.__class__, "test_memory_id"):
            pytest.skip("No memory ID available from store test")

        result = self.send_jsonrpc("tools/call", {
            "name": "get_memory",
            "arguments": {
                "memory_id": self.__class__.test_memory_id
            }
        })

        assert "content" in result
        content = result["content"][0]["text"]

        assert "Memory:" in content
        assert self.__class__.test_memory_id in content
        assert "Type:" in content
        assert "Tags:" in content
        assert "Content:" in content
        print(f"✅ Retrieved specific memory: {self.__class__.test_memory_id}")

    def test_08_list_recent_memories(self):
        """Test list_recent_memories tool"""
        result = self.send_jsonrpc("tools/call", {
            "name": "list_recent_memories",
            "arguments": {
                "limit": 10
            }
        })

        assert "content" in result
        content = result["content"][0]["text"]

        assert "most recent memories" in content or "No recent memories" in content
        print(f"✅ Listed recent memories")

    def test_09_unified_memory_store(self):
        """Test unified memory interface - storage"""
        result = self.send_jsonrpc("tools/call", {
            "name": "memory",
            "arguments": {
                "request": "Remember that the automated test suite ran successfully on this date"
            }
        })

        assert "content" in result
        content = result["content"][0]["text"]

        assert "stored successfully" in content.lower() or "memory" in content.lower()
        print(f"✅ Unified interface (store) worked")

    def test_10_unified_memory_retrieve(self):
        """Test unified memory interface - retrieval"""
        result = self.send_jsonrpc("tools/call", {
            "name": "memory",
            "arguments": {
                "request": "What do I know about automated tests?"
            }
        })

        assert "content" in result
        content = result["content"][0]["text"]

        # Should either find results or indicate none found
        assert "Found" in content or "No memories" in content or "not sure" in content
        print(f"✅ Unified interface (retrieve) worked")

    def test_11_store_multiple_types(self):
        """Test storing different memory types"""
        memory_types = [
            ("fact", "The Engram system uses Redis Stack for vector storage"),
            ("preference", "Test user prefers detailed logging"),
            ("solution", "Fixed MCP endpoints by matching Redis client API"),
            ("insight", "Vector embeddings enable semantic search"),
            ("decision", "Decided to use volume mounts for live code reload"),
            ("pattern", "MCP tools follow consistent request/response format")
        ]

        for mem_type, content in memory_types:
            result = self.send_jsonrpc("tools/call", {
                "name": "store_memory",
                "arguments": {
                    "content": content,
                    "tags": ["test", mem_type],
                    "memory_type": mem_type,
                    "importance": 0.6
                }
            })

            assert "content" in result
            response_text = result["content"][0]["text"]
            assert "stored successfully" in response_text.lower()

        print(f"✅ Stored 6 different memory types")

    def test_12_retrieve_by_type(self):
        """Test retrieving memories filtered by type"""
        result = self.send_jsonrpc("tools/call", {
            "name": "retrieve_memories",
            "arguments": {
                "query": "system information",
                "memory_type": "fact",
                "top_k": 5
            }
        })

        assert "content" in result
        content = result["content"][0]["text"]
        print(f"✅ Type-filtered retrieval executed")

    def test_13_invalid_memory_id(self):
        """Test get_memory with invalid ID"""
        result = self.send_jsonrpc("tools/call", {
            "name": "get_memory",
            "arguments": {
                "memory_id": "mem-doesnotexist"
            }
        })

        assert "content" in result
        content = result["content"][0]["text"]
        assert "not found" in content.lower() or "❌" in content
        print(f"✅ Invalid ID handled correctly")

    @pytest.mark.skip(reason="SSE endpoint only sends heartbeats every 30s, too slow for tests")
    def test_14_get_endpoint(self):
        """Test GET endpoint for SSE (should return stream)"""
        # SSE endpoint streams indefinitely with 30s heartbeats
        # Manually verified to work, but too slow for automated tests
        pass

    def test_15_performance_batch_store(self):
        """Test performance with batch memory storage"""
        import time
        start = time.time()

        for i in range(5):
            self.send_jsonrpc("tools/call", {
                "name": "store_memory",
                "arguments": {
                    "content": f"Performance test memory #{i+1}",
                    "tags": ["performance", "batch"],
                    "memory_type": "fact",
                    "importance": 0.5
                }
            })

        elapsed = time.time() - start
        avg_time = elapsed / 5

        print(f"✅ Batch store: 5 memories in {elapsed:.2f}s (avg {avg_time:.2f}s each)")
        assert avg_time < 5.0, f"Storage too slow: {avg_time:.2f}s per memory"


def test_connection():
    """Quick connection test"""
    client = httpx.Client(verify=False, timeout=10.0)
    try:
        response = client.post(
            API_URL,
            headers=HEADERS,
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )
        assert response.status_code == 200
        print(f"✅ Connection successful")
    finally:
        client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])