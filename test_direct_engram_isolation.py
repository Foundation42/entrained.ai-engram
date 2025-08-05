#!/usr/bin/env python3
"""
Direct Engram API Memory Isolation Test

This test directly calls the Engram API endpoints (/cam/curated/*) to verify
memory isolation and the Columbo curation system, bypassing the agent layer.

Test Coverage:
1. Direct storage via /cam/curated/store
2. Direct retrieval via /cam/curated/retrieve  
3. Direct analysis via /cam/curated/analyze
4. Multi-entity isolation verification
5. Cross-contamination detection
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
    preferences: List[str]
    unique_fact: str

class DirectEngramIsolationTester:
    def __init__(self, engram_url: str = "http://46.62.130.230:8000"):
        self.engram_url = engram_url
        self.agent_id = "agent-claude-prime"
        
        # Create distinct test entities
        self.entities = [
            TestEntity(
                name="Christian",
                entity_id="human-christian-kind-hare",
                location="Liversedge, West Yorkshire", 
                skills=["Python", "AI systems", "Machine Learning"],
                preferences=["technical discussions", "programming", "rainy weather"],
                unique_fact="loves programming on rainy days"
            ),
            TestEntity(
                name="Daniel", 
                entity_id="human-daniel-wise-fox",
                location="Manchester, England",
                skills=["JavaScript", "React", "Node.js"],
                preferences=["web development", "coffee", "sunny weather"], 
                unique_fact="drinks 5 cups of coffee daily"
            ),
            TestEntity(
                name="Sarah",
                entity_id="human-sarah-brave-owl", 
                location="London, England",
                skills=["Data Science", "R", "Statistics"],
                preferences=["data analysis", "tea", "classical music"],
                unique_fact="has a PhD in Statistics from Oxford"
            )
        ]
        
        self.test_results = []
        
    async def run_comprehensive_test(self):
        """Run the complete direct Engram API test suite"""
        print("🧪 DIRECT ENGRAM API MEMORY ISOLATION TEST")
        print("=" * 80)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            
            # Phase 1: System health check
            print("\n📋 PHASE 1: System Health Check")
            print("-" * 50)
            await self._check_system_health(client)
            
            # Phase 2: Direct storage testing
            print("\n📋 PHASE 2: Direct Storage Testing")
            print("-" * 50)
            await self._test_direct_storage(client)
            
            # Phase 3: Direct retrieval testing
            print("\n📋 PHASE 3: Direct Retrieval Testing")
            print("-" * 50)
            await self._test_direct_retrieval(client)
            
            # Phase 4: Analysis endpoint testing
            print("\n📋 PHASE 4: Analysis Endpoint Testing")
            print("-" * 50)
            await self._test_analysis_endpoint(client)
            
            # Phase 5: Memory isolation verification
            print("\n📋 PHASE 5: Memory Isolation Verification")
            print("-" * 50)
            await self._test_memory_isolation(client)
            
            # Phase 6: Statistics verification
            print("\n📋 PHASE 6: Statistics Verification")
            print("-" * 50)
            await self._verify_statistics(client)
            
        # Final results
        self._print_final_results()
    
    async def _check_system_health(self, client: httpx.AsyncClient):
        """Check Engram system health"""
        try:
            response = await client.get(f"{self.engram_url}/health")
            if response.status_code == 200:
                health = response.json()
                self._record_result(
                    "System Health",
                    True,
                    f"✅ Engram healthy: {health.get('status', 'unknown')}"
                )
            else:
                self._record_result(
                    "System Health",
                    False,
                    f"❌ Health check failed: {response.status_code}"
                )
        except Exception as e:
            self._record_result(
                "System Health",
                False,
                f"❌ Health check error: {e}"
            )
    
    async def _test_direct_storage(self, client: httpx.AsyncClient):
        """Test direct storage via /cam/curated/store"""
        print("💾 Testing direct storage...")
        
        for entity in self.entities:
            print(f"  📝 Storing information for {entity.name}")
            
            # Create comprehensive introduction
            intro_text = (
                f"Hi! My name is {entity.name} and I live in {entity.location}. "
                f"I work with {', '.join(entity.skills)} and I love {', '.join(entity.preferences)}. "
                f"Here's a unique fact about me: {entity.unique_fact}."
            )
            
            # Generate embedding (using zeros for test - in production would use actual embedding)
            embedding = [0.1] * 768
            
            # Create storage request
            storage_request = {
                "witnessed_by": [entity.entity_id, self.agent_id],
                "situation_type": "consultation_1to1",
                "content": {
                    "text": f"User: {intro_text}\nAssistant: Nice to meet you, {entity.name}!",
                    "content_type": "conversation_turn"
                },
                "primary_vector": embedding,
                "user_input": intro_text,
                "agent_response": f"Nice to meet you, {entity.name}!",
                "conversation_context": f"Introduction from {entity.name}",
                "curation_preferences": {
                    "priority_topics": ["personal_info", "location", "skills", "preferences"],
                    "retention_bias": "balanced",
                    "privacy_sensitivity": "personal",
                    "agent_personality": "technical_specialist"
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "interaction_quality": 0.9,
                    "session_id": f"direct-test-{entity.name.lower()}"
                }
            }
            
            try:
                response = await client.post(
                    f"{self.engram_url}/cam/curated/store",
                    json=storage_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memory_id = result.get("memory_id")
                    storage_type = result.get("curation_decision", {}).get("storage_type")
                    confidence = result.get("curation_decision", {}).get("confidence_score", 0)
                    
                    self._record_result(
                        f"Storage - {entity.name}",
                        True,
                        f"✅ Stored as {storage_type} (confidence: {confidence:.2f}, ID: {memory_id})"
                    )
                else:
                    self._record_result(
                        f"Storage - {entity.name}",
                        False,
                        f"❌ Storage failed: {response.status_code} - {response.text[:100]}..."
                    )
                    
            except Exception as e:
                self._record_result(
                    f"Storage - {entity.name}",
                    False,
                    f"❌ Storage error: {e}"
                )
    
    async def _test_direct_retrieval(self, client: httpx.AsyncClient):
        """Test direct retrieval via /cam/curated/retrieve"""
        print("🧠 Testing direct retrieval...")
        
        for entity in self.entities:
            print(f"  🔍 Testing retrieval for {entity.name}")
            
            # Test name recall
            name_query = "What is my name?"
            embedding = [0.1] * 768  # Simplified for test
            
            retrieval_request = {
                "requesting_entity": entity.entity_id,
                "resonance_vectors": [
                    {"vector": embedding, "weight": 1.0}
                ],
                "query_text": name_query,
                "conversation_context": f"User asking for their name - {entity.name}",
                "retrieval_options": {
                    "top_k": 5,
                    "similarity_threshold": 0.0,
                    "exclude_denials": True
                }
            }
            
            try:
                response = await client.post(
                    f"{self.engram_url}/cam/curated/retrieve",
                    json=retrieval_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get("memories", [])
                    analysis = result.get("retrieval_analysis", {})
                    
                    # Check if any memory contains the entity's name
                    name_found = False
                    for memory in memories:
                        content = memory.get("content_preview", "") or memory.get("content", {}).get("text", "")
                        if entity.name.lower() in content.lower():
                            name_found = True
                            break
                    
                    self._record_result(
                        f"Name Retrieval - {entity.name}",
                        name_found,
                        f"{'✅' if name_found else '❌'} Found {len(memories)} memories, name {'found' if name_found else 'not found'}"
                    )
                    
                    # Test location recall
                    location_query = "Where do I live?"
                    location_request = {**retrieval_request, "query_text": location_query}
                    
                    location_response = await client.post(
                        f"{self.engram_url}/cam/curated/retrieve",
                        json=location_request
                    )
                    
                    if location_response.status_code == 200:
                        location_result = location_response.json()
                        location_memories = location_result.get("memories", [])
                        
                        location_found = False
                        for memory in location_memories:
                            content = memory.get("content_preview", "") or memory.get("content", {}).get("text", "")
                            if any(part.lower() in content.lower() for part in entity.location.split(", ")):
                                location_found = True
                                break
                        
                        self._record_result(
                            f"Location Retrieval - {entity.name}",
                            location_found,
                            f"{'✅' if location_found else '❌'} Location {'found' if location_found else 'not found'} in {len(location_memories)} memories"
                        )
                else:
                    self._record_result(
                        f"Name Retrieval - {entity.name}",
                        False,
                        f"❌ Retrieval failed: {response.status_code} - {response.text[:100]}..."
                    )
                    
            except Exception as e:
                self._record_result(
                    f"Name Retrieval - {entity.name}",
                    False,
                    f"❌ Retrieval error: {e}"
                )
    
    async def _test_analysis_endpoint(self, client: httpx.AsyncClient):
        """Test the analysis endpoint"""
        print("🔬 Testing analysis endpoint...")
        
        test_cases = [
            {
                "name": "Factual Content",
                "user_input": "My name is Alex and I live in Berlin. I'm a software engineer.",
                "agent_response": "Nice to meet you, Alex! Berlin is a great city for tech.",
                "should_store": True
            },
            {
                "name": "Weather Ephemeral",
                "user_input": "It's raining today and I'm feeling tired.",
                "agent_response": "Sorry about the weather! Hope you feel better.",
                "should_store": False
            },
            {
                "name": "Technical Discussion",
                "user_input": "I'm working on a neural network in PyTorch for image classification.",
                "agent_response": "That sounds interesting! PyTorch is great for computer vision.",
                "should_store": True
            }
        ]
        
        for test_case in test_cases:
            analysis_request = {
                "user_input": test_case["user_input"],
                "agent_response": test_case["agent_response"],
                "conversation_context": f"Analysis test: {test_case['name']}",
                "curation_preferences": {
                    "priority_topics": ["technical_details", "personal_info", "programming"],
                    "retention_bias": "balanced",
                    "agent_personality": "technical_specialist"
                }
            }
            
            try:
                response = await client.post(
                    f"{self.engram_url}/cam/curated/analyze",
                    json=analysis_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    should_store = result.get("should_store", False)
                    storage_type = result.get("storage_type", "unknown")
                    confidence = result.get("confidence_score", 0)
                    
                    # Check if analysis matches expectation
                    analysis_correct = should_store == test_case["should_store"]
                    
                    self._record_result(
                        f"Analysis - {test_case['name']}",
                        analysis_correct,
                        f"{'✅' if analysis_correct else '❌'} Should store: {should_store} (expected: {test_case['should_store']}), Type: {storage_type}, Confidence: {confidence:.2f}"
                    )
                else:
                    self._record_result(
                        f"Analysis - {test_case['name']}",
                        False,
                        f"❌ Analysis failed: {response.status_code} - {response.text[:100]}..."
                    )
                    
            except Exception as e:
                self._record_result(
                    f"Analysis - {test_case['name']}",
                    False,
                    f"❌ Analysis error: {e}"
                )
    
    async def _test_memory_isolation(self, client: httpx.AsyncClient):
        """Test memory isolation between entities"""
        print("🔒 Testing memory isolation...")
        
        # Test cross-entity queries - each entity should NOT see others' memories
        isolation_tests = [
            (self.entities[0], self.entities[1]),  # Christian shouldn't see Daniel's info
            (self.entities[1], self.entities[2]),  # Daniel shouldn't see Sarah's info
            (self.entities[2], self.entities[0]),  # Sarah shouldn't see Christian's info
        ]
        
        for asking_entity, other_entity in isolation_tests:
            # Query for the other entity's name
            query = f"Do you know anything about {other_entity.name}?"
            embedding = [0.1] * 768
            
            isolation_request = {
                "requesting_entity": asking_entity.entity_id,
                "resonance_vectors": [
                    {"vector": embedding, "weight": 1.0}
                ],
                "query_text": query,
                "conversation_context": f"Isolation test: {asking_entity.name} asking about {other_entity.name}",
                "retrieval_options": {
                    "top_k": 10,  # Get more results to be thorough
                    "similarity_threshold": 0.0,
                    "exclude_denials": True
                }
            }
            
            try:
                response = await client.post(
                    f"{self.engram_url}/cam/curated/retrieve",
                    json=isolation_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get("memories", [])
                    
                    # Check if any memory contains information about the other entity
                    contaminated = False
                    contamination_details = []
                    
                    for memory in memories:
                        content = memory.get("content_preview", "") or memory.get("content", {}).get("text", "")
                        
                        # Check for other entity's name, location, or unique facts
                        if other_entity.name.lower() in content.lower():
                            contaminated = True
                            contamination_details.append(f"Name: {other_entity.name}")
                        
                        if any(part.lower() in content.lower() for part in other_entity.location.split(", ")):
                            contaminated = True
                            contamination_details.append(f"Location: {other_entity.location}")
                        
                        if any(word in content.lower() for word in other_entity.unique_fact.split() if len(word) > 4):
                            contaminated = True
                            contamination_details.append(f"Unique fact reference")
                    
                    self._record_result(
                        f"Isolation - {asking_entity.name} queries {other_entity.name}",
                        not contaminated,
                        f"{'❌ CONTAMINATED' if contaminated else '✅ ISOLATED'} - Found {len(memories)} memories" + 
                        (f" [Contamination: {', '.join(contamination_details)}]" if contaminated else "")
                    )
                else:
                    self._record_result(
                        f"Isolation - {asking_entity.name} queries {other_entity.name}",
                        False,
                        f"❌ Isolation test failed: {response.status_code}"
                    )
                    
            except Exception as e:
                self._record_result(
                    f"Isolation - {asking_entity.name} queries {other_entity.name}",
                    False,
                    f"❌ Isolation test error: {e}"
                )
    
    async def _verify_statistics(self, client: httpx.AsyncClient):
        """Verify memory statistics"""
        print("📊 Verifying statistics...")
        
        for entity in self.entities:
            try:
                response = await client.get(
                    f"{self.engram_url}/cam/curated/stats/{entity.entity_id}"
                )
                
                if response.status_code == 200:
                    stats = response.json()
                    total_memories = stats.get('total_memories', 0)
                    avg_confidence = stats.get('average_confidence_score', 0)
                    
                    self._record_result(
                        f"Statistics - {entity.name}",
                        total_memories > 0,
                        f"Total: {total_memories}, Avg confidence: {avg_confidence:.2f}"
                    )
                else:
                    self._record_result(
                        f"Statistics - {entity.name}",
                        False,
                        f"❌ Stats failed: {response.status_code}"
                    )
                    
            except Exception as e:
                self._record_result(
                    f"Statistics - {entity.name}",
                    False,
                    f"❌ Stats error: {e}"
                )
    
    def _record_result(self, test_name: str, success: bool, details: str):
        """Record a test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if not success or "CONTAMINATED" in details:
            print(f"    ⚠️  {details}")
    
    def _print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("🎯 DIRECT ENGRAM API TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}")
                    print(f"     {result['details']}")
        
        # Categorize issues
        contamination_issues = [r for r in self.test_results if not r["success"] and "contaminated" in r["details"].lower()]
        storage_issues = [r for r in self.test_results if not r["success"] and "storage" in r["test"].lower()]
        retrieval_issues = [r for r in self.test_results if not r["success"] and "retrieval" in r["test"].lower()]
        
        if contamination_issues:
            print(f"\n🚨 CRITICAL: {len(contamination_issues)} Memory Contamination Issues!")
            
        if storage_issues:
            print(f"\n⚠️  WARNING: {len(storage_issues)} Storage Issues!")
            
        if retrieval_issues:
            print(f"\n⚠️  WARNING: {len(retrieval_issues)} Retrieval Issues!")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED! Memory isolation is working perfectly! 🎉")
        
        print("\n" + "=" * 80)

async def main():
    """Run the direct Engram API test"""
    tester = DirectEngramIsolationTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())