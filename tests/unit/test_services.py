"""Unit tests for services module"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from services.embedding import EmbeddingService


@pytest.mark.unit
class TestEmbeddingService:
    """Test EmbeddingService class"""
    
    def test_embedding_service_initialization(self, monkeypatch):
        """Test EmbeddingService initialization"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        service = EmbeddingService()
        
        assert service.api_key == "test-key"
        assert service.model == "text-embedding-3-small"
        assert service.base_url == "https://api.openai.com/v1"
    
    def test_embedding_service_no_api_key(self, monkeypatch):
        """Test EmbeddingService without API key"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("core.config.settings.openai_api_key", None)
        
        service = EmbeddingService()
        assert service.api_key is None
    
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, monkeypatch):
        """Test successful embedding generation"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        service = EmbeddingService()
        
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 1536}]
        }
        
        service.client.post = AsyncMock(return_value=mock_response)
        
        result = await service.generate_embedding("test text")
        assert result is not None
        assert len(result) == 1536
    
    @pytest.mark.asyncio
    async def test_generate_embedding_no_api_key(self):
        """Test embedding generation without API key"""
        service = EmbeddingService()
        service.api_key = None
        
        result = await service.generate_embedding("test text")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self, monkeypatch):
        """Test embedding generation with API error"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        service = EmbeddingService()
        
        # Mock the HTTP client to return error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        service.client.post = AsyncMock(return_value=mock_response)
        
        result = await service.generate_embedding("test text")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, monkeypatch):
        """Test batch embedding generation"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        service = EmbeddingService()
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 1536}]
        }
        
        service.client.post = AsyncMock(return_value=mock_response)
        
        texts = ["text1", "text2", "text3"]
        results = await service.generate_embeddings_batch(texts)
        
        assert len(results) == 3
        assert all(r is not None for r in results)
    
    def test_combine_vectors_simple(self):
        """Test vector combination without weights"""
        service = EmbeddingService()
        
        vectors = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ]
        
        result = service.combine_vectors(vectors)
        assert len(result) == 3
        # Should be normalized average
        assert isinstance(result, list)
    
    def test_combine_vectors_weighted(self):
        """Test weighted vector combination"""
        service = EmbeddingService()
        
        vectors = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ]
        weights = [0.7, 0.3]
        
        result = service.combine_vectors(vectors, weights)
        assert len(result) == 3
        # Result should be normalized
        norm = np.linalg.norm(result)
        assert abs(norm - 1.0) < 0.01  # Approximately unit length
    
    def test_combine_vectors_empty(self):
        """Test combining empty vector list"""
        service = EmbeddingService()
        result = service.combine_vectors([])
        assert result == []
    
    @pytest.mark.asyncio
    async def test_close(self, monkeypatch):
        """Test closing the service"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        service = EmbeddingService()
        service.client.aclose = AsyncMock()
        
        await service.close()
        service.client.aclose.assert_called_once()
