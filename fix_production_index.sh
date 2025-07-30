#!/bin/bash
# Quick fix for production server - create missing multi-entity index

echo "🏥 Creating missing multi-entity vector index on production..."

# Create the multi-entity vector index
docker exec entrained-ai-engram-redis redis-cli FT.CREATE engram_vector_idx_multi \
  ON HASH \
  PREFIX 1 memory: \
  SCHEMA \
    witnessed_by TAG SEPARATOR , \
    situation_id TAG SEPARATOR , \
    situation_type TAG SEPARATOR , \
    content TEXT \
    summary TEXT \
    timestamp NUMERIC SORTABLE \
    interaction_quality NUMERIC SORTABLE \
    duration_minutes NUMERIC SORTABLE \
    topic_tags TAG SEPARATOR , \
    privacy_level TAG \
    embedding VECTOR HNSW 6 TYPE FLOAT32 DIM 768 DISTANCE_METRIC COSINE

echo "✅ Multi-entity vector index created!"
echo "🧪 Testing with a quick search..."

# Test the index exists
docker exec entrained-ai-engram-redis redis-cli FT.INFO engram_vector_idx_multi | head -10

echo "🎉 Production fix complete! Multi-entity retrieval should work now."