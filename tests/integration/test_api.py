"""Integration tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


@pytest.mark.integration
class TestAPIEndpoints:
    """Test API endpoint integration"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns correct info"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "entrained.ai-engram"
        assert data["status"] == "running"
        assert "single-agent" in data["features"]
        assert "multi-entity" in data["features"]
    
    def test_health_endpoint_success(self, client):
        """Test health endpoint when Redis is connected"""
        with patch("core.redis_client_hash.redis_client") as mock_redis:
            mock_redis.client.ping.return_value = True
            mock_redis.vector_index_created = True
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["redis"] == "connected"
    
    def test_health_endpoint_failure(self, client):
        """Test health endpoint when Redis is disconnected"""
        with patch("core.redis_client_hash.redis_client") as mock_redis:
            mock_redis.client.ping.side_effect = Exception("Connection failed")
            
            response = client.get("/health")
            assert response.status_code == 503
            
            data = response.json()
            assert data["status"] == "unhealthy"
