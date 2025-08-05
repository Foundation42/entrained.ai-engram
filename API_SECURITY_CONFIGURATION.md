# API Security Configuration Guide

Comprehensive guide to configuring and managing security features in the Engram Memory System.

## Overview

The Engram API includes enterprise-grade security features designed for production deployments:

- **API Key Authentication**: Multi-method authentication support
- **Rate Limiting**: Per-IP request throttling with automatic blocking
- **Content Validation**: XSS protection and input sanitization
- **Security Headers**: OWASP-compliant HTTP security headers
- **Admin Authentication**: Separate admin endpoints with HTTP Basic Auth

## Authentication Methods

### API Key Authentication

The system supports three methods for providing API keys:

#### 1. X-API-Key Header (Recommended)
```bash
curl -X GET "http://localhost:8000/cam/curated/stats/entity-123" \
  -H "X-API-Key: your-api-key-here"
```

#### 2. Authorization Bearer Token
```bash
curl -X GET "http://localhost:8000/cam/curated/stats/entity-123" \
  -H "Authorization: Bearer your-api-key-here"
```

#### 3. Query Parameter (Less Secure)
```bash
curl -X GET "http://localhost:8000/cam/curated/stats/entity-123?api_key=your-api-key-here"
```

### Configuration

Enable API authentication in your `.env` file:

```bash
# Enable API key authentication
ENGRAM_ENABLE_API_AUTH=true

# Set your secure API key (32+ characters recommended)
ENGRAM_API_SECRET_KEY=your-very-secure-production-api-key-2025

# Optional: Customize CORS origins
ENGRAM_CORS_ORIGINS=["https://yourdomain.com","https://api.yourdomain.com"]
```

### API Key Generation

Generate a secure API key:

```bash
# Method 1: OpenSSL (recommended)
openssl rand -hex 32

# Method 2: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Method 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

**Example secure API key**: `engram-prod-2025-a8f3d9e2b7c4f1a6e5d8c3b2a9f6e4d7b1c8a5f2`

## Rate Limiting

### Default Limits

- **Per Minute**: 60 requests per IP address
- **Per Hour**: 1000 requests per IP address
- **Block Duration**: 1 hour for excessive requests

### Configuration

Customize rate limits in your `.env` file:

```bash
# Rate limiting configuration
ENGRAM_MAX_REQUESTS_PER_MINUTE=60
ENGRAM_MAX_REQUESTS_PER_HOUR=1000
ENGRAM_BLOCK_DURATION_SECONDS=3600

# Disable rate limiting (development only)
ENGRAM_ENABLE_API_AUTH=false
```

### Rate Limiting Behavior

When limits are exceeded:

1. **429 Too Many Requests** response for minute limit
2. **Temporary IP block** for hour limit exceeded
3. **Automatic unblocking** after block duration (currently requires restart)

### Monitoring Rate Limits

Check current rate limit status:

```python
import httpx

async def check_rate_limits():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/health",
            headers={"X-API-Key": "your-api-key"}
        )
        
        # Check response headers for rate limit info
        print(f"Rate limit remaining: {response.headers.get('X-RateLimit-Remaining')}")
        print(f"Rate limit reset: {response.headers.get('X-RateLimit-Reset')}")
```

## Content Validation & XSS Protection

### Comment Validation

For Comments-as-Engrams endpoints, the system automatically validates:

- **Length limits**: 10,000 characters maximum for comments
- **Dangerous patterns**: Script tags, JavaScript URIs, event handlers
- **HTML sanitization**: Automatic HTML entity escaping

### Configuration

Customize validation limits:

```bash
# Content validation limits
ENGRAM_COMMENT_MAX_LENGTH=10000
ENGRAM_COMMENT_MIN_LENGTH=10
ENGRAM_ARTICLE_ID_MAX_LENGTH=200
ENGRAM_AUTHOR_ID_MAX_LENGTH=100

# Enable/disable auto-moderation
ENGRAM_ENABLE_AUTO_MODERATION=true
ENGRAM_TOXICITY_THRESHOLD=0.8
```

### Dangerous Pattern Detection

The system blocks content containing:

- `<script>` tags and variants
- `javascript:` and `vbscript:` URIs
- Event handlers: `onload=`, `onerror=`, `onclick=`, etc.
- Data URIs with executable content

Example blocked content:
```javascript
// These will be rejected:
"Click here: <script>alert('xss')</script>"
"Check this out: javascript:alert('xss')"
"<img src='x' onerror='alert(1)'>"
```

## Security Headers

### Automatic Security Headers

All API responses include OWASP-recommended security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Custom Security Headers

Add custom headers via reverse proxy (Nginx example):

```nginx
server {
    location / {
        proxy_pass http://engram-backend;
        
        # Additional security headers
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'" always;
        add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    }
}
```

## Admin Authentication

### HTTP Basic Authentication

Admin endpoints use separate HTTP Basic Auth:

```bash
# Default credentials (CHANGE IN PRODUCTION!)
ENGRAM_ADMIN_USERNAME=admin
ENGRAM_ADMIN_PASSWORD=engram-admin-2025
```

### Admin Endpoints

Access admin endpoints with both API key and basic auth:

```bash
# Check system status
curl -X GET "http://localhost:8000/api/v1/admin/status" \
  -H "X-API-Key: your-api-key" \
  -u "admin:your-admin-password"

# Flush memories
curl -X POST "http://localhost:8000/api/v1/admin/flush/memories" \
  -H "X-API-Key: your-api-key" \
  -u "admin:your-admin-password"

# Recreate indexes
curl -X POST "http://localhost:8000/api/v1/admin/recreate/indexes" \
  -H "X-API-Key: your-api-key" \
  -u "admin:your-admin-password"
```

### Secure Admin Configuration

For production, use strong admin credentials:

```bash
# Generate secure admin password
ENGRAM_ADMIN_USERNAME=admin
ENGRAM_ADMIN_PASSWORD=$(openssl rand -base64 32)

# Or use a descriptive username
ENGRAM_ADMIN_USERNAME=engram-admin-$(whoami)
ENGRAM_ADMIN_PASSWORD=your-secure-admin-password-here
```

## Environment-Specific Configurations

### Development Environment

```bash
# .env.development
ENGRAM_DEBUG=true
ENGRAM_ENABLE_API_AUTH=false
ENGRAM_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

### Staging Environment

```bash
# .env.staging
ENGRAM_DEBUG=false
ENGRAM_ENABLE_API_AUTH=true
ENGRAM_API_SECRET_KEY=staging-api-key-different-from-prod
ENGRAM_CORS_ORIGINS=["https://staging.yourdomain.com"]
```

### Production Environment

```bash
# .env.production
ENGRAM_DEBUG=false
ENGRAM_ENABLE_API_AUTH=true
ENGRAM_API_SECRET_KEY=your-ultra-secure-production-key
ENGRAM_CORS_ORIGINS=["https://yourdomain.com","https://api.yourdomain.com"]
ENGRAM_MAX_REQUESTS_PER_MINUTE=100
ENGRAM_MAX_REQUESTS_PER_HOUR=2000
```

## Security Monitoring

### Health Check Endpoints

Monitor security status via health endpoints:

```bash
# Basic health (no auth required)
curl http://localhost:8000/health

# Detailed health (auth required)
curl -H "X-API-Key: your-key" http://localhost:8000/health

# Admin status (admin auth required)
curl -u admin:password -H "X-API-Key: your-key" \
  http://localhost:8000/api/v1/admin/status
```

### Log Monitoring

Security events are logged with structured information:

```json
{
  "timestamp": "2025-08-05T10:30:00Z",
  "level": "WARNING",
  "event": "invalid_api_key_attempt",
  "client_ip": "192.168.1.100",
  "user_agent": "curl/7.68.0",
  "endpoint": "/cam/comments/store"
}
```

Monitor logs for security events:

```bash
# Watch for security events
docker logs engram-api --tail 50 -f | grep -E "(WARNING|ERROR|invalid_api_key|rate_limit|blocked_ip)"

# Count failed auth attempts
docker logs engram-api | grep "invalid_api_key" | wc -l
```

### Metrics and Alerting

Implement monitoring for:

- Failed authentication attempts
- Rate limit violations
- Blocked IP addresses
- Content validation failures
- Admin endpoint access

Example Prometheus metrics:

```python
from prometheus_client import Counter, Histogram

# Security metrics
AUTH_FAILURES = Counter('engram_auth_failures_total', 'Failed authentication attempts', ['ip'])
RATE_LIMIT_VIOLATIONS = Counter('engram_rate_limit_violations_total', 'Rate limit violations', ['ip'])
CONTENT_VALIDATION_FAILURES = Counter('engram_content_validation_failures_total', 'Content validation failures')
```

## Client Implementation Examples

### JavaScript/TypeScript

```typescript
class EngramSecureClient {
  private apiKey: string;
  private baseUrl: string;
  private rateLimitRemaining: number = 60;

  constructor(apiKey: string, baseUrl: string) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    const headers = {
      'X-API-Key': this.apiKey,
      'Content-Type': 'application/json',
      ...options.headers
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers
    });

    // Update rate limit tracking
    const remaining = response.headers.get('X-RateLimit-Remaining');
    if (remaining) {
      this.rateLimitRemaining = parseInt(remaining);
    }

    if (response.status === 429) {
      throw new Error('Rate limit exceeded');
    }

    if (response.status === 401) {
      throw new Error('Invalid API key');
    }

    return response;
  }

  async storeComment(data: CommentData) {
    return this.makeRequest('/cam/comments/store', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  getRateLimitRemaining(): number {
    return this.rateLimitRemaining;
  }
}

// Usage
const client = new EngramSecureClient('your-api-key', 'https://api.yourdomain.com');
try {
  await client.storeComment({
    author_id: 'user-123',
    article_id: 'article-456',
    comment_text: 'Great article!'
  });
} catch (error) {
  console.error('API call failed:', error.message);
}
```

### Python

```python
import httpx
import asyncio
from typing import Optional
import logging

class EngramSecureClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit_remaining = 60
        self.logger = logging.getLogger(__name__)

    async def _make_request(self, endpoint: str, method: str = "GET", **kwargs):
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            **kwargs.get("headers", {})
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                **{k: v for k, v in kwargs.items() if k != "headers"}
            )
            
            # Track rate limits
            if "X-RateLimit-Remaining" in response.headers:
                self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
            
            # Handle security responses
            if response.status_code == 429:
                self.logger.warning("Rate limit exceeded")
                raise httpx.HTTPStatusError("Rate limit exceeded", request=response.request, response=response)
            
            if response.status_code == 401:
                self.logger.error("Invalid API key")
                raise httpx.HTTPStatusError("Invalid API key", request=response.request, response=response)
            
            response.raise_for_status()
            return response

    async def store_comment(self, author_id: str, article_id: str, comment_text: str):
        return await self._make_request(
            "/cam/comments/store",
            method="POST",
            json={
                "author_id": author_id,
                "article_id": article_id,
                "comment_text": comment_text
            }
        )

    async def health_check(self):
        response = await self._make_request("/health")
        return response.json()

# Usage
async def main():
    client = EngramSecureClient("your-api-key", "https://api.yourdomain.com")
    
    try:
        health = await client.health_check()
        print(f"API Status: {health['status']}")
        
        await client.store_comment(
            author_id="user-123",
            article_id="article-456", 
            comment_text="Excellent insights on AI memory systems!"
        )
        
        print(f"Rate limit remaining: {client.rate_limit_remaining}")
        
    except httpx.HTTPStatusError as e:
        print(f"API error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting Security Issues

### Common Authentication Problems

1. **401 Unauthorized**:
   - Verify API key is correct
   - Check that `ENGRAM_ENABLE_API_AUTH=true`
   - Ensure API key is properly URL-encoded in query params

2. **429 Rate Limited**:
   - Implement exponential backoff
   - Check current rate limit settings
   - Consider IP whitelisting for high-volume clients

3. **403 Forbidden**:
   - Verify witness-based access control
   - Check entity permissions for multi-entity operations

### Testing Security Configuration

```bash
#!/bin/bash
# security-test.sh

API_KEY="your-api-key"
BASE_URL="http://localhost:8000"

echo "Testing API security configuration..."

# Test 1: Valid API key
echo "1. Testing valid API key..."
response=$(curl -s -w "%{http_code}" -H "X-API-Key: $API_KEY" "$BASE_URL/health")
if [[ "${response: -3}" == "200" ]]; then
    echo "✅ Valid API key accepted"
else
    echo "❌ Valid API key rejected (${response: -3})"
fi

# Test 2: Invalid API key
echo "2. Testing invalid API key..."
response=$(curl -s -w "%{http_code}" -H "X-API-Key: invalid-key" "$BASE_URL/health")
if [[ "${response: -3}" == "401" ]]; then
    echo "✅ Invalid API key properly rejected"
else
    echo "❌ Invalid API key not rejected (${response: -3})"
fi

# Test 3: Rate limiting
echo "3. Testing rate limiting..."
for i in {1..65}; do
    curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/health" > /dev/null
done
response=$(curl -s -w "%{http_code}" -H "X-API-Key: $API_KEY" "$BASE_URL/health")
if [[ "${response: -3}" == "429" ]]; then
    echo "✅ Rate limiting working"
else
    echo "❌ Rate limiting not working (${response: -3})"
fi

# Test 4: XSS protection
echo "4. Testing XSS protection..."
response=$(curl -s -w "%{http_code}" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"author_id":"test","article_id":"test","comment_text":"<script>alert(1)</script>"}' \
    "$BASE_URL/cam/comments/store")
if [[ "${response: -3}" == "400" ]]; then
    echo "✅ XSS protection working"
else
    echo "❌ XSS protection not working (${response: -3})"
fi

echo "Security test complete."
```

### Security Audit Checklist

- [ ] Strong API keys (32+ characters) in production
- [ ] `ENGRAM_ENABLE_API_AUTH=true` in production
- [ ] Rate limiting configured appropriately
- [ ] Admin credentials changed from defaults
- [ ] CORS origins properly configured
- [ ] Security headers enabled
- [ ] SSL/TLS termination at load balancer
- [ ] Content validation enabled
- [ ] Log monitoring for security events
- [ ] Regular security updates applied

---

This comprehensive security configuration ensures your Engram Memory System is protected against common web application vulnerabilities while maintaining usability for authorized clients.