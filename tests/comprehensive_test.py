#!/usr/bin/env python3
"""
Comprehensive test suite for Engram - testing real-world scenarios
"""

import httpx
import asyncio
from datetime import datetime, timedelta
import json
import random
import time
from typing import List, Dict, Any


class EngramTestSuite:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.memories_created = []
        
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        try:
            response = await self.client.post(
                "http://localhost:11434/api/embeddings",
                json={
                    "model": "nomic-embed-text:latest",
                    "prompt": text
                }
            )
            if response.status_code == 200:
                return response.json()["embedding"]
        except:
            print("Warning: Ollama not available, using random embeddings")
            # Fallback to random embeddings for testing
            random.seed(hash(text))
            embedding = [random.gauss(0, 1) for _ in range(settings.vector_dimensions)]
            # Normalize
            norm = sum(x**2 for x in embedding) ** 0.5
            return [x/norm for x in embedding]
    
    async def store_memory(self, content: str, metadata: Dict[str, Any], 
                          tags: List[str], media: List[Dict] = None,
                          causality: Dict = None) -> str:
        """Store a memory and track it"""
        embedding = await self.get_embedding(content)
        
        memory = {
            "content": {
                "text": content,
                "media": media or []
            },
            "primary_vector": embedding,
            "metadata": metadata,
            "tags": tags,
            "causality": causality
        }
        
        response = await self.client.post(f"{self.base_url}/cam/store", json=memory)
        memory_id = response.json()["memory_id"]
        self.memories_created.append(memory_id)
        return memory_id
    
    async def search_memories(self, query: str, tags: List[str] = None, 
                             top_k: int = 5) -> List[Dict]:
        """Search for memories"""
        query_embedding = await self.get_embedding(query)
        
        request = {
            "resonance_vectors": [{
                "vector": query_embedding,
                "weight": 1.0,
                "label": "primary_query"
            }],
            "retrieval": {
                "top_k": top_k,
                "similarity_threshold": 0.3
            }
        }
        
        if tags:
            request["tags"] = {"include": tags}
        
        response = await self.client.post(f"{self.base_url}/cam/retrieve", json=request)
        return response.json()["memories"]
    
    async def test_email_faculty_flow(self):
        """Test 1: Email Faculty Conversation Flow"""
        print("\n=== Test 1: Email Faculty Conversation Flow ===")
        
        # Initial email from professor
        email1_id = await self.store_memory(
            content="I'm working on sparse neural networks and wondering about the theoretical limits "
                   "of sparsity while maintaining performance. Have you seen any recent work on this?",
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "conversation",
                "participants": ["claude", "prof.zhang@university.edu"],
                "thread_id": "email-thread-sparse-nn",
                "domain": "machine_learning",
                "confidence": 0.95
            },
            tags=["faculty:claude", "domain:ml", "sparse-networks", "email-conversation"]
        )
        print(f"Stored initial email: {email1_id}")
        
        # Search for relevant context
        print("\nSearching for relevant context...")
        context_memories = await self.search_memories(
            "sparse neural networks theoretical limits performance",
            tags=["domain:ml"]
        )
        print(f"Found {len(context_memories)} relevant memories")
        
        # Store a related paper memory that should be found
        paper_id = await self.store_memory(
            content="The Lottery Ticket Hypothesis demonstrates that dense networks contain sparse "
                   "subnetworks that can achieve comparable accuracy when trained in isolation",
            metadata={
                "timestamp": (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "research_note",
                "domain": "machine_learning",
                "confidence": 0.9
            },
            tags=["lottery-ticket", "sparse-networks", "pruning"],
            media=[{
                "type": "document",
                "url": "https://arxiv.org/abs/1803.03635",
                "title": "The Lottery Ticket Hypothesis",
                "embedding": await self.get_embedding("lottery ticket hypothesis sparse neural networks")
            }]
        )
        
        # Store AI response with causality
        response_id = await self.store_memory(
            content="Based on the Lottery Ticket Hypothesis and recent work, theoretical sparsity limits "
                   "appear to be around 90-95% for many architectures while maintaining accuracy. "
                   "The key insight is that sparse subnetworks exist from initialization.",
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "conversation",
                "participants": ["claude", "prof.zhang@university.edu"],
                "thread_id": "email-thread-sparse-nn",
                "domain": "machine_learning",
                "confidence": 0.85
            },
            tags=["faculty:claude", "domain:ml", "sparse-networks", "email-response"],
            causality={
                "parent_memories": [email1_id, paper_id],
                "influence_strength": [0.9, 0.8],
                "synthesis_type": "response_with_citation",
                "reasoning": "Answering professor's question using lottery ticket research"
            }
        )
        print(f"Stored response with causality links: {response_id}")
        
        # Verify thread continuity
        thread_memories = await self.search_memories(
            "sparse networks email conversation",
            tags=["email-conversation", "email-response"]
        )
        print(f"Thread continuity check: Found {len(thread_memories)} memories in conversation")
        
    async def test_cross_domain_linking(self):
        """Test 2: Cross-Domain Knowledge Linking"""
        print("\n=== Test 2: Cross-Domain Knowledge Linking ===")
        
        # ML memory
        ml_id = await self.store_memory(
            content="Attention mechanisms in transformers selectively focus on relevant tokens, "
                   "similar to selective attention in human cognition",
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "insight",
                "domain": "machine_learning",
                "confidence": 0.9
            },
            tags=["attention", "transformers", "domain:ml"]
        )
        
        # Cognitive science memory
        cogsci_id = await self.store_memory(
            content="Human visual attention uses feature integration theory to bind features "
                   "into coherent objects, filtering irrelevant information",
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "gpt4-faculty-002",
                "memory_type": "fact",
                "domain": "cognitive_science",
                "confidence": 0.95
            },
            tags=["attention", "vision", "domain:cogsci"]
        )
        
        # Neuroscience memory
        neuro_id = await self.store_memory(
            content="The pulvinar nucleus coordinates attention across cortical areas through "
                   "synchronized oscillations in the alpha band",
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "research_finding",
                "domain": "neuroscience",
                "confidence": 0.88
            },
            tags=["attention", "brain", "domain:neuro"]
        )
        
        # Cross-domain synthesis
        synthesis_id = await self.store_memory(
            content="Attention mechanisms across domains share common principles: selective filtering, "
                   "feature binding, and coordinated processing. This suggests deep computational "
                   "principles that transcend specific implementations.",
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "cross_domain_insight",
                "domain": "interdisciplinary",
                "confidence": 0.85
            },
            tags=["attention", "cross-domain", "synthesis"],
            causality={
                "parent_memories": [ml_id, cogsci_id, neuro_id],
                "influence_strength": [0.8, 0.9, 0.7],
                "synthesis_type": "cross_domain_connection",
                "reasoning": "Identifying common attention principles across ML, CogSci, and Neuro"
            }
        )
        
        # Test cross-domain search
        print("\nSearching for 'attention mechanisms'...")
        results = await self.search_memories("attention mechanisms across different fields")
        print(f"Found {len(results)} cross-domain connections")
        for r in results[:3]:
            print(f"  - {r['metadata']['domain']}: {r['content_preview'][:80]}...")
    
    async def test_multimedia_integration(self):
        """Test 3: Multimedia Memory Integration"""
        print("\n=== Test 3: Multimedia Memory Integration ===")
        
        # Memory with multiple media types
        multimedia_id = await self.store_memory(
            content="Comprehensive study on neural architecture search showing automated discovery "
                   "of efficient architectures. Includes visualizations and benchmarks.",
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "research_review",
                "domain": "machine_learning",
                "confidence": 0.92
            },
            tags=["nas", "architecture-search", "benchmarks"],
            media=[
                {
                    "type": "image",
                    "url": "https://example.com/nas-comparison-chart.png",
                    "description": "Performance comparison of NAS methods",
                    "embedding": await self.get_embedding("neural architecture search performance comparison chart")
                },
                {
                    "type": "website",
                    "url": "https://automl.org/",
                    "title": "AutoML Resources",
                    "preview_text": "Automated machine learning resources and benchmarks",
                    "embedding": await self.get_embedding("automated machine learning automl resources")
                },
                {
                    "type": "document",
                    "url": "https://arxiv.org/abs/1234.5678",
                    "title": "Neural Architecture Search: A Survey",
                    "authors": ["Smith, J.", "Doe, A."],
                    "embedding": await self.get_embedding("neural architecture search survey paper")
                }
            ]
        )
        print(f"Stored multimedia memory: {multimedia_id}")
        
        # Search using content from different media
        print("\nSearching based on visual content description...")
        visual_results = await self.search_memories("performance comparison charts visualization")
        print(f"Found {len(visual_results)} memories with visual content")
        
        # Get full memory details
        response = await self.client.get(f"{self.base_url}/cam/memory/{multimedia_id}")
        memory_details = response.json()
        print(f"Retrieved memory has {len(memory_details['content']['media'])} media items")
    
    async def test_annotation_collaboration(self):
        """Test 4: Annotation & Collaboration"""
        print("\n=== Test 4: Annotation & Collaboration ===")
        
        # Create a memory
        base_memory_id = await self.store_memory(
            content="Proposal: Using knowledge distillation to transfer capabilities from "
                   "large models to smaller, energy-efficient ones",
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "claude-faculty-001",
                "memory_type": "proposal",
                "domain": "machine_learning",
                "confidence": 0.8
            },
            tags=["knowledge-distillation", "efficiency", "proposal"]
        )
        
        # Multiple agents annotate
        annotations = [
            {
                "annotator_id": "research-assistant-007",
                "annotation": {
                    "type": "validation",
                    "content": "Tested this approach on BERT models - achieved 95% performance with 50% size reduction",
                    "confidence": 0.95,
                    "tags": ["validated", "bert"],
                    "evidence_links": ["experiment-log-123"]
                }
            },
            {
                "annotator_id": "gpt4-faculty-002",
                "annotation": {
                    "type": "theoretical_concern",
                    "content": "Consider information bottleneck theory - some capabilities may not transfer",
                    "confidence": 0.7,
                    "tags": ["theory", "limitation"],
                    "vector": await self.get_embedding("information bottleneck theory knowledge distillation")
                }
            },
            {
                "annotator_id": "claude-faculty-003",
                "annotation": {
                    "type": "application_idea",
                    "content": "This could be applied to edge computing scenarios for IoT devices",
                    "confidence": 0.85,
                    "tags": ["application", "iot", "edge-computing"]
                }
            }
        ]
        
        # Add annotations
        for ann in annotations:
            response = await self.client.post(
                f"{self.base_url}/cam/memory/{base_memory_id}/annotate",
                json=ann
            )
            print(f"Added annotation from {ann['annotator_id']}")
        
        # Retrieve annotations
        response = await self.client.get(f"{self.base_url}/cam/memory/{base_memory_id}/annotations")
        retrieved_annotations = response.json()["annotations"]
        print(f"Retrieved {len(retrieved_annotations)} annotations")
        
        # Search for memories with specific annotation tags
        annotated_results = await self.search_memories(
            "knowledge distillation validation edge computing",
            tags=["proposal"]
        )
        print(f"Found {len(annotated_results)} relevant annotated memories")
    
    async def test_scale_performance(self):
        """Test 5: Real-World Scale Test"""
        print("\n=== Test 5: Real-World Scale Test ===")
        
        # Bulk insert memories
        print("Inserting 100 memories...")
        start_time = time.time()
        
        domains = ["machine_learning", "cognitive_science", "neuroscience", "computer_vision", "nlp"]
        memory_types = ["fact", "insight", "conversation", "research_note", "question"]
        
        bulk_ids = []
        for i in range(100):
            content = f"Memory {i}: " + random.choice([
                "Neural network optimization techniques for edge devices",
                "Cognitive load theory in human-computer interaction",
                "Visual cortex processing hierarchies and deep learning",
                "Language model fine-tuning strategies",
                "Attention mechanisms in biological and artificial systems",
                "Sparse coding principles in sensory processing",
                "Transfer learning across different domains",
                "Memory consolidation in hippocampal circuits",
                "Transformer architectures for multimodal learning",
                "Reinforcement learning in decision making"
            ])
            
            memory_id = await self.store_memory(
                content=content + f" - variation {i}",
                metadata={
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "agent_id": f"test-agent-{i % 5}",
                    "memory_type": random.choice(memory_types),
                    "domain": random.choice(domains),
                    "confidence": random.uniform(0.7, 0.95)
                },
                tags=[f"bulk-test", f"domain:{random.choice(domains)}", f"batch-{i//10}"]
            )
            bulk_ids.append(memory_id)
            
            if i % 20 == 0:
                print(f"  Progress: {i}/100 memories")
        
        insert_time = time.time() - start_time
        print(f"Bulk insert completed in {insert_time:.2f} seconds")
        print(f"Average: {insert_time/100:.3f} seconds per memory")
        
        # Test search performance
        print("\nTesting search performance...")
        search_queries = [
            "neural network optimization",
            "attention mechanisms",
            "cognitive processing",
            "transfer learning",
            "memory consolidation"
        ]
        
        search_times = []
        for query in search_queries:
            start = time.time()
            results = await self.search_memories(query, top_k=10)
            search_time = (time.time() - start) * 1000  # Convert to ms
            search_times.append(search_time)
            print(f"  Query '{query}': {len(results)} results in {search_time:.1f}ms")
        
        avg_search_time = sum(search_times) / len(search_times)
        print(f"\nAverage search time: {avg_search_time:.1f}ms")
        
        # Test vector search accuracy
        print("\nTesting vector search accuracy...")
        # Create a very specific memory
        specific_content = "Quantum computing applications in cryptographic key distribution using BB84 protocol"
        specific_id = await self.store_memory(
            content=specific_content,
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "accuracy-test",
                "memory_type": "fact",
                "domain": "quantum_computing",
                "confidence": 0.99
            },
            tags=["quantum", "cryptography", "bb84"]
        )
        
        # Search for it with a related query
        results = await self.search_memories("quantum cryptography BB84 protocol key distribution")
        
        # Check if our specific memory is in top results
        found_rank = None
        for i, result in enumerate(results):
            if result["memory_id"] == specific_id:
                found_rank = i + 1
                break
        
        if found_rank:
            print(f"Specific memory found at rank {found_rank} with score {results[found_rank-1]['similarity_score']:.3f}")
        else:
            print("Warning: Specific memory not found in top results")
        
        print(f"\nTotal memories created in test suite: {len(self.memories_created)}")
    
    async def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Engram Comprehensive Test Suite")
        print("==================================")
        
        # Check if Engram is running
        try:
            response = await self.client.get(f"{self.base_url}/health")
            health = response.json()
            print(f"✅ Engram status: {health['status']}")
            print(f"✅ Redis: {health['redis']}")
            print(f"✅ Vector index: {health['vector_index']}")
        except Exception as e:
            print(f"❌ Error: Could not connect to Engram. Is it running?")
            print(f"   {e}")
            return
        
        # Run tests
        try:
            await self.test_email_faculty_flow()
            await self.test_cross_domain_linking()
            await self.test_multimedia_integration()
            await self.test_annotation_collaboration()
            await self.test_scale_performance()
            
            print("\n✅ All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
    async def cleanup(self):
        """Clean up resources"""
        await self.client.aclose()


async def main():
    test_suite = EngramTestSuite()
    try:
        await test_suite.run_all_tests()
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    asyncio.run(main())