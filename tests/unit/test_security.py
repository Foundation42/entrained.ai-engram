"""Unit tests for core.security module"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request
from core.security import APIKeyAuth, RateLimiter, ContentValidator


@pytest.mark.unit
class TestAPIKeyAuth:
    """Test API key authentication"""
    
    @pytest.mark.asyncio
    async def test_auth_disabled(self, monkeypatch):
        """Test authentication when disabled"""
        monkeypatch.setenv("ENGRAM_ENABLE_API_AUTH", "false")
        from core.config import Settings
        settings = Settings()
        
        with patch('core.security.settings', settings):
            auth = APIKeyAuth()
            request = Mock(spec=Request)
            result = await auth(request)
            assert result == "development"
    
    @pytest.mark.asyncio
    async def test_valid_api_key_header(self, test_api_key, monkeypatch):
        """Test valid API key in X-API-Key header"""
        monkeypatch.setenv("ENGRAM_ENABLE_API_AUTH", "true")
        monkeypatch.setenv("ENGRAM_API_SECRET_KEY", test_api_key)
        from core.config import Settings
        settings = Settings()
        
        with patch('core.security.settings', settings):
            auth = APIKeyAuth()
            request = Mock(spec=Request)
            request.headers = {"X-API-Key": test_api_key}
            request.query_params = {}
            
            result = await auth(request)
            assert result == test_api_key
    
    @pytest.mark.asyncio
    async def test_invalid_api_key(self, test_api_key, monkeypatch):
        """Test invalid API key raises exception"""
        monkeypatch.setenv("ENGRAM_ENABLE_API_AUTH", "true")
        monkeypatch.setenv("ENGRAM_API_SECRET_KEY", test_api_key)
        from core.config import Settings
        settings = Settings()
        
        with patch('core.security.settings', settings):
            auth = APIKeyAuth()
            request = Mock(spec=Request)
            request.headers = {"X-API-Key": "wrong-key"}
            request.query_params = {}
            request.client = Mock()
            request.client.host = "127.0.0.1"
            
            with pytest.raises(HTTPException) as exc_info:
                await auth(request)
            assert exc_info.value.status_code == 401


@pytest.mark.unit
class TestRateLimiter:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_disabled(self, monkeypatch):
        """Test rate limiting when auth is disabled"""
        monkeypatch.setenv("ENGRAM_ENABLE_API_AUTH", "false")
        from core.config import Settings
        settings = Settings()
        
        with patch('core.security.settings', settings):
            limiter = RateLimiter()
            request = Mock(spec=Request)
            request.client = Mock()
            request.client.host = "127.0.0.1"
            request.headers = {}
            
            result = await limiter.check_rate_limit(request)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_within_limits(self, monkeypatch):
        """Test requests within rate limits"""
        monkeypatch.setenv("ENGRAM_ENABLE_API_AUTH", "true")
        from core.config import Settings
        settings = Settings()
        
        with patch('core.security.settings', settings):
            limiter = RateLimiter()
            request = Mock(spec=Request)
            request.client = Mock()
            request.client.host = "127.0.0.1"
            request.headers = {}
            
            # Make a few requests
            for _ in range(5):
                result = await limiter.check_rate_limit(request)
                assert result is True
    
    def test_get_client_ip_forwarded(self):
        """Test client IP extraction from X-Forwarded-For"""
        limiter = RateLimiter()
        request = Mock(spec=Request)
        request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
        request.client = Mock()
        request.client.host = "10.0.0.1"
        
        ip = limiter._get_client_ip(request)
        assert ip == "1.2.3.4"


@pytest.mark.unit
class TestContentValidator:
    """Test content validation and sanitization"""
    
    def test_valid_comment_request(self):
        """Test validation of valid comment request"""
        validator = ContentValidator()
        request_data = {
            "author_id": "user-123",
            "article_id": "article-456",
            "comment_text": "This is a valid comment."
        }
        
        result = validator.validate_comment_request(request_data)
        assert result["author_id"] == "user-123"
        assert result["article_id"] == "article-456"
        assert "valid comment" in result["comment_text"]
    
    def test_missing_required_field(self):
        """Test validation with missing required field"""
        validator = ContentValidator()
        request_data = {
            "author_id": "user-123",
            "article_id": "article-456"
            # Missing comment_text
        }
        
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_comment_request(request_data)
        assert exc_info.value.status_code == 400
        assert "comment_text" in str(exc_info.value.detail)
    
    def test_comment_too_long(self):
        """Test validation with comment exceeding max length"""
        validator = ContentValidator()
        request_data = {
            "author_id": "user-123",
            "article_id": "article-456",
            "comment_text": "x" * 20000  # Exceeds max length
        }
        
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_comment_request(request_data)
        assert exc_info.value.status_code == 400
        assert "too long" in str(exc_info.value.detail)
    
    def test_xss_prevention(self):
        """Test XSS pattern detection"""
        validator = ContentValidator()
        request_data = {
            "author_id": "user-123",
            "article_id": "article-456",
            "comment_text": "<script>alert('xss')</script>"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_comment_request(request_data)
        assert exc_info.value.status_code == 400
        assert "dangerous" in str(exc_info.value.detail)
    
    def test_html_escaping(self):
        """Test HTML entity escaping"""
        validator = ContentValidator()
        request_data = {
            "author_id": "user-123",
            "article_id": "article-456",
            "comment_text": "Test with <b>HTML</b> & special chars"
        }
        
        result = validator.validate_comment_request(request_data)
        assert "&lt;b&gt;" in result["comment_text"]
        assert "&amp;" in result["comment_text"]
