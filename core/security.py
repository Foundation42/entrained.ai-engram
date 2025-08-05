"""
Security middleware for Engram API
Provides API key authentication, rate limiting, and request validation
"""

import hashlib
import hmac
import time
from typing import Dict, Optional, Set
from collections import defaultdict, deque
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from core.config import settings

logger = logging.getLogger(__name__)

class APIKeyAuth(HTTPBearer):
    """API Key authentication for all endpoints"""
    
    def __init__(self):
        super().__init__(auto_error=False)
    
    async def __call__(self, request: Request) -> Optional[str]:
        """Validate API key from request"""
        if not settings.enable_api_auth:
            logger.debug("API authentication disabled")
            return "development"
            
        if not settings.api_secret_key:
            logger.error("API_SECRET_KEY not configured but authentication enabled")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error"
            )
        
        # Check for API key in headers
        api_key = None
        
        # Method 1: X-API-Key header (recommended)
        api_key = request.headers.get("X-API-Key")
        
        # Method 2: Authorization Bearer token
        if not api_key:
            credentials: HTTPAuthorizationCredentials = await super().__call__(request)
            if credentials:
                api_key = credentials.credentials
        
        # Method 3: Query parameter (less secure, for testing)
        if not api_key:
            api_key = request.query_params.get("api_key")
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Use X-API-Key header, Authorization Bearer, or api_key query param.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate API key
        if not self._validate_api_key(api_key):
            logger.warning(f"Invalid API key attempt from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.debug("API key validated successfully")
        return api_key
    
    def _validate_api_key(self, provided_key: str) -> bool:
        """Validate the provided API key against configured secret"""
        expected_key = settings.api_secret_key
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(provided_key, expected_key)


class RateLimiter:
    """Rate limiter to prevent abuse"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Set[str] = set()
        
        # Rate limiting configuration
        self.max_requests_per_minute = 60
        self.max_requests_per_hour = 1000
        self.block_duration = 3600  # 1 hour in seconds
        
    async def check_rate_limit(self, request: Request) -> bool:
        """Check if request should be rate limited"""
        if not settings.enable_api_auth:
            return True  # No rate limiting in development
            
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP {client_ip} attempted request")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="IP blocked due to excessive requests"
            )
        
        current_time = time.time()
        client_requests = self.requests[client_ip]
        
        # Clean old requests (older than 1 hour)
        while client_requests and current_time - client_requests[0] > 3600:
            client_requests.popleft()
        
        # Check hourly limit
        if len(client_requests) >= self.max_requests_per_hour:
            self._block_ip(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Hourly rate limit exceeded"
            )
        
        # Check minute limit
        recent_requests = sum(1 for req_time in client_requests if current_time - req_time < 60)
        if recent_requests >= self.max_requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again in a minute."
            )
        
        # Record this request
        client_requests.append(current_time)
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, considering proxies"""
        # Check for forwarded headers (common in production behind proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _block_ip(self, ip: str):
        """Block an IP address temporarily"""
        self.blocked_ips.add(ip)
        logger.warning(f"Blocking IP {ip} for {self.block_duration} seconds")
        
        # TODO: Implement automatic unblocking after duration
        # For now, blocked IPs persist until server restart


class ContentValidator:
    """Validate and sanitize request content"""
    
    def __init__(self):
        self.max_comment_length = 10000
        self.max_article_id_length = 200
        self.max_author_id_length = 100
        
        # Dangerous patterns (basic XSS prevention)
        self.dangerous_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"onmouseover=",
        ]
    
    def validate_comment_request(self, request_data: Dict) -> Dict:
        """Validate and sanitize comment request data"""
        import re
        
        # Validate required fields
        required_fields = ["author_id", "article_id", "comment_text"]
        for field in required_fields:
            if field not in request_data or not request_data[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Required field '{field}' is missing or empty"
                )
        
        # Validate field lengths
        if len(request_data["comment_text"]) > self.max_comment_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Comment text too long (max {self.max_comment_length} characters)"
            )
        
        if len(request_data["article_id"]) > self.max_article_id_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Article ID too long (max {self.max_article_id_length} characters)"
            )
        
        if len(request_data["author_id"]) > self.max_author_id_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Author ID too long (max {self.max_author_id_length} characters)"
            )
        
        # Basic XSS prevention
        comment_text = request_data["comment_text"]
        for pattern in self.dangerous_patterns:
            if re.search(pattern, comment_text, re.IGNORECASE):
                logger.warning(f"Potentially dangerous content detected: {pattern}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Content contains potentially dangerous elements"
                )
        
        # Sanitize HTML entities (basic protection)
        import html
        request_data["comment_text"] = html.escape(comment_text)
        request_data["article_id"] = html.escape(request_data["article_id"])
        request_data["author_id"] = html.escape(request_data["author_id"])
        
        return request_data


# Global instances
api_key_auth = APIKeyAuth()
rate_limiter = RateLimiter()
content_validator = ContentValidator()


async def security_middleware(request: Request, call_next):
    """Comprehensive security middleware"""
    try:
        # Skip security for health check endpoints
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            response = await call_next(request)
            return response
        
        # Rate limiting
        await rate_limiter.check_rate_limit(request)
        
        # API key authentication
        await api_key_auth(request)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security middleware error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security validation failed"
        )