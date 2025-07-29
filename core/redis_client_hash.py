import json
import logging
from typing import Optional, Dict, Any, List
from redis import Redis
import numpy as np
import time

from core.config import settings

logger = logging.getLogger(__name__)


class RedisHashClient:
    """Redis client using HASH storage for vector search compatibility"""
    
    def __init__(self):
        self.client: Optional[Redis] = None
        self.vector_index_created = False
        
    def connect(self):
        """Initialize Redis connection"""
        try:
            self.client = Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=False,  # Important: we need binary support for vectors
                max_connections=settings.max_connections,
                socket_connect_timeout=settings.connection_timeout,
                socket_keepalive=settings.socket_keepalive,
            )
            
            self.client.ping()
            logger.info("Successfully connected to Redis")
            
            # Create vector index
            self._ensure_vector_index()
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _ensure_vector_index(self):
        """Create vector similarity search index if it doesn't exist"""
        try:
            # Check if index exists
            self.client.execute_command('FT.INFO', settings.vector_index_name)
            logger.info(f"Vector index '{settings.vector_index_name}' already exists")
            self.vector_index_created = True
        except:
            # Create index
            logger.info(f"Creating vector index '{settings.vector_index_name}'")
            self._create_vector_index()
    
    def _create_vector_index(self):
        """Create the vector similarity search index using HASH storage"""
        try:
            # Drop existing index if needed (for clean setup)
            try:
                self.client.execute_command('FT.DROPINDEX', settings.vector_index_name, 'DD')
                logger.info(f"Dropped existing index '{settings.vector_index_name}'")
            except:
                pass  # Index doesn't exist
            
            # Create index with HASH storage
            self.client.execute_command(
                'FT.CREATE',
                settings.vector_index_name,
                'ON', 'HASH',
                'PREFIX', '1', 'memory:',  # Key prefix pattern
                'SCHEMA',
                'agent_id', 'TAG', 'SEPARATOR', ',',
                'memory_type', 'TAG', 'SEPARATOR', ',',
                'domain', 'TAG', 'SEPARATOR', ',',
                'tags', 'TAG', 'SEPARATOR', ',',
                'content', 'TEXT',
                'timestamp', 'NUMERIC', 'SORTABLE',
                'confidence', 'NUMERIC', 'SORTABLE',
                'embedding', 'VECTOR', settings.vector_algorithm, '6',
                'TYPE', 'FLOAT32',
                'DIM', str(settings.vector_dimensions),
                'DISTANCE_METRIC', settings.vector_distance_metric
            )
            
            logger.info(f"Successfully created vector index '{settings.vector_index_name}'")
            self.vector_index_created = True
            
            # Give Redis a moment to fully initialize the index
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            raise
    
    def store_memory(self, memory_id: str, memory_data: Dict[str, Any]) -> bool:
        """Store a memory using HASH storage"""
        try:
            # Extract agent_id for key pattern
            agent_id = memory_data['metadata']['agent_id']
            key = f"memory:{agent_id}:{memory_id}"
            
            # Extract and validate vector
            vector = memory_data.get("primary_vector", [])
            if not vector:
                logger.error(f"No vector provided for memory {memory_id}")
                return False
            
            if len(vector) != settings.vector_dimensions:
                logger.error(f"Vector dimension mismatch: expected {settings.vector_dimensions}, got {len(vector)}")
                return False
            
            # Prepare hash fields
            hash_data = {
                'id': memory_id,
                'agent_id': agent_id,
                'content': memory_data['content']['text'],
                'memory_type': memory_data['metadata']['memory_type'],
                'domain': memory_data['metadata'].get('domain', ''),
                'timestamp': str(int(datetime.fromisoformat(memory_data['metadata']['timestamp'].rstrip('Z')).timestamp() * 1000)),
                'confidence': str(memory_data['metadata'].get('confidence', 1.0)),
                'tags': ','.join(memory_data.get('tags', [])),
                'metadata_json': json.dumps(memory_data['metadata']),
                'content_json': json.dumps(memory_data['content'])
            }
            
            # Store hash fields
            self.client.hset(key, mapping=hash_data)
            
            # Store vector as binary (CRITICAL: must be Float32)
            vector_buffer = np.array(vector, dtype=np.float32).tobytes()
            self.client.hset(key, 'embedding', vector_buffer)
            
            # Handle causality if present
            if memory_data.get("causality") and memory_data["causality"].get("parent_memories"):
                self._store_causality_relations(memory_id, memory_data["causality"])
            
            logger.info(f"Stored memory {memory_id} at key {key} with {len(vector)}-dim vector")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory {memory_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _store_causality_relations(self, memory_id: str, causality: Dict[str, Any]):
        """Store causality relationships"""
        try:
            for parent_id in causality.get("parent_memories", []):
                self.client.sadd(f"causality:{memory_id}:parents", parent_id)
                self.client.sadd(f"causality:{parent_id}:children", memory_id)
        except Exception as e:
            logger.error(f"Failed to store causality relations for {memory_id}: {e}")
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a memory by ID"""
        try:
            # Find the key by scanning (we don't know the agent_id)
            pattern = f"memory:*:{memory_id}"
            keys = list(self.client.scan_iter(match=pattern, count=100))
            
            if not keys:
                logger.warning(f"No memory found with ID {memory_id}")
                return None
            
            key = keys[0]  # Take first match
            data = self.client.hgetall(key)
            
            if not data:
                return None
            
            # Decode and reconstruct memory
            memory = {
                "id": data[b'id'].decode(),
                "content": json.loads(data[b'content_json'].decode()),
                "metadata": json.loads(data[b'metadata_json'].decode()),
                "tags": data[b'tags'].decode().split(',') if data[b'tags'] else [],
                "created_at": data[b'timestamp'].decode()
            }
            
            # Get and decode vector
            if b'embedding' in data:
                vector_bytes = data[b'embedding']
                vector = np.frombuffer(vector_bytes, dtype=np.float32).tolist()
                memory["primary_vector"] = vector
            
            return memory
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None
    
    def search_memories(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for memories using vector similarity"""
        try:
            logger.info(f"Searching with vector of dimension {len(query_vector)}, top_k={top_k}")
            
            # Validate query vector dimensions
            if len(query_vector) != settings.vector_dimensions:
                logger.error(f"Query vector dimension mismatch: expected {settings.vector_dimensions}, got {len(query_vector)}")
                return []
            
            # Build filter query
            filter_parts = []
            
            # Agent filter
            if filters and filters.get("agent_ids"):
                agent_filter = "|".join([f"{aid}" for aid in filters["agent_ids"]])
                filter_parts.append(f"@agent_id:{{{agent_filter}}}")
            
            # Tag filter  
            if tags:
                tag_filter = "|".join(tags)
                filter_parts.append(f"@tags:{{{tag_filter}}}")
            
            # Domain filter
            if filters and filters.get("domains"):
                domain_filter = "|".join(filters["domains"])
                filter_parts.append(f"@domain:{{{domain_filter}}}")
            
            # Build base query
            if filter_parts:
                base_query = "(" + " ".join(filter_parts) + ")"
            else:
                base_query = "*"
            
            # Build KNN query
            knn_query = f"{base_query}=>[KNN {top_k} @embedding $query_vector AS vector_score]"
            
            # Convert query vector to binary
            query_buffer = np.array(query_vector, dtype=np.float32).tobytes()
            
            # Execute search
            results = self.client.execute_command(
                'FT.SEARCH',
                settings.vector_index_name,
                knn_query,
                'PARAMS', '2',
                'query_vector', query_buffer,
                'SORTBY', 'vector_score', 'ASC',
                'RETURN', '7',
                'id', 'content', 'agent_id', 'tags', 'metadata_json', 'vector_score', 'confidence',
                'DIALECT', '2'
            )
            
            # Parse results
            total_results = results[0]
            logger.info(f"Search returned {total_results} documents")
            
            memories = []
            
            # Results format: [total, doc1_id, [field1, value1, ...], doc2_id, ...]
            for i in range(1, len(results), 2):
                if i >= len(results):
                    break
                    
                doc_id = results[i].decode() if isinstance(results[i], bytes) else results[i]
                fields = results[i + 1]
                
                # Parse fields into dict
                field_dict = {}
                for j in range(0, len(fields), 2):
                    field_name = fields[j].decode() if isinstance(fields[j], bytes) else fields[j]
                    field_value = fields[j + 1]
                    
                    if isinstance(field_value, bytes):
                        field_dict[field_name] = field_value.decode()
                    else:
                        field_dict[field_name] = field_value
                
                # Convert cosine distance to similarity score (1 - distance/2)
                distance = float(field_dict.get('vector_score', 1.0))
                similarity = 1 - (distance / 2)
                
                # Build result
                memory_data = {
                    "memory_id": field_dict.get('id', doc_id.split(':')[-1]),
                    "similarity_score": similarity,
                    "content_preview": field_dict.get('content', '')[:200] + "...",
                    "metadata": json.loads(field_dict.get('metadata_json', '{}')),
                    "tags": field_dict.get('tags', '').split(',') if field_dict.get('tags') else [],
                    "media_count": 0,  # TODO: Calculate from content
                    "annotation_count": len(self.get_annotations(field_dict.get('id', '')))
                }
                memories.append(memory_data)
            
            # Sort by similarity score (highest first)
            memories.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def add_annotation(self, memory_id: str, annotation: Dict[str, Any]) -> bool:
        """Add an annotation to a memory"""
        try:
            key = f"annotations:{memory_id}"
            self.client.rpush(key, json.dumps(annotation))
            return True
        except Exception as e:
            logger.error(f"Failed to add annotation to {memory_id}: {e}")
            return False
    
    def get_annotations(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get all annotations for a memory"""
        try:
            key = f"annotations:{memory_id}"
            annotations = self.client.lrange(key, 0, -1)
            return [json.loads(ann) for ann in annotations]
        except Exception as e:
            logger.error(f"Failed to get annotations for {memory_id}: {e}")
            return []
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the vector index"""
        try:
            info = self.client.execute_command('FT.INFO', settings.vector_index_name)
            
            # Parse info into dict
            info_dict = {}
            for i in range(0, len(info), 2):
                key = info[i].decode() if isinstance(info[i], bytes) else str(info[i])
                value = info[i+1]
                if isinstance(value, bytes):
                    value = value.decode()
                info_dict[key] = value
            
            return {
                "index_name": settings.vector_index_name,
                "num_docs": int(info_dict.get('num_docs', 0)),
                "indexing": info_dict.get('indexing', False),
                "indexing_failures": int(info_dict.get('hash_indexing_failures', 0))
            }
        except Exception as e:
            logger.error(f"Failed to get index info: {e}")
            return {}
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")


# Import datetime for timestamp conversion
from datetime import datetime

# Global Redis client instance
redis_client = RedisHashClient()