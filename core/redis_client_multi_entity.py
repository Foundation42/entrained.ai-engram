"""
Redis client for multi-entity memory system

Handles storage and retrieval of memories with witness-based access control
"""

import json
import logging
from typing import Optional, Dict, Any, List
import redis
import numpy as np
import time
from datetime import datetime

from core.config import settings

logger = logging.getLogger(__name__)


class RedisMultiEntityClient:
    """Redis client for multi-entity memory operations"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.vector_index_created = False
        self.index_name = f"{settings.vector_index_name}_multi"
        
    def connect(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=False,  # Binary support for vectors
                socket_keepalive=settings.socket_keepalive,
                socket_connect_timeout=settings.connection_timeout,
            )
            
            # Test connection
            self.client.ping()
            logger.info("Successfully connected to Redis")
            
            # Ensure vector index exists
            self._ensure_vector_index()
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _ensure_vector_index(self):
        """Create vector search index if it doesn't exist"""
        if self.vector_index_created:
            return
            
        try:
            # Use a different index name for multi-entity
            multi_entity_index_name = f"{settings.vector_index_name}_multi"
            
            # Check if index exists
            self.client.execute_command('FT.INFO', multi_entity_index_name)
            logger.info(f"Vector index '{multi_entity_index_name}' already exists")
            self.vector_index_created = True
            self.index_name = multi_entity_index_name
            return
        except redis.exceptions.ResponseError:
            # Index doesn't exist, create it
            pass
        
        try:
            # Use a different index name for multi-entity
            multi_entity_index_name = f"{settings.vector_index_name}_multi"
            self.index_name = multi_entity_index_name
            
            # Create index with multi-entity fields
            self.client.execute_command(
                'FT.CREATE',
                multi_entity_index_name,
                'ON', 'HASH',
                'PREFIX', '1', 'memory:',
                'SCHEMA',
                # Entity fields (remove hyphens for TAG compatibility)
                'witnessed_by', 'TAG', 'SEPARATOR', ',',
                'situation_id', 'TAG', 'SEPARATOR', ',',
                'situation_type', 'TAG', 'SEPARATOR', ',',
                # Content fields
                'content', 'TEXT',
                'summary', 'TEXT',
                # Metadata fields
                'timestamp', 'NUMERIC', 'SORTABLE',
                'interaction_quality', 'NUMERIC', 'SORTABLE',
                'duration_minutes', 'NUMERIC', 'SORTABLE',
                'topic_tags', 'TAG', 'SEPARATOR', ',',
                'privacy_level', 'TAG',
                # Vector field
                'embedding', 'VECTOR', settings.vector_algorithm, '6',
                'TYPE', 'FLOAT32',
                'DIM', str(settings.vector_dimensions),
                'DISTANCE_METRIC', settings.vector_distance_metric
            )
            
            logger.info(f"Successfully created multi-entity vector index '{multi_entity_index_name}'")
            self.vector_index_created = True
            
            # Give Redis time to initialize
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            raise
    
    def store_memory(self, memory_id: str, memory_data: Dict[str, Any]) -> bool:
        """Store a multi-entity memory"""
        try:
            # Extract witnessed_by list
            witnessed_by = memory_data.get('witnessed_by', [])
            if not witnessed_by:
                logger.error("Memory must have at least one witness")
                return False
            
            # Generate key
            key = f"memory:{memory_id}"
            
            # Extract vector
            vector = memory_data.get('primary_vector', [])
            if not vector or len(vector) != settings.vector_dimensions:
                logger.error(f"Invalid vector dimensions: expected {settings.vector_dimensions}, got {len(vector)}")
                return False
            
            # Prepare hash fields
            hash_data = {}
            
            # Basic fields
            hash_data['id'] = memory_id
            created_at_val = memory_data.get('created_at', datetime.utcnow())
            if isinstance(created_at_val, datetime):
                hash_data['created_at'] = created_at_val.isoformat() + 'Z'
            else:
                hash_data['created_at'] = created_at_val
            
            # Witnessed by - remove hyphens and join
            witnessed_clean = [str(w).replace('-', '') for w in witnessed_by]
            hash_data['witnessed_by'] = ','.join(witnessed_clean)
            
            # Situation info
            situation = memory_data.get('situation', {})
            logger.debug(f"Situation data type: {type(situation)}, content: {situation}")
            
            # Handle both dict and object access patterns
            if isinstance(situation, dict):
                hash_data['situation_id'] = str(situation.get('situation_id', '')).replace('-', '')
                hash_data['situation_type'] = str(situation.get('situation_type', 'unknown'))
            else:
                # If it's an object, use attribute access
                hash_data['situation_id'] = str(getattr(situation, 'situation_id', '')).replace('-', '')
                hash_data['situation_type'] = str(getattr(situation, 'situation_type', 'unknown'))
            
            # Content - ensure all values are strings, not None
            content = memory_data.get('content', {})
            hash_data['content'] = content.get('text') or ''
            hash_data['summary'] = content.get('summary') or ''
            
            # Speakers breakdown (store as JSON)
            speakers = content.get('speakers', {})
            hash_data['speakers_json'] = json.dumps(speakers)
            
            # Metadata
            metadata = memory_data.get('metadata', {})
            # Handle timestamp - could be datetime object or ISO string
            timestamp_val = metadata.get('timestamp', datetime.utcnow())
            if isinstance(timestamp_val, datetime):
                timestamp_ms = int(timestamp_val.timestamp() * 1000)
            else:
                # It's a string, parse it
                timestamp_ms = int(datetime.fromisoformat(timestamp_val.rstrip('Z')).timestamp() * 1000)
            hash_data['timestamp'] = str(timestamp_ms)
            hash_data['interaction_quality'] = str(metadata.get('interaction_quality', 1.0))
            
            # Handle duration_minutes - ensure it's a valid number, not None or string "None"
            duration_val = metadata.get('situation_duration_minutes', 0)
            if duration_val is None or duration_val == 'None':
                duration_val = 0
            hash_data['duration_minutes'] = str(duration_val)
            
            # Topic tags
            topic_tags = metadata.get('topic_tags', [])
            hash_data['topic_tags'] = ','.join(topic_tags) if topic_tags else ''
            
            # Access control
            access_control = memory_data.get('access_control', {})
            hash_data['privacy_level'] = access_control.get('privacy_level', 'participants_only')
            
            # Store full data as JSON
            hash_data['memory_json'] = json.dumps(memory_data, default=str)
            
            # Store hash fields
            self.client.hset(key, mapping=hash_data)
            
            # Store vector as binary
            vector_buffer = np.array(vector, dtype=np.float32).tobytes()
            self.client.hset(key, 'embedding', vector_buffer)
            
            # Update entity access indexes
            for entity_id in witnessed_by:
                entity_key = f"entity_access:{entity_id}"
                self.client.sadd(entity_key, memory_id)
            
            # Update situation index
            if situation.get('situation_id'):
                sit_key = f"situation:{situation['situation_id']}"
                self.client.hset(sit_key, mapping={
                    'participants': json.dumps(witnessed_by),
                    'created_at': hash_data['created_at'],
                    'situation_type': hash_data['situation_type']
                })
                self.client.sadd(f"{sit_key}:memories", memory_id)
            
            logger.info(f"Stored multi-entity memory {memory_id} witnessed by {len(witnessed_by)} entities")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory {memory_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search_memories(
        self,
        requesting_entity: str,
        query_vector: List[float],
        top_k: int = 10,
        entity_filters: Optional[Dict[str, Any]] = None,
        situation_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search memories with entity-based access control"""
        try:
            logger.info(f"Searching memories for entity {requesting_entity}")
            
            # Validate query vector
            if len(query_vector) != settings.vector_dimensions:
                logger.error(f"Invalid query vector dimensions")
                return []
            
            # Build filter query
            filter_parts = []
            
            # CRITICAL: Entity must be in witnessed_by list
            # Remove hyphens from requesting entity
            requesting_clean = requesting_entity.replace('-', '')
            filter_parts.append(f"@witnessed_by:{{{requesting_clean}}}")
            
            # Additional entity filters
            if entity_filters:
                # Co-participants filter
                if entity_filters.get('co_participants'):
                    for co_participant in entity_filters['co_participants']:
                        co_clean = co_participant.replace('-', '')
                        filter_parts.append(f"@witnessed_by:{{{co_clean}}}")
            
            # Situation filters
            if situation_filters:
                # Situation types
                if situation_filters.get('situation_types'):
                    types = "|".join(situation_filters['situation_types'])
                    filter_parts.append(f"@situation_type:{{{types}}}")
                
                # Topic tags
                if situation_filters.get('topic_tags'):
                    tags = "|".join(situation_filters['topic_tags'])
                    filter_parts.append(f"@topic_tags:{{{tags}}}")
                
                # Time range
                if situation_filters.get('time_range'):
                    time_range = situation_filters['time_range']
                    if time_range.get('after') or time_range.get('before'):
                        after_ms = int(time_range['after'].timestamp() * 1000) if time_range.get('after') else '-inf'
                        before_ms = int(time_range['before'].timestamp() * 1000) if time_range.get('before') else '+inf'
                        filter_parts.append(f"@timestamp:[{after_ms} {before_ms}]")
            
            # Build final query
            base_query = "(" + " ".join(filter_parts) + ")" if filter_parts else "*"
            knn_query = f"{base_query}=>[KNN {top_k} @embedding $query_vector AS vector_score]"
            
            logger.info(f"🔍 ISOLATION DEBUG - Multi-entity search:")
            logger.info(f"   Requesting entity: {requesting_entity}")
            logger.info(f"   Filter parts: {filter_parts}")
            logger.info(f"   Final query: {knn_query}")
            logger.info(f"   Top K: {top_k}")
            
            # Convert query vector to binary
            query_buffer = np.array(query_vector, dtype=np.float32).tobytes()
            
            # Execute search (with index creation retry)
            try:
                results = self.client.execute_command(
                    'FT.SEARCH',
                    self.index_name,
                    knn_query,
                    'PARAMS', '2',
                    'query_vector', query_buffer,
                    'SORTBY', 'vector_score', 'ASC',
                    'RETURN', '8',
                    'id', 'witnessed_by', 'situation_type', 'summary', 
                    'speakers_json', 'memory_json', 'vector_score', 'privacy_level',
                    'DIALECT', '2'
                )
            except redis.exceptions.ResponseError as e:
                if "No such index" in str(e):
                    logger.warning(f"Multi-entity vector index {self.index_name} not found, creating it...")
                    self._ensure_vector_index()
                    # Retry the search after creating index
                    results = self.client.execute_command(
                        'FT.SEARCH',
                        self.index_name,
                        knn_query,
                        'PARAMS', '2',
                        'query_vector', query_buffer,
                        'SORTBY', 'vector_score', 'ASC',
                        'RETURN', '8',
                        'id', 'witnessed_by', 'situation_type', 'summary', 
                        'speakers_json', 'memory_json', 'vector_score', 'privacy_level',
                        'DIALECT', '2'
                    )
                else:
                    raise
            
            # Parse results
            memories = []
            total_results = results[0]
            
            for i in range(1, len(results), 2):
                if i >= len(results):
                    break
                    
                doc_key = results[i]
                fields = results[i + 1] if i + 1 < len(results) else []
                
                # Parse fields into dict
                field_dict = {}
                for j in range(0, len(fields), 2):
                    if j + 1 < len(fields):
                        field_name = fields[j].decode() if isinstance(fields[j], bytes) else fields[j]
                        field_value = fields[j + 1]
                        if isinstance(field_value, bytes):
                            field_value = field_value.decode()
                        field_dict[field_name] = field_value
                
                # Restore witnessed_by with hyphens
                witnessed_str = field_dict.get('witnessed_by', '')
                witnessed_list = witnessed_str.split(',') if witnessed_str else []
                
                # Parse full memory data
                memory_json = json.loads(field_dict.get('memory_json', '{}'))
                
                # Get co-participants (excluding requesting entity)
                co_participants = [w for w in memory_json.get('witnessed_by', []) if w != requesting_entity]
                
                # Parse speakers
                speakers_data = json.loads(field_dict.get('speakers_json', '{}'))
                speakers_involved = list(speakers_data.keys())
                
                memory_result = {
                    'memory_id': field_dict.get('id'),
                    'similarity_score': 1 - float(field_dict.get('vector_score', 1)),
                    'access_granted': True,
                    'access_reason': 'witnessed_by_includes_requesting_entity',
                    'situation_summary': field_dict.get('summary', ''),
                    'situation_type': field_dict.get('situation_type', 'unknown'),
                    'co_participants': co_participants,
                    'content_preview': memory_json.get('content', {}).get('text', '')[:200] + '...',
                    'speakers_involved': speakers_involved,
                    'metadata': memory_json.get('metadata', {}),
                    'privacy_level': field_dict.get('privacy_level', 'participants_only')
                }
                
                memories.append(memory_result)
            
            logger.info(f"Found {len(memories)} accessible memories for {requesting_entity}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_memory(self, memory_id: str, requesting_entity: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory with access control check"""
        try:
            key = f"memory:{memory_id}"
            
            # Get memory data
            memory_data = self.client.hgetall(key)
            if not memory_data:
                return None
            
            # Check access control
            witnessed_by_str = memory_data.get(b'witnessed_by', b'').decode()
            witnessed_clean = witnessed_by_str.split(',') if witnessed_by_str else []
            
            # Check if requesting entity has access (remove hyphens for comparison)
            requesting_clean = requesting_entity.replace('-', '')
            if requesting_clean not in witnessed_clean:
                logger.warning(f"Access denied: {requesting_entity} not in witnessed_by list for {memory_id}")
                return None
            
            # Parse and return full memory
            memory_json = json.loads(memory_data.get(b'memory_json', b'{}').decode())
            return memory_json
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None


# Singleton instance
redis_multi_entity_client = RedisMultiEntityClient()