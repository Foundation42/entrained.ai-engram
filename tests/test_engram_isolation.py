#!/usr/bin/env python3
"""
Isolated Engram Memory System Test

This test directly calls the Engram server APIs to verify memory storage and retrieval
without depending on the Agent Team's infrastructure. Helps debug memory system issues.
"""
import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class TestEntity:
    name: str
    entity_id: str
    location: str 
    skills: List[str]
    unique_fact: str

class EngramIsolationTester:
    def __init__(self, engram_url: str = "http://46.62.130.230:8000"):
        self.engram_url = engram_url
        self.agent_id = "agent-claude-prime"
        
        # Create test entities
        self.entities = [
            TestEntity(
                name="Christian",
                entity_id="human-christian-kind-hare",
                location="Liversedge, West Yorkshire", 
                skills=["Python", "AI systems"],
                unique_fact="loves programming on rainy days"
            ),
            TestEntity(
                name="Daniel", 
                entity_id="human-daniel-wise-fox",
                location="Manchester, England",
                skills=["JavaScript", "React"],
                unique_fact="prefers coffee over tea"
            ),
            TestEntity(
                name="Sarah",
                entity_id="human-sarah-brave-owl", 
                location="Edinburgh, Scotland",
                skills=["R", "Statistics"],
                unique_fact="climbs mountains on weekends"
            )
        ]

    async def run_comprehensive_test(self):
        """Run comprehensive memory isolation test"""
        print("🧪 ENGRAM MEMORY ISOLATION TEST")
        print("=" * 80)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Phase 1: Clear database
            await self._clear_database(client)
            
            # Phase 2: Store memories for each entity
            await self._store_entity_memories(client)
            
            # Phase 3: Check storage statistics
            await self._check_storage_stats(client)
            
            # Phase 4: Test direct retrieval
            await self._test_direct_retrieval(client)
            
            # Phase 5: Test curation analysis
            await self._test_curation_analysis(client)

    async def _clear_database(self, client: httpx.AsyncClient):
        """Clear the database using admin endpoint"""
        print("\n📋 PHASE 1: Database Cleanup")
        print("-" * 50)
        
        try:
            response = await client.post(
                f"{self.engram_url}/api/v1/admin/flush/memories",
                auth=("admin", "engram-admin-2025")
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Database cleared: {result.get('deleted_count', 0)} keys deleted")
            else:
                print(f"⚠️ Clear failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Clear error: {e}")

    async def _store_entity_memories(self, client: httpx.AsyncClient):
        """Store memories for each test entity"""
        print("\n📋 PHASE 2: Memory Storage")
        print("-" * 50)
        
        for entity in self.entities:
            print(f"\n💾 Storing memories for {entity.name} ({entity.entity_id})")
            
            # Create conversation content
            user_message = f"Hi! My name is {entity.name} and I live in {entity.location}. I'm skilled in {', '.join(entity.skills)}. Here's something unique about me: {entity.unique_fact}."
            agent_response = f"Hello {entity.name}! Nice to meet you. I'll remember that you're from {entity.location} and skilled in {', '.join(entity.skills)}."
            
            # Test curated storage
            await self._store_curated_memory(client, entity, user_message, agent_response)

    async def _store_curated_memory(self, client: httpx.AsyncClient, entity: TestEntity, user_input: str, agent_response: str):
        """Store a curated memory for an entity"""
        try:
            # First analyze the memory
            analysis_response = await client.post(
                f"{self.engram_url}/cam/curated/analyze",
                json={
                    "user_input": user_input,
                    "agent_response": agent_response,
                    "conversation_context": f"Introduction conversation with {entity.name}",
                    "curation_preferences": {
                        "priority_topics": ["personal_info", "technical_details"],
                        "retention_bias": "balanced",
                        "agent_personality": "helpful_assistant"
                    }
                }
            )
            
            if analysis_response.status_code == 200:
                analysis = analysis_response.json()
                print(f"  📊 Analysis: should_store={analysis.get('should_store', False)}, confidence={analysis.get('confidence_score', 0):.2f}")
                
                if analysis.get('should_store', False):
                    # Store the memory
                    storage_response = await client.post(
                        f"{self.engram_url}/cam/curated/store",
                        json={
                            "witnessed_by": [entity.entity_id, self.agent_id],
                            "situation_id": f"sit-{entity.name.lower()}-intro-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            "situation_type": "introduction_conversation",
                            "content": {
                                "text": f"User: {user_input}\nAssistant: {agent_response}",
                                "summary": f"Introduction conversation with {entity.name}",
                                "speakers": {
                                    entity.entity_id: user_input,
                                    self.agent_id: agent_response
                                }
                            },
                            "primary_vector": [0.1 + (i * 0.001) for i in range(settings.vector_dimensions)],  # Unique vector for testing
                            "metadata": {
                                "timestamp": datetime.now().isoformat(),
                                "interaction_quality": 1.0,
                                "topic_tags": ["introduction", "personal_info"]
                            },
                            "access_control": {
                                "privacy_level": "participants_only"
                            },
                            "user_input": user_input,
                            "agent_response": agent_response,
                            "conversation_context": f"Introduction with {entity.name}"
                        }
                    )
                    
                    if storage_response.status_code == 200:
                        result = storage_response.json()
                        print(f"  ✅ Stored: memory_id={result.get('memory_id', 'unknown')}")
                    else:
                        print(f"  ❌ Storage failed: {storage_response.status_code} - {storage_response.text[:100]}")
                else:
                    print(f"  ⚠️ Analysis rejected storage")
            else:
                print(f"  ❌ Analysis failed: {analysis_response.status_code} - {analysis_response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ Error storing memory: {e}")

    async def _check_storage_stats(self, client: httpx.AsyncClient):
        """Check storage statistics for each entity"""
        print("\n📋 PHASE 3: Storage Statistics")
        print("-" * 50)
        
        for entity in self.entities:
            try:
                response = await client.get(
                    f"{self.engram_url}/cam/curated/stats/{entity.entity_id}"
                )
                
                if response.status_code == 200:
                    stats = response.json()
                    total = stats.get('total_memories', 0)
                    confidence = stats.get('average_confidence_score', 0)
                    print(f"📊 {entity.name}: {total} memories, avg confidence: {confidence:.2f}")
                else:
                    print(f"❌ Stats failed for {entity.name}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Stats error for {entity.name}: {e}")

    async def _test_direct_retrieval(self, client: httpx.AsyncClient):
        """Test direct memory retrieval for each entity"""
        print("\n📋 PHASE 4: Direct Memory Retrieval")
        print("-" * 50)
        
        test_queries = [
            "What is my name?",
            "Where do I live?", 
            "What are my skills?",
            "What's unique about me?"
        ]
        
        for entity in self.entities:
            print(f"\n🧠 Testing retrieval for {entity.name}")
            
            for query in test_queries:
                try:
                    response = await client.post(
                        f"{self.engram_url}/cam/curated/retrieve",
                        json={
                            "requesting_entity": entity.entity_id,
                            "resonance_vectors": [
                                {
                                    "vector": [0.1] * settings.vector_dimensions,  # Dummy vector for testing
                                    "weight": 1.0,
                                    "source": query
                                }
                            ],
                            "entity_filters": {
                                "witnessed_by_includes": [entity.entity_id]
                            },
                            "retrieval_options": {
                                "top_k": 5,
                                "similarity_threshold": 0.1,  # Low threshold for testing
                                "include_speakers_breakdown": True
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        memories = result.get('memories', [])
                        print(f"  🔍 '{query}' → {len(memories)} memories found")
                        
                        if memories:
                            # Show first memory content preview
                            first_memory = memories[0]
                            content = first_memory.get('content', {}).get('summary', 'No summary')[:100]
                            print(f"      💭 Preview: {content}...")
                        else:
                            print(f"      ⚠️ No memories found for query")
                    else:
                        print(f"  ❌ Retrieval failed: {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ Retrieval error: {e}")

    async def _test_curation_analysis(self, client: httpx.AsyncClient):
        """Test curation analysis functionality"""
        print("\n📋 PHASE 5: Curation Analysis Test")
        print("-" * 50)
        
        test_cases = [
            {
                "name": "High Value Facts",
                "user_input": "My name is TestUser and I'm a Python developer from London",
                "agent_response": "Nice to meet you TestUser! I'll remember you're a Python developer from London."
            },
            {
                "name": "Weather (Should Filter)",
                "user_input": "It's raining today and I'm feeling tired",
                "agent_response": "Sorry about the weather! Hope you feel better soon."
            }
        ]
        
        for test_case in test_cases:
            try:
                response = await client.post(
                    f"{self.engram_url}/cam/curated/analyze",
                    json={
                        "user_input": test_case["user_input"],
                        "agent_response": test_case["agent_response"],
                        "conversation_context": "Test analysis"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    should_store = result.get('should_store', False)
                    confidence = result.get('confidence_score', 0)
                    observations = len(result.get('observations', []))
                    
                    print(f"🧪 {test_case['name']}: store={should_store}, confidence={confidence:.2f}, observations={observations}")
                else:
                    print(f"❌ Analysis failed for {test_case['name']}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Analysis error for {test_case['name']}: {e}")

async def main():
    """Run the comprehensive Engram isolation test"""
    tester = EngramIsolationTester()
    await tester.run_comprehensive_test()
    
    print("\n" + "=" * 80)
    print("🎯 ENGRAM ISOLATION TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())