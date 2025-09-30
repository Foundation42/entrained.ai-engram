"""Unit tests for core.config module"""
import pytest
from core.config import Settings


@pytest.mark.unit
class TestSettings:
    """Test Settings configuration"""
    
    def test_default_settings(self):
        """Test default settings values"""
        settings = Settings()
        assert settings.app_name == "entrained.ai-engram"
        assert settings.api_version == "v1"
        assert settings.redis_host == "localhost"
        assert settings.redis_port == 6379
        assert settings.vector_dimensions == 1536
    
    def test_custom_settings(self, monkeypatch):
        """Test custom settings from environment"""
        monkeypatch.setenv("ENGRAM_APP_NAME", "test-engram")
        monkeypatch.setenv("ENGRAM_REDIS_PORT", "6380")
        monkeypatch.setenv("ENGRAM_VECTOR_DIMENSIONS", "768")
        
        settings = Settings()
        assert settings.app_name == "test-engram"
        assert settings.redis_port == 6380
        assert settings.vector_dimensions == 768
    
    def test_api_auth_settings(self, monkeypatch):
        """Test API authentication settings"""
        monkeypatch.setenv("ENGRAM_ENABLE_API_AUTH", "true")
        monkeypatch.setenv("ENGRAM_API_SECRET_KEY", "test-secret")
        
        settings = Settings()
        assert settings.enable_api_auth is True
        assert settings.api_secret_key == "test-secret"
    
    def test_vector_settings(self):
        """Test vector configuration"""
        settings = Settings()
        assert settings.vector_index_name == "engram_vector_idx"
        assert settings.vector_distance_metric == "COSINE"
        assert settings.vector_algorithm == "HNSW"
