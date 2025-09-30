"""Unit tests for models module"""
import pytest
from datetime import datetime
from models.memory import Memory, MemoryContent, MemoryMetadata, MediaItem
from models.retrieval import ResonanceVector, RetrievalRequest, RetrievalConfig


@pytest.mark.unit
class TestMemoryModels:
    """Test Memory model classes"""
    
    def test_memory_content_creation(self):
        """Test MemoryContent model creation"""
        content = MemoryContent(
            text="Test content",
            media=[]
        )
        assert content.text == "Test content"
        assert len(content.media) == 0
    
    def test_memory_content_with_media(self):
        """Test MemoryContent with media items"""
        media = MediaItem(
            type="image",
            url="https://example.com/image.jpg",
            description="Test image"
        )
        content = MemoryContent(
            text="Content with media",
            media=[media]
        )
        assert len(content.media) == 1
        assert content.media[0].type == "image"
    
    def test_memory_metadata_creation(self):
        """Test MemoryMetadata model creation"""
        timestamp = datetime.utcnow()
        metadata = MemoryMetadata(
            timestamp=timestamp,
            agent_id="test-agent",
            memory_type="conversation"
        )
        assert metadata.agent_id == "test-agent"
        assert metadata.memory_type == "conversation"
        assert metadata.timestamp == timestamp
    
    def test_memory_metadata_with_session(self):
        """Test MemoryMetadata with session ID"""
        metadata = MemoryMetadata(
            timestamp=datetime.utcnow(),
            agent_id="test-agent",
            memory_type="conversation",
            session_id="session-123"
        )
        assert metadata.session_id == "session-123"
    
    def test_memory_creation(self):
        """Test Memory model creation"""
        content = MemoryContent(text="Test", media=[])
        metadata = MemoryMetadata(
            timestamp=datetime.utcnow(),
            agent_id="test-agent",
            memory_type="test"
        )
        vector = [0.1] * 1536
        
        memory = Memory(
            content=content,
            primary_vector=vector,
            metadata=metadata,
            tags=["test", "sample"]
        )
        
        assert memory.id.startswith("mem-")
        assert memory.content.text == "Test"
        assert len(memory.primary_vector) == 1536
        assert "test" in memory.tags
        assert memory.storage_backend == "redis"
    
    def test_memory_with_causality(self):
        """Test Memory with causality information"""
        from models.memory import CausalityInfo
        
        content = MemoryContent(text="Test", media=[])
        metadata = MemoryMetadata(
            timestamp=datetime.utcnow(),
            agent_id="test-agent",
            memory_type="synthesis"
        )
        causality = CausalityInfo(
            parent_memories=["mem-123", "mem-456"],
            influence_strength=[0.6, 0.4],
            synthesis_type="combination"
        )
        
        memory = Memory(
            content=content,
            primary_vector=[0.1] * 1536,
            metadata=metadata,
            causality=causality
        )
        
        assert memory.causality is not None
        assert len(memory.causality.parent_memories) == 2


@pytest.mark.unit
class TestRetrievalModels:
    """Test Retrieval model classes"""
    
    def test_resonance_vector_creation(self):
        """Test ResonanceVector model creation"""
        vector = ResonanceVector(
            vector=[0.1] * 1536,
            weight=1.0,
            label="query"
        )
        assert len(vector.vector) == 1536
        assert vector.weight == 1.0
        assert vector.label == "query"
    
    def test_retrieval_config_defaults(self):
        """Test RetrievalConfig default values"""
        config = RetrievalConfig()
        assert config.top_k == 10
        assert config.similarity_threshold == 0.75
        assert config.diversity_lambda == 0.5
        assert config.boost_recent == 0.0
    
    def test_retrieval_config_custom(self):
        """Test RetrievalConfig with custom values"""
        config = RetrievalConfig(
            top_k=20,
            similarity_threshold=0.8,
            diversity_lambda=0.3
        )
        assert config.top_k == 20
        assert config.similarity_threshold == 0.8
        assert config.diversity_lambda == 0.3
    
    def test_retrieval_request_creation(self):
        """Test RetrievalRequest model creation"""
        vector = ResonanceVector(
            vector=[0.1] * 1536,
            weight=1.0
        )
        request = RetrievalRequest(
            resonance_vectors=[vector]
        )
        assert len(request.resonance_vectors) == 1
        assert request.retrieval.top_k == 10  # Default
    
    def test_retrieval_request_with_filters(self):
        """Test RetrievalRequest with filters"""
        from models.retrieval import RetrievalFilters
        
        vector = ResonanceVector(vector=[0.1] * 1536, weight=1.0)
        filters = RetrievalFilters(
            memory_types=["conversation", "insight"],
            agent_ids=["agent-1", "agent-2"]
        )
        
        request = RetrievalRequest(
            resonance_vectors=[vector],
            filters=filters
        )
        
        assert request.filters is not None
        assert "conversation" in request.filters.memory_types
