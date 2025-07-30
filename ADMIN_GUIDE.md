# Engram Admin Guide

## Safe Database Management

Engram provides secure admin endpoints for database management that preserve system integrity.

### Authentication

All admin endpoints require HTTP Basic Authentication:
- **Username:** `admin`  
- **Password:** `engram-admin-2025` (⚠️ Change this in production!)

### Admin Endpoints

#### 1. Safe Memory Flush
```bash
curl -u admin:engram-admin-2025 -X POST \
  http://your-server:8000/api/v1/admin/flush/memories
```

**What it does:**
- ✅ Removes all memories (single-agent and multi-entity)
- ✅ Removes all entity access keys and situation data
- ✅ **Preserves vector indexes** (no service disruption!)
- ✅ Provides detailed before/after counts
- ✅ Handles both memory systems safely

**Response example:**
```json
{
  "status": "success",
  "message": "Successfully flushed 156 keys",
  "initial_counts": {
    "single_agent_memories": 45,
    "multi_entity_memories": 23,
    "entity_access_keys": 67,
    "situation_keys": 21,
    "total_keys": 156
  },
  "deleted_count": 156,
  "remaining_counts": {
    "memories": 0,
    "entity_access": 0,
    "situations": 0
  },
  "indexes_preserved": {
    "single_agent_index": true,
    "multi_entity_index": true
  }
}
```

#### 2. System Health Status
```bash
curl -u admin:engram-admin-2025 \
  http://your-server:8000/api/v1/admin/status
```

**What it shows:**
- Memory counts by type
- Vector index status
- Redis connection health

**Response example:**
```json
{
  "status": "healthy",
  "memory_counts": {
    "total_memories": 68,
    "entity_access_keys": 45,
    "situation_keys": 23
  },
  "indexes": {
    "single_agent": "exists",
    "multi_entity": "exists"
  },
  "redis_connection": "connected"
}
```

#### 3. Recreate Missing Indexes
```bash
curl -u admin:engram-admin-2025 -X POST \
  http://your-server:8000/api/v1/admin/recreate/indexes
```

**When to use:**
- After manual Redis operations
- If you see "No such index" errors
- During maintenance/recovery

**Response example:**
```json
{
  "status": "success",
  "message": "Index recreation completed",
  "results": {
    "single_agent": "recreated_successfully",
    "multi_entity": "recreated_successfully"
  }
}
```

### Production Usage Examples

#### Complete System Reset
```bash
# 1. Check current status
curl -u admin:engram-admin-2025 http://production:8000/api/v1/admin/status

# 2. Safely flush all memories
curl -u admin:engram-admin-2025 -X POST http://production:8000/api/v1/admin/flush/memories

# 3. Verify system is clean but healthy
curl -u admin:engram-admin-2025 http://production:8000/api/v1/admin/status
```

#### Recovery After Issues
```bash
# If you're seeing "No such index" errors:
curl -u admin:engram-admin-2025 -X POST http://production:8000/api/v1/admin/recreate/indexes

# Then verify health:
curl -u admin:engram-admin-2025 http://production:8000/api/v1/admin/status
```

### Security Notes

1. **Change the default password** in `api/admin_endpoints.py` before production deployment
2. **Use HTTPS** in production to protect credentials
3. **Restrict network access** to admin endpoints (firewall/VPN)
4. **Monitor admin endpoint usage** in your logs

### Why This is Better Than Scripts

❌ **Old way (unsafe):**
- Required container exec access
- Could break vector indexes
- No authentication
- No detailed feedback
- Manual Redis commands

✅ **New way (safe):**
- Clean REST API interface
- Preserves system integrity
- Authenticated access
- Detailed reporting
- Professional operations

### Troubleshooting

**Q: Getting 401 Unauthorized**
A: Check your username/password. Default is `admin:engram-admin-2025`

**Q: Flush says "No memories to flush"**  
A: System is already clean - this is normal

**Q: Index recreation fails**
A: Check Redis connection and logs. Redis might be down.

**Q: Memory counts seem wrong**
A: Run the status endpoint to see current state before operations