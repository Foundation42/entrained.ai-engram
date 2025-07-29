#!/usr/bin/env python3
"""
Advanced test suite for Engram - testing complex scenarios
"""

import httpx
import asyncio
from datetime import datetime, timedelta
import json
import random
from typing import List, Dict, Any


class AdvancedEngramTests:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama or generate mock"""
        try:
            response = await self.client.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "nomic-embed-text:latest", "prompt": text}
            )
            if response.status_code == 200:
                return response.json()["embedding"]
        except:
            pass
        
        # Fallback to deterministic mock embedding
        random.seed(hash(text))
        embedding = [random.gauss(0, 1) for _ in range(768)]
        norm = sum(x**2 for x in embedding) ** 0.5
        return [x/norm for x in embedding]
    
    async def store_memory(self, content: str, metadata: Dict[str, Any], 
                          tags: List[str], causality: Dict = None) -> str:
        """Helper to store a memory"""
        embedding = await self.get_embedding(content)
        
        memory = {
            "content": {"text": content, "media": []},
            "primary_vector": embedding,
            "metadata": metadata,
            "tags": tags,
            "causality": causality
        }
        
        response = await self.client.post(f"{self.base_url}/cam/store", json=memory)
        return response.json()["memory_id"]
    
    async def test_causality_chain_depth(self):
        """Test 1: Causality Chain Depth - A→B→C→D→E"""
        print("\n=== Test 1: Causality Chain Depth ===")
        print("Creating a chain of ideas: A→B→C→D→E")
        
        chain_ids = []
        chain_content = [
            ("A", "Foundation: Neurons in the brain communicate through electrical signals"),
            ("B", "Discovery: Artificial neurons can mimic biological signal processing"),
            ("C", "Innovation: Deep neural networks stack multiple layers of artificial neurons"),
            ("D", "Breakthrough: Transformer architectures enable parallel processing of sequences"),
            ("E", "Application: Large language models emerge from scaled transformer architectures")
        ]
        
        # Create the chain
        for i, (label, content) in enumerate(chain_content):
            metadata = {
                "timestamp": (datetime.utcnow() - timedelta(days=len(chain_content)-i)).isoformat() + "Z",
                "agent_id": "historian-001",
                "memory_type": "historical_progression",
                "domain": "ai_history",
                "confidence": 0.95
            }
            
            causality = None
            if i > 0:
                # Each memory builds on the previous one
                causality = {
                    "parent_memories": [chain_ids[i-1]],
                    "influence_strength": [0.9],
                    "synthesis_type": "logical_progression",
                    "reasoning": f"{label} builds directly on {chain_content[i-1][0]}"
                }
            
            memory_id = await self.store_memory(
                content=f"{label}: {content}",
                metadata=metadata,
                tags=["history", "ai-evolution", f"stage-{label}"],
                causality=causality
            )
            chain_ids.append(memory_id)
            print(f"   ✓ Created {label}: {memory_id}")
        
        # Test retrieval of the full chain
        print("\nTracing causality from E back to A:")
        
        # Get memory E details
        response = await self.client.get(f"{self.base_url}/cam/memory/{chain_ids[-1]}")
        memory_e = response.json()
        print(f"   E ({chain_ids[-1]}): {memory_e['content']['text'][:60]}...")
        
        # TODO: When causality chain endpoint is implemented, trace full genealogy
        # For now, we verify the parent relationship was stored
        if memory_e.get('causality', {}).get('parent_memories'):
            print(f"   └─> Parent: {memory_e['causality']['parent_memories'][0]}")
        
        # Wait for indexing
        await asyncio.sleep(0.5)
        
        # Search for memories related to "neural evolution"
        query_embedding = await self.get_embedding("evolution of neural architectures from biology to AI")
        search_response = await self.client.post(
            f"{self.base_url}/cam/retrieve",
            json={
                "resonance_vectors": [{"vector": query_embedding, "weight": 1.0}],
                "retrieval": {"top_k": 10, "similarity_threshold": 0.0}
            }
        )
        
        results = search_response.json()
        print(f"\nSearching for 'neural evolution' found {results['total_found']} memories")
        chain_found = sum(1 for r in results['memories'] if r['memory_id'] in chain_ids)
        print(f"   Chain memories in results: {chain_found}/{len(chain_ids)}")
    
    async def test_memory_conflict_resolution(self):
        """Test 2: Memory Conflict Resolution"""
        print("\n=== Test 2: Memory Conflict Resolution ===")
        print("Creating conflicting memories about the same topic")
        
        # Store conflicting information about coffee's effects
        conflict_topic = "coffee consumption and productivity"
        
        # Memory 1: Coffee improves productivity
        memory1_id = await self.store_memory(
            content="Studies show coffee consumption increases productivity by 20% due to enhanced focus",
            metadata={
                "timestamp": (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z",
                "agent_id": "researcher-001",
                "memory_type": "research_finding",
                "domain": "productivity",
                "confidence": 0.85,
                "source": "Journal of Workplace Efficiency, 2023"
            },
            tags=["coffee", "productivity", "positive-effect", "research"]
        )
        print(f"   ✓ Stored Memory 1 (pro-coffee): {memory1_id}")
        
        # Memory 2: Coffee decreases productivity
        memory2_id = await self.store_memory(
            content="Coffee consumption leads to productivity crashes and 15% decrease in afternoon performance",
            metadata={
                "timestamp": (datetime.utcnow() - timedelta(days=20)).isoformat() + "Z",
                "agent_id": "researcher-002",
                "memory_type": "research_finding",
                "domain": "productivity",
                "confidence": 0.80,
                "source": "Sleep and Performance Quarterly, 2024"
            },
            tags=["coffee", "productivity", "negative-effect", "research"]
        )
        print(f"   ✓ Stored Memory 2 (anti-coffee): {memory2_id}")
        
        # Memory 3: Synthesis of conflicting views
        memory3_id = await self.store_memory(
            content="Coffee's effect on productivity is context-dependent: beneficial for morning tasks but detrimental for sustained afternoon work",
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_id": "synthesizer-001",
                "memory_type": "conflict_resolution",
                "domain": "productivity",
                "confidence": 0.90
            },
            tags=["coffee", "productivity", "nuanced-view", "synthesis"],
            causality={
                "parent_memories": [memory1_id, memory2_id],
                "influence_strength": [0.7, 0.7],
                "synthesis_type": "conflict_resolution",
                "reasoning": "Reconciling contradictory findings through contextual analysis"
            }
        )
        print(f"   ✓ Stored Memory 3 (synthesis): {memory3_id}")
        
        # Add annotations to track conflict
        annotation1 = {
            "annotator_id": "conflict-detector",
            "annotation": {
                "type": "conflict_flag",
                "content": "This finding conflicts with memory " + memory2_id,
                "confidence": 0.95,
                "tags": ["conflict", "requires-resolution"]
            }
        }
        await self.client.post(f"{self.base_url}/cam/memory/{memory1_id}/annotate", json=annotation1)
        
        # Wait for indexing
        await asyncio.sleep(0.5)
        
        # Search for coffee productivity info
        query_embedding = await self.get_embedding("coffee impact on work productivity")
        search_response = await self.client.post(
            f"{self.base_url}/cam/retrieve",
            json={
                "resonance_vectors": [{"vector": query_embedding, "weight": 1.0}],
                "retrieval": {"top_k": 5, "similarity_threshold": 0.0}
            }
        )
        
        results = search_response.json()
        print(f"\nSearching for 'coffee productivity' returns {results['total_found']} memories:")
        for mem in results['memories'][:3]:
            tags = ', '.join([t for t in mem['tags'] if 'effect' in t or 'synthesis' in t])
            print(f"   - {mem['memory_id']}: {tags} (confidence: {mem['metadata'].get('confidence', 'N/A')})")
        
        print("\nConflict Resolution Strategy:")
        print("   1. Both conflicting views are preserved")
        print("   2. Synthesis memory links to both parents")
        print("   3. Confidence scores help weight contradictions")
        print("   4. Annotations flag conflicts for attention")
    
    async def test_temporal_decay_simulation(self):
        """Test 3: Temporal Decay Simulation"""
        print("\n=== Test 3: Temporal Decay Simulation ===")
        print("Creating memories with different ages and importance scores")
        
        # Create memories at different time points
        time_points = [
            (365, "Ancient wisdom: The fundamental principles of logic established by Aristotle", 0.95),
            (180, "Classical knowledge: Newton's laws of motion govern macroscopic physics", 0.90),
            (90, "Modern insight: Quantum mechanics reveals probabilistic nature of reality", 0.85),
            (30, "Recent discovery: Room-temperature superconductor claims need verification", 0.70),
            (7, "Current event: New AI model achieves breakthrough in reasoning tasks", 0.75),
            (1, "Breaking news: Tech company announces revolutionary brain-computer interface", 0.60),
            (0, "Just learned: Coffee helps with morning productivity", 0.40)
        ]
        
        memory_ids = []
        for days_ago, content, importance in time_points:
            timestamp = (datetime.utcnow() - timedelta(days=days_ago)).isoformat() + "Z"
            
            memory_id = await self.store_memory(
                content=content,
                metadata={
                    "timestamp": timestamp,
                    "agent_id": "temporal-test",
                    "memory_type": "fact",
                    "domain": "science",
                    "confidence": 0.8,
                    "importance": importance,
                    "decay_rate": 0.1 if importance > 0.8 else 0.5  # Important memories decay slower
                },
                tags=["temporal-test", f"age-{days_ago}d", f"importance-{int(importance*10)}"],
                causality=None
            )
            memory_ids.append((memory_id, days_ago, importance))
            print(f"   ✓ Stored: {days_ago}d old, importance={importance}: {content[:50]}...")
        
        # Search with recency boosting
        query_embedding = await self.get_embedding("important scientific knowledge and discoveries")
        
        # Search WITHOUT recency boost
        print("\nSearch results WITHOUT recency boost:")
        search_response = await self.client.post(
            f"{self.base_url}/cam/retrieve",
            json={
                "resonance_vectors": [{"vector": query_embedding, "weight": 1.0}],
                "retrieval": {"top_k": 7, "similarity_threshold": 0.0}
            }
        )
        
        results = search_response.json()
        for i, mem in enumerate(results['memories'], 1):
            age_tag = next((t for t in mem['tags'] if t.startswith('age-')), 'unknown')
            imp_tag = next((t for t in mem['tags'] if t.startswith('importance-')), 'unknown')
            print(f"   {i}. {age_tag}, {imp_tag}: {mem['content_preview'][:50]}...")
        
        # Simulate importance decay calculation
        print("\nSimulated importance with temporal decay:")
        for mem_id, days_ago, original_imp in memory_ids:
            # Simple decay formula: importance * e^(-decay_rate * days/365)
            decay_rate = 0.1 if original_imp > 0.8 else 0.5
            import math
            decayed_importance = original_imp * math.exp(-decay_rate * days_ago / 365)
            print(f"   {days_ago}d old: {original_imp:.2f} → {decayed_importance:.2f} "
                  f"({'slow' if decay_rate == 0.1 else 'fast'} decay)")
        
        print("\nTemporal Decay Insights:")
        print("   - High-importance memories (>0.8) decay slowly")
        print("   - Low-importance memories decay quickly")
        print("   - Ancient wisdom with high importance remains relevant")
        print("   - Recent trivia fades fast despite recency")
    
    async def test_agent_personality_consistency(self):
        """Test 4: Agent Personality Consistency"""
        print("\n=== Test 4: Agent Personality Consistency ===")
        print("Creating memories from agents with distinct personalities")
        
        # Define agent personalities
        agents = [
            {
                "id": "optimist-001",
                "personality": "enthusiastic and positive",
                "topics": [
                    "AI will solve climate change through innovative optimization algorithms!",
                    "Every challenge is an opportunity for breakthrough discoveries!",
                    "The future of technology is incredibly bright and full of potential!"
                ],
                "style_markers": ["exciting", "amazing", "wonderful", "breakthrough"]
            },
            {
                "id": "skeptic-001", 
                "personality": "cautious and analytical",
                "topics": [
                    "AI claims require rigorous validation before acceptance",
                    "We must carefully consider the limitations and biases in our models",
                    "Technology promises should be tempered with realistic expectations"
                ],
                "style_markers": ["however", "consider", "evidence suggests", "caution"]
            },
            {
                "id": "pragmatist-001",
                "personality": "practical and results-focused",
                "topics": [
                    "AI works best when applied to specific, well-defined problems",
                    "Implementation details matter more than theoretical possibilities",
                    "Let's focus on what delivers measurable value today"
                ],
                "style_markers": ["practical", "specific", "measurable", "implementation"]
            }
        ]
        
        # Store memories for each agent
        agent_memories = {}
        for agent in agents:
            agent_memories[agent['id']] = []
            print(f"\n   Agent: {agent['id']} ({agent['personality']})")
            
            for topic in agent['topics']:
                memory_id = await self.store_memory(
                    content=topic,
                    metadata={
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "agent_id": agent['id'],
                        "memory_type": "opinion",
                        "domain": "ai_philosophy",
                        "confidence": 0.85,
                        "personality_traits": agent['personality'],
                        "communication_style": agent['style_markers']
                    },
                    tags=["personality-test", agent['id'], "opinion"] + agent['style_markers'][:2]
                )
                agent_memories[agent['id']].append(memory_id)
                print(f"      ✓ {topic[:60]}...")
        
        # Test personality consistency in retrieval
        print("\n\nTesting personality-aware retrieval:")
        
        # Query 1: Looking for optimistic views
        query1 = "exciting breakthroughs in AI technology"
        embedding1 = await self.get_embedding(query1)
        
        response1 = await self.client.post(
            f"{self.base_url}/cam/retrieve",
            json={
                "resonance_vectors": [{"vector": embedding1, "weight": 1.0}],
                "filters": {"agent_ids": ["optimist-001"]},
                "retrieval": {"top_k": 3, "similarity_threshold": 0.0}
            }
        )
        
        results1 = response1.json()
        print(f"\n   Query: '{query1}' (filtering for optimist)")
        print(f"   Found {results1['total_found']} memories from optimist-001")
        
        # Query 2: Looking for cautious views
        query2 = "AI limitations and careful analysis"
        embedding2 = await self.get_embedding(query2)
        
        response2 = await self.client.post(
            f"{self.base_url}/cam/retrieve",
            json={
                "resonance_vectors": [{"vector": embedding2, "weight": 1.0}],
                "filters": {"agent_ids": ["skeptic-001"]},
                "retrieval": {"top_k": 3, "similarity_threshold": 0.0}
            }
        )
        
        results2 = response2.json()
        print(f"\n   Query: '{query2}' (filtering for skeptic)")
        print(f"   Found {results2['total_found']} memories from skeptic-001")
        
        # Query 3: Mixed retrieval - let personalities emerge naturally
        query3 = "AI development approaches and perspectives"
        embedding3 = await self.get_embedding(query3)
        
        response3 = await self.client.post(
            f"{self.base_url}/cam/retrieve",
            json={
                "resonance_vectors": [{"vector": embedding3, "weight": 1.0}],
                "retrieval": {"top_k": 9, "similarity_threshold": 0.0}
            }
        )
        
        results3 = response3.json()
        print(f"\n   Query: '{query3}' (no filter - all personalities)")
        
        # Count memories by agent
        agent_counts = {}
        for mem in results3['memories']:
            agent = mem['metadata'].get('agent_id', 'unknown')
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        print("   Distribution of perspectives:")
        for agent, count in agent_counts.items():
            personality = next((a['personality'] for a in agents if a['id'] == agent), 'unknown')
            print(f"      {agent} ({personality}): {count} memories")
        
        print("\n   Personality Consistency Features:")
        print("   - Agent metadata preserved through storage/retrieval")
        print("   - Personality traits stored for context")
        print("   - Communication style markers enable personality-aware search")
        print("   - Filtering by agent maintains voice consistency")
    
    async def run_all_advanced_tests(self):
        """Run all advanced tests"""
        print("🧪 Advanced Engram Test Suite")
        print("=============================")
        
        try:
            # Check if Engram is running
            response = await self.client.get(f"{self.base_url}/health")
            health = response.json()
            if health['status'] != 'healthy':
                print("❌ Engram is not healthy!")
                return
            
            print("✅ Engram is running\n")
            
            # Run tests
            await self.test_causality_chain_depth()
            await self.test_memory_conflict_resolution()
            await self.test_temporal_decay_simulation()
            await self.test_agent_personality_consistency()
            
            print("\n✅ All advanced tests completed!")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    async def cleanup(self):
        """Clean up resources"""
        await self.client.aclose()


async def main():
    # Don't flush Redis - just run the tests
    # This preserves the index while still testing new data
    print("Running advanced tests...")
    
    # Run tests
    test_suite = AdvancedEngramTests()
    try:
        await test_suite.run_all_advanced_tests()
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    asyncio.run(main())