"""Pytest configuration and shared fixtures for Engram tests"""
import pytest
import os
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    client = Mock()
    client.ping = Mock(return_value=True)
    client.get = Mock(return_value=None)
    client.set = Mock(return_value=True)
    client.hset = Mock(return_value=True)
    client.hget = Mock(return_value=None)
    client.hgetall = Mock(return_value={})
    client.delete = Mock(return_value=True)
    client.ft = Mock()
    return client


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing"""
    service = Mock()
    service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    service.generate_embeddings_batch = AsyncMock(return_value=[[0.1] * 1536])
    service.combine_vectors = Mock(return_value=[0.1] * 1536)
    return service


@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing"""
    return {
        "content": {
            "text": "Test memory content",
            "media": []
        },
        "primary_vector": [0.1] * 1536,
        "metadata": {
            "timestamp": "2025-01-01T00:00:00Z",
            "agent_id": "test-agent",
            "memory_type": "test"
        },
        "tags": ["test", "sample"]
    }


@pytest.fixture
def test_api_key():
    """Test API key for authentication tests"""
    return "test-secret-key-12345"


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch, test_api_key):
    """Set test environment variables"""
    monkeypatch.setenv("ENGRAM_API_SECRET_KEY", test_api_key)
    monkeypatch.setenv("ENGRAM_ENABLE_API_AUTH", "false")
    monkeypatch.setenv("ENGRAM_DEBUG", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
