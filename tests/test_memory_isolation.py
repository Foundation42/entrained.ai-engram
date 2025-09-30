#!/usr/bin/env python3
"""
Comprehensive Memory Isolation Test

This test systematically verifies that the Columbo memory system properly isolates
memories between different entities and doesn't suffer from cross-contamination.

Test Coverage:
1. Multiple entities with distinct information
2. Storage verification per entity
3. Retrieval verification per entity  
4. Cross-contamination detection
5. Session isolation
6. Different information types (facts, skills, preferences)
7. Edge cases and boundary conditions
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

class MemoryIsolationTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
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
        """Run the complete memory isolation test suite"""
        print("🧪 COMPREHENSIVE MEMORY ISOLATION TEST")
        print("=" * 80)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            
            # Phase 1: Clean slate verification
            print("\n📋 PHASE 1: Clean Slate Verification")
            print("-" * 50)
            await self._verify_clean_slate(client)
            
            # Phase 2: Information storage for each entity
            print("\n📋 PHASE 2: Multi-Entity Information Storage")
            print("-" * 50)
            await self._store_entity_information(client)
            
            # Phase 3: Individual entity recall verification
            print("\n📋 PHASE 3: Individual Entity Recall Verification")
            print("-" * 50)
            await self._verify_individual_recall(client)
            
            # Phase 4: Cross-contamination testing
            print("\n📋 PHASE 4: Cross-Contamination Detection")
            print("-" * 50)
            await self._test_cross_contamination(client)
            
            # Phase 5: Session isolation testing
            print("\n📋 PHASE 5: Session Isolation Testing")
            print("-" * 50)
            await self._test_session_isolation(client)
            
            # Phase 6: Edge case testing
            print("\n📋 PHASE 6: Edge Case Testing")
            print("-" * 50)
            await self._test_edge_cases(client)
            
            # Phase 7: Memory statistics verification
            print("\n📋 PHASE 7: Memory Statistics Verification")
            print("-" * 50)
            await self._verify_memory_statistics(client)
            
        # Final results
        self._print_final_results()
    
    async def _verify_clean_slate(self, client: httpx.AsyncClient):
        """Verify entities start with clean memory"""
        for entity in self.entities:
            print(f"🧹 Testing clean slate for {entity.name} ({entity.entity_id})")
            
            response = await self._ask_question(
                client,
                entity.entity_id, 
                f"What is my name?",
                f"clean-slate-{entity.name.lower()}"
            )
            
            # Should not know the name yet
            if entity.name.lower() in response.lower():
                self._record_result(
                    f"Clean Slate - {entity.name}",
                    False, 
                    f"Agent already knows {entity.name}'s name: {response[:100]}..."
                )
            else:
                self._record_result(
                    f"Clean Slate - {entity.name}",
                    True,
                    f"✅ Clean slate confirmed for {entity.name}"
                )
    
    async def _store_entity_information(self, client: httpx.AsyncClient):
        """Store comprehensive information for each entity"""
        for entity in self.entities:
            print(f"💾 Storing information for {entity.name}")
            
            # Introduction message with all key facts
            intro_message = (
                f"Hi! My name is {entity.name} and I live in {entity.location}. "
                f"I work with {', '.join(entity.skills)} and I love {', '.join(entity.preferences)}. "
                f"Here's a unique fact about me: {entity.unique_fact}."
            )
            
            response = await self._send_message(
                client,
                entity.entity_id,
                intro_message,
                f"intro-{entity.name.lower()}"
            )
            
            print(f"  📝 {entity.name}: {response[:100]}...")
            
            # Store additional context in separate messages
            await self._send_message(
                client,
                entity.entity_id, 
                f"I specialize in {entity.skills[0]} development.",
                f"specialty-{entity.name.lower()}"
            )
            
            await self._send_message(
                client,
                entity.entity_id,
                f"My favorite thing about {entity.location} is the community.",
                f"location-love-{entity.name.lower()}"
            )
    
    async def _verify_individual_recall(self, client: httpx.AsyncClient):
        """Test that each entity's information can be recalled correctly"""
        recall_tests = [
            ("name", "What is my name?"),
            ("location", "Where do I live?"), 
            ("skills", "What programming languages do I use?"),
            ("unique_fact", "What unique fact did I tell you about myself?")
        ]
        
        for entity in self.entities:
            print(f"🧠 Testing recall for {entity.name}")
            
            for test_type, question in recall_tests:
                response = await self._ask_question(
                    client,
                    entity.entity_id,
                    question,
                    f"recall-{test_type}-{entity.name.lower()}"
                )
                
                # Verify correct information is returned
                success = self._verify_recall_accuracy(entity, test_type, response)
                self._record_result(
                    f"Recall {test_type.title()} - {entity.name}",
                    success,
                    response[:150] + "..." if len(response) > 150 else response
                )
    
    async def _test_cross_contamination(self, client: httpx.AsyncClient):
        """Test for memory contamination between entities"""
        print("🔍 Testing for cross-contamination...")
        
        contamination_tests = [
            # Test if Christian gets Daniel's info
            (self.entities[0], self.entities[1], "Do you know anything about Daniel?"),
            (self.entities[0], self.entities[2], "Do you know anything about Sarah?"),
            
            # Test if Daniel gets Christian's info
            (self.entities[1], self.entities[0], "Do you know anything about Christian?"),
            (self.entities[1], self.entities[2], "Do you know anything about Sarah?"),
            
            # Test if Sarah gets others' info
            (self.entities[2], self.entities[0], "Do you know anything about Christian?"),
            (self.entities[2], self.entities[1], "Do you know anything about Daniel?"),
        ]
        
        for asking_entity, other_entity, question in contamination_tests:
            response = await self._ask_question(
                client,
                asking_entity.entity_id,
                question,
                f"contamination-{asking_entity.name}-asks-about-{other_entity.name}"
            )
            
            # Should NOT contain information about the other entity
            contaminated = self._check_for_contamination(other_entity, response)
            
            self._record_result(
                f"Contamination Check - {asking_entity.name} asks about {other_entity.name}",
                not contaminated,
                f"Response: {response[:100]}..." + (f" [CONTAMINATED WITH {other_entity.name}'S INFO]" if contaminated else " [CLEAN]")
            )
    
    async def _test_session_isolation(self, client: httpx.AsyncClient):
        """Test that different sessions maintain proper isolation"""
        print("🔐 Testing session isolation...")
        
        for entity in self.entities:
            # Ask the same question in a new session
            new_session_response = await self._ask_question(
                client,
                entity.entity_id,
                "What is my name?",
                f"new-session-{entity.name.lower()}"
            )
            
            # Should still remember the name (cross-session persistence)
            name_remembered = entity.name.lower() in new_session_response.lower()
            
            self._record_result(
                f"Cross-Session Memory - {entity.name}",
                name_remembered,
                f"New session response: {new_session_response[:100]}..."
            )
    
    async def _test_edge_cases(self, client: httpx.AsyncClient):
        """Test edge cases and boundary conditions"""
        print("⚠️ Testing edge cases...")
        
        # Test with very similar names
        similar_entity = TestEntity(
            name="Christina", # Similar to Christian
            entity_id="human-christina-calm-deer",
            location="Leeds, West Yorkshire", 
            skills=["Java", "Spring Boot"],
            preferences=["backend development"],
            unique_fact="has 10 years of enterprise experience"
        )
        
        # Store Christina's info
        await self._send_message(
            client,
            similar_entity.entity_id,
            f"Hi! My name is {similar_entity.name} and I live in {similar_entity.location}. I work with {similar_entity.skills[0]}.",
            f"similar-name-intro"
        )
        
        # Test if Christian gets Christina's info or vice versa
        christian_response = await self._ask_question(
            client,
            self.entities[0].entity_id,  # Christian
            "What is my name?",
            "similar-name-test-christian"
        )
        
        christina_response = await self._ask_question(
            client,
            similar_entity.entity_id,  # Christina
            "What is my name?", 
            "similar-name-test-christina"
        )
        
        # Verify no confusion
        christian_correct = "christian" in christian_response.lower() and "christina" not in christian_response.lower()
        christina_correct = "christina" in christina_response.lower() and "christian" not in christina_response.lower()
        
        self._record_result(
            "Similar Name Isolation - Christian",
            christian_correct,
            f"Christian asked for name, got: {christian_response[:100]}..."
        )
        
        self._record_result(
            "Similar Name Isolation - Christina", 
            christina_correct,
            f"Christina asked for name, got: {christina_response[:100]}..."
        )
    
    async def _verify_memory_statistics(self, client: httpx.AsyncClient):
        """Verify memory statistics are properly segregated"""
        print("📊 Verifying memory statistics...")
        
        for entity in self.entities:
            try:
                stats_response = await client.get(
                    f"http://46.62.130.230:8000/cam/curated/stats/{entity.entity_id}"
                )
                
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    total_memories = stats.get('total_memories', 0)
                    
                    self._record_result(
                        f"Memory Stats - {entity.name}",
                        total_memories > 0,
                        f"Total memories: {total_memories}, Avg confidence: {stats.get('average_confidence_score', 0):.2f}"
                    )
                else:
                    self._record_result(
                        f"Memory Stats - {entity.name}",
                        False,
                        f"Failed to get stats: {stats_response.status_code}"
                    )
            except Exception as e:
                self._record_result(
                    f"Memory Stats - {entity.name}",
                    False,
                    f"Error getting stats: {e}"
                )
    
    async def _send_message(self, client: httpx.AsyncClient, entity_id: str, message: str, session_suffix: str) -> str:
        """Send a message and return the response"""
        try:
            response = await client.post(
                f"{self.base_url}/agent/invoke",
                json={
                    "input": {"text": message},
                    "metadata": {
                        "session_id": f"isolation-test-{session_suffix}",
                        "sender_id": entity_id,
                        "timestamp": datetime.now().isoformat()
                    },
                    "options": {
                        "memory_context": True,
                        "streaming": False
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", {}).get("text", "No response")
            else:
                return f"ERROR: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"EXCEPTION: {str(e)}"
    
    async def _ask_question(self, client: httpx.AsyncClient, entity_id: str, question: str, session_suffix: str) -> str:
        """Ask a question and return the response""" 
        return await self._send_message(client, entity_id, question, session_suffix)
    
    def _verify_recall_accuracy(self, entity: TestEntity, test_type: str, response: str) -> bool:
        """Verify that the response contains correct information for the entity"""
        response_lower = response.lower()
        
        if test_type == "name":
            return entity.name.lower() in response_lower
        elif test_type == "location":
            return any(part.lower() in response_lower for part in entity.location.split(", "))
        elif test_type == "skills":
            return any(skill.lower() in response_lower for skill in entity.skills)
        elif test_type == "unique_fact":
            return any(word in response_lower for word in entity.unique_fact.split() if len(word) > 3)
        
        return False
    
    def _check_for_contamination(self, other_entity: TestEntity, response: str) -> bool:
        """Check if response contains information about another entity"""
        response_lower = response.lower()
        
        # Check for other entity's name, location, or unique facts
        if other_entity.name.lower() in response_lower:
            return True
        if any(part.lower() in response_lower for part in other_entity.location.split(", ")):
            return True
        if any(skill.lower() in response_lower for skill in other_entity.skills):
            return True
        if any(word in response_lower for word in other_entity.unique_fact.split() if len(word) > 4):
            return True
            
        return False
    
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
        print("🎯 COMPREHENSIVE TEST RESULTS")
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
        contamination_issues = [r for r in self.test_results if not r["success"] and "contamination" in r["test"].lower()]
        recall_issues = [r for r in self.test_results if not r["success"] and "recall" in r["test"].lower()]
        
        if contamination_issues:
            print(f"\n🚨 CRITICAL: {len(contamination_issues)} Cross-Contamination Issues Detected!")
            
        if recall_issues:
            print(f"\n⚠️  WARNING: {len(recall_issues)} Memory Recall Failures!")
        
        print("\n" + "=" * 80)

async def main():
    """Run the comprehensive memory isolation test"""
    tester = MemoryIsolationTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())