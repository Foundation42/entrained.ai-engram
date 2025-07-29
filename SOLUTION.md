# Engram Vector Search Solution

## The Issue

The vector search was returning 0 results due to Redis vector index configuration issues in the latest Redis Stack. The key issues were:

1. **Storage Format**: Need to use HASH storage (not JSON) for vector compatibility
2. **Key Pattern**: Must match the index prefix exactly 
3. **Binary Vectors**: Vectors must be stored as binary Float32 arrays
4. **Index Creation**: Must ensure index is created before storing data

## Working Solution

Based on your TypeScript reference, here's what works:

### 1. Create Index with HASH Storage
```python
r.execute_command(
    'FT.CREATE', 'memory_vectors',
    'ON', 'HASH',
    'PREFIX', '1', 'memory:',
    'SCHEMA',
    'agentId', 'TAG',
    'content', 'TEXT', 
    'embedding', 'VECTOR', 'HNSW', '6',
    'TYPE', 'FLOAT32',
    'DIM', '768',
    'DISTANCE_METRIC', 'COSINE'
)
```

### 2. Store Memories as HASH
```python
# Key pattern: memory:agentId:memoryId
key = f"memory:{agent_id}:{memory_id}"

# Store fields
r.hset(key, mapping={
    'agentId': agent_id,
    'content': text,
    # other fields...
})

# Store embedding as binary
embedding_buffer = np.array(embedding, dtype=np.float32).tobytes()
r.hset(key, 'embedding', embedding_buffer)
```

### 3. Search with KNN
```python
results = r.execute_command(
    'FT.SEARCH',
    'memory_vectors',
    '@agentId:{agent_id} => [KNN 10 @embedding $query_vector AS score]',
    'PARAMS', '2',
    'query_vector', query_buffer,
    'SORTBY', 'score', 'ASC',
    'DIALECT', '2'
)
```

## Key Takeaways

1. Redis 6.x+ changed how vector indexes work
2. HASH storage is more reliable than JSON for vectors
3. Binary format is required for vector fields
4. The key prefix in the index MUST match your actual keys
5. Wait for index to be ready before storing data

## Next Steps

To fully fix Engram:

1. Update `redis_client_v2.py` to ensure the key prefix matches
2. Consider adding a reindex command for existing data
3. Add retry logic for indexing failures
4. Implement proper error handling for vector operations

The core functionality is there - it just needs these adjustments to work with the latest Redis Stack!