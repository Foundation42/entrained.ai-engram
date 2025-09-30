# Production Deployment Guide

This guide covers deploying Engram Memory System to production with enterprise-grade security, monitoring, and reliability.

## Quick Production Checklist

- [ ] OpenAI API key configured
- [ ] Strong API secret key set
- [ ] Redis persistence enabled
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] SSL/TLS terminated at load balancer
- [ ] Log aggregation setup
- [ ] Health checks configured

## Environment Configuration

### Required Environment Variables

Create a production `.env` file:

```bash
# === CORE CONFIGURATION ===
ENGRAM_APP_NAME=engram-production
ENGRAM_API_VERSION=v1
ENGRAM_DEBUG=false

# === REDIS CONFIGURATION ===
ENGRAM_REDIS_HOST=redis
ENGRAM_REDIS_PORT=6379
ENGRAM_REDIS_PASSWORD=your-secure-redis-password
ENGRAM_REDIS_DB=0

# === OPENAI EMBEDDINGS (REQUIRED) ===
ENGRAM_OPENAI_API_KEY=sk-your-openai-api-key-here
ENGRAM_VECTOR_DIMENSIONS=1536
ENGRAM_VECTOR_ALGORITHM=HNSW
ENGRAM_VECTOR_DISTANCE_METRIC=COSINE

# === SECURITY (REQUIRED) ===
ENGRAM_API_SECRET_KEY=your-very-secure-api-key-min-32-chars
ENGRAM_ENABLE_API_AUTH=true

# === CORS CONFIGURATION ===
ENGRAM_CORS_ORIGINS=["https://yourdomain.com","https://api.yourdomain.com"]

# === COMMENTS-AS-ENGRAMS ===
ENGRAM_ENABLE_COMMENT_ENGRAMS=true
ENGRAM_ENABLE_AGENT_RESPONSES=true
ENGRAM_DEFAULT_AGENT_ID=agent-claude-prime

# === RATE LIMITING ===
ENGRAM_MAX_REQUESTS_PER_MINUTE=60
ENGRAM_MAX_REQUESTS_PER_HOUR=1000

# === ADMIN CONFIGURATION ===
ENGRAM_ADMIN_USERNAME=admin
ENGRAM_ADMIN_PASSWORD=your-secure-admin-password-change-this
```

### Security Best Practices

#### 1. API Key Generation
```bash
# Generate a secure API key (32+ characters)
openssl rand -hex 32

# Or use a password manager to generate a strong key
# Example: engram-prod-2025-a8f3d9e2b7c4f1a6e5d8c3b2a9f6e4d7
```

#### 2. Redis Security
```bash
# Set a strong Redis password
ENGRAM_REDIS_PASSWORD=$(openssl rand -hex 24)

# In production, also configure Redis AUTH
# Add to your redis.conf:
# requirepass your-redis-password
# rename-command FLUSHDB ""
# rename-command FLUSHALL ""
```

#### 3. Network Security
- Use private networks for Redis communication
- Implement IP whitelisting
- Use SSL/TLS termination at load balancer
- Enable firewall rules

## Docker Production Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  engram-api:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    container_name: engram-production-api
    restart: unless-stopped
    env_file: .env
    environment:
      - ENGRAM_DEBUG=false
      - ENGRAM_ENABLE_API_AUTH=true
    ports:
      - "8000:8000"
    depends_on:
      - redis
    networks:
      - engram-network
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  redis:
    image: redis/redis-stack:7.4.0-v2
    container_name: engram-production-redis
    restart: unless-stopped
    environment:
      - REDIS_ARGS=--requirepass ${ENGRAM_REDIS_PASSWORD}
    ports:
      - "6379:6379"
      - "8001:8001"  # RedisInsight (disable in production)
    volumes:
      - redis-data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    networks:
      - engram-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: engram-production-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - nginx-logs:/var/log/nginx
    depends_on:
      - engram-api
    networks:
      - engram-network

networks:
  engram-network:
    driver: bridge

volumes:
  redis-data:
    driver: local
  nginx-logs:
    driver: local
```

### Production Dockerfile

Create `Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

# Set production environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Create non-root user
RUN groupadd -r engram && useradd -r -g engram engram

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs && chown -R engram:engram /app

# Switch to non-root user
USER engram

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Deployment Commands

```bash
# 1. Set up production environment
cp .env.example .env
# Edit .env with production values

# 2. Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# 3. Verify deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs engram-api

# 4. Test API
curl -H "X-API-Key: your-api-key" http://your-server:8000/health
```

## Kubernetes Deployment

### ConfigMap and Secrets

```yaml
# config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: engram-config
data:
  ENGRAM_APP_NAME: "engram-production"
  ENGRAM_API_VERSION: "v1"
  ENGRAM_DEBUG: "false"
  ENGRAM_REDIS_HOST: "redis"
  ENGRAM_REDIS_PORT: "6379"
  ENGRAM_VECTOR_DIMENSIONS: "1536"
  ENGRAM_ENABLE_API_AUTH: "true"
  ENGRAM_ENABLE_COMMENT_ENGRAMS: "true"

---
apiVersion: v1
kind: Secret
metadata:
  name: engram-secrets
type: Opaque
stringData:
  ENGRAM_OPENAI_API_KEY: "sk-your-openai-api-key"
  ENGRAM_API_SECRET_KEY: "your-secure-api-key"
  ENGRAM_REDIS_PASSWORD: "your-redis-password"
  ENGRAM_ADMIN_PASSWORD: "your-admin-password"
```

### Deployment Manifests

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: engram-api
  labels:
    app: engram-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: engram-api
  template:
    metadata:
      labels:
        app: engram-api
    spec:
      containers:
      - name: engram-api
        image: your-registry/engram:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: engram-config
        - secretRef:
            name: engram-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: engram-api-service
spec:
  selector:
    app: engram-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: engram-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: engram-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: engram-api-service
            port:
              number: 80
```

## Monitoring & Observability

### Health Checks

The API provides several health check endpoints:

```bash
# Basic health check
curl http://your-server:8000/health

# Admin status (with authentication)
curl -u admin:password -H "X-API-Key: your-key" \
  http://your-server:8000/api/v1/admin/status
```

### Logging Configuration

Create `logging.conf`:

```ini
[loggers]
keys=root,engram

[handlers]
keys=console,file

[formatters]
keys=detailed

[logger_root]
level=INFO
handlers=console,file

[logger_engram]
level=INFO
handlers=file
qualname=engram
propagate=0

[handler_console]
class=StreamHandler
level=INFO
formatter=detailed
args=(sys.stdout,)

[handler_file]
class=handlers.RotatingFileHandler
level=INFO
formatter=detailed
args=('/app/logs/engram.log', 'a', 10485760, 5)

[formatter_detailed]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Prometheus Metrics

Add to your `requirements.txt`:
```
prometheus-client==0.17.1
```

Example metrics endpoint:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Add to main.py
REQUEST_COUNT = Counter('engram_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('engram_request_duration_seconds', 'Request latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Log Aggregation with ELK Stack

Docker Compose addition:

```yaml
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
      - ./logs:/app/logs

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
```

## Backup & Recovery

### Redis Backup Strategy

1. **Automated Backups**:
```bash
#!/bin/bash
# backup-redis.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker exec engram-production-redis redis-cli --rdb /data/backup_$DATE.rdb
aws s3 cp /path/to/redis/data/backup_$DATE.rdb s3://your-backup-bucket/redis/
```

2. **Point-in-time Recovery**:
```bash
# Restore from backup
docker stop engram-production-redis
aws s3 cp s3://your-backup-bucket/redis/backup_20250805_120000.rdb /path/to/redis/data/dump.rdb
docker start engram-production-redis
```

### Database Migration

```bash
# Export memories
curl -u admin:password -H "X-API-Key: your-key" \
  http://your-server:8000/api/v1/admin/export > memories_backup.json

# Import to new instance
curl -u admin:password -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d @memories_backup.json \
  http://new-server:8000/api/v1/admin/import
```

## Performance Optimization

### Redis Configuration

Create `redis.conf`:

```conf
# Memory optimization
maxmemory 4gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511

# Security
requirepass your-redis-password
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
```

### API Performance

1. **Connection Pooling**:
```python
# In core/redis_client_*.py
redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    max_connections=20,
    retry_on_timeout=True
)
```

2. **Caching Strategy**:
```python
# Cache frequently accessed memories
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_frequent_memory(memory_id: str):
    return redis_client.get_memory(memory_id)
```

### Load Balancing

Nginx configuration:

```nginx
upstream engram_backend {
    server engram-api-1:8000;
    server engram-api-2:8000;
    server engram-api-3:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://engram_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
}
```

## Security Hardening

### SSL/TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/certificate.pem;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy no-referrer-when-downgrade always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

### Firewall Rules

```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 6379/tcp   # Redis (internal only)
ufw deny 8000/tcp   # API (behind proxy)
ufw enable
```

### Security Scanning

Regular security audits:

```bash
# Docker image scanning
docker scan your-registry/engram:latest

# Dependency scanning
pip-audit

# Static analysis
bandit -r .

# Container security
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/app \
  aquasec/trivy:latest image your-registry/engram:latest
```

## Troubleshooting

### Common Issues

1. **Memory Out of Space**:
```bash
# Check Redis memory usage
docker exec redis redis-cli info memory

# Increase memory limits or implement cleanup
curl -u admin:password -H "X-API-Key: your-key" \
  http://your-server:8000/api/v1/admin/flush/memories
```

2. **High API Latency**:
```bash
# Check API metrics
curl http://your-server:8000/metrics

# Monitor Redis performance
docker exec redis redis-cli --latency-history
```

3. **Vector Index Issues**:
```bash
# Recreate indexes
curl -u admin:password -H "X-API-Key: your-key" \
  -X POST http://your-server:8000/api/v1/admin/recreate/indexes
```

### Debug Mode

For troubleshooting only (never in production):

```bash
# Enable debug logging
ENGRAM_DEBUG=true docker-compose restart engram-api

# Check detailed logs
docker logs engram-production-api --tail 100 -f
```

## Maintenance Tasks

### Regular Maintenance Schedule

**Daily:**
- Check system health endpoints
- Monitor log levels and error rates
- Verify backup completion

**Weekly:**
- Review memory usage trends
- Update security patches
- Performance optimization review

**Monthly:**
- Full system backup verification
- Security audit and penetration testing
- Capacity planning review

### Automated Maintenance Script

```bash
#!/bin/bash
# maintenance.sh

# Health check
if ! curl -f -H "X-API-Key: $API_KEY" http://localhost:8000/health > /dev/null 2>&1; then
    echo "Health check failed" | mail -s "Engram Health Alert" admin@yourdomain.com
fi

# Backup
./backup-redis.sh

# Log rotation
find /app/logs -name "*.log" -mtime +30 -delete

# Update metrics
curl -H "X-API-Key: $API_KEY" http://localhost:8000/metrics > /tmp/metrics
```

Set up cron job:
```bash
# Add to crontab
0 2 * * * /path/to/maintenance.sh
```

---

This production deployment guide ensures your Engram Memory System runs reliably and securely in enterprise environments. Always test deployments in staging environments that mirror production before deploying to live systems.