#!/usr/bin/env python3
"""
Comprehensive test suite for AI-powered memory curation system
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"  # Still used for embeddings

class MemoryCurationTester:
    
    def __init__(self):
        self.test_results = []
        self.entity_id = "human-christian-test-curation"
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": "nomic-embed-text:latest", "prompt": text},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                return None
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            return None

    def test_memory_analysis(self):
        """Test memory curation analysis"""
        print("\n🧠 Testing Memory Curation Analysis")
        print("=" * 50)
        
        test_cases = [
            {
                "name": "Factual Information Storage",
                "user_input": "My name is Christian and I live in Liversedge, West Yorkshire",
                "agent_response": "Nice to meet you, Christian! I'll remember that you live in Liversedge.",
                "expected_storage": True,
                "expected_type": "facts"
            },
            {
                "name": "Preference Information",
                "user_input": "I prefer detailed technical explanations",
                "agent_response": "I'll make sure to provide detailed technical explanations for you.",
                "expected_storage": True,
                "expected_type": "preferences"
            },
            {
                "name": "Temporary Context",
                "user_input": "It's raining today",
                "agent_response": "That's unfortunate about the weather today.",
                "expected_storage": False,
                "expected_type": "temporary"
            },
            {
                "name": "Project Context",
                "user_input": "I'm working on an AI agent system called Engram",
                "agent_response": "That sounds like an interesting project! Tell me more about Engram.",
                "expected_storage": True,
                "expected_type": "context"
            },
            {
                "name": "Skill Information",
                "user_input": "I'm a Python developer with 10 years of experience",
                "agent_response": "That's impressive experience! I'll keep that in mind for our technical discussions.",
                "expected_storage": True,
                "expected_type": "skills"
            }
        ]
        
        for case in test_cases:
            try:
                # Create curation request
                request_data = {
                    "user_input": case["user_input"],
                    "agent_response": case["agent_response"],
                    "conversation_context": "Testing memory curation system",
                    "existing_memory_count": 5,
                    "curation_preferences": {
                        "priority_topics": ["technical_details", "personal_info"],
                        "retention_bias": "balanced",
                        "privacy_sensitivity": "personal",
                        "agent_personality": "technical_assistant"
                    }
                }
                
                # Test memory analysis
                response = requests.post(
                    f"{BASE_URL}/cam/curated/analyze",
                    json=request_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    decision = response.json()
                    
                    # Check if storage decision matches expectation
                    storage_correct = decision["should_store"] == case["expected_storage"]
                    
                    # Check storage type if it should be stored
                    type_correct = True
                    if case["expected_storage"] and decision["should_store"]:
                        type_correct = decision["storage_type"] == case["expected_type"]
                    
                    overall_correct = storage_correct and type_correct
                    
                    details = f"Storage: {decision['should_store']} (expected: {case['expected_storage']})"
                    if decision["should_store"]:
                        details += f", Type: {decision['storage_type']} (expected: {case['expected_type']})"
                        details += f", Confidence: {decision['confidence_score']:.2f}"
                    
                    self.log_test(case["name"], overall_correct, details)
                    
                else:
                    self.log_test(case["name"], False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(case["name"], False, f"Exception: {str(e)}")
            
            time.sleep(1)  # Rate limiting
    
    def test_curated_storage(self):
        """Test curated memory storage"""
        print("\n💾 Testing Curated Memory Storage")
        print("=" * 50)
        
        # Test storing a factual memory
        embedding = self.get_embedding("Christian lives in Liversedge")
        if not embedding:
            self.log_test("Get Embedding for Storage", False, "Failed to get embedding")
            return
        
        storage_request = {
            "witnessed_by": [self.entity_id],
            "situation_id": f"curation-test-{int(time.time())}",
            "situation_type": "conversation",
            "content": {
                "text": "Christian lives in Liversedge, West Yorkshire and works on AI systems",
                "content_type": "conversation_turn"
            },
            "primary_vector": embedding,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "interaction_quality": 0.9
            },
            "user_input": "I live in Liversedge and work on AI systems",
            "agent_response": "That's great! I'll remember that you live in Liversedge and work on AI.",
            "conversation_context": "Initial introduction conversation",
            "curation_preferences": {
                "priority_topics": ["location", "profession"],
                "retention_bias": "balanced",
                "privacy_sensitivity": "personal",
                "agent_personality": "helpful_assistant"
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/cam/curated/store",
                json=storage_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "stored":
                    curation_info = result.get("curation_decision", {})
                    details = f"Stored as {curation_info.get('storage_type', 'unknown')} "
                    details += f"with confidence {curation_info.get('confidence_score', 0):.2f}"
                    self.log_test("Curated Storage", True, details)
                    
                    # Save memory ID for retrieval test
                    self.test_memory_id = result.get("memory_id")
                    
                elif result.get("status") == "rejected_by_curation":
                    details = f"Rejected: {result.get('reasoning', 'No reason given')}"
                    self.log_test("Curated Storage", False, details)
                else:
                    self.log_test("Curated Storage", False, f"Unexpected status: {result.get('status')}")
            else:
                self.log_test("Curated Storage", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Curated Storage", False, f"Exception: {str(e)}")
    
    def test_intelligent_retrieval(self):
        """Test context-aware intelligent retrieval"""
        print("\n🔍 Testing Intelligent Retrieval")
        print("=" * 50)
        
        test_queries = [
            {
                "name": "Location Query",
                "query_text": "Where do I live?",
                "expected_intent": "facts"
            },
            {
                "name": "Preference Query", 
                "query_text": "What are my preferences for explanations?",
                "expected_intent": "preferences"
            },
            {
                "name": "Project Context Query",
                "query_text": "What was I working on?",
                "expected_intent": "context"
            }
        ]
        
        for query in test_queries:
            try:
                # Get embedding for query
                embedding = self.get_embedding(query["query_text"])
                if not embedding:
                    self.log_test(f"Embedding for {query['name']}", False, "Failed to get embedding")
                    continue
                
                # Test intelligent retrieval
                retrieval_request = {
                    "requesting_entity": self.entity_id,
                    "resonance_vectors": [{"vector": embedding, "weight": 1.0}],
                    "query_text": query["query_text"],
                    "conversation_context": "Testing intelligent retrieval",
                    "retrieval_options": {
                        "top_k": 5,
                        "similarity_threshold": 0.0,
                        "exclude_denials": True
                    }
                }
                
                response = requests.post(
                    f"{BASE_URL}/cam/curated/retrieve",
                    json=retrieval_request,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get("memories", [])
                    analysis = result.get("retrieval_analysis", {})
                    
                    details = f"Found {len(memories)} memories"
                    if analysis:
                        details += f", Intent: {analysis.get('intent_type', 'unknown')}"
                        details += f", Threshold: {analysis.get('confidence_threshold_used', 0):.2f}"
                    
                    # Consider it successful if we got some memories or analysis
                    success = len(memories) > 0 or bool(analysis)
                    self.log_test(query["name"], success, details)
                    
                else:
                    self.log_test(query["name"], False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(query["name"], False, f"Exception: {str(e)}")
            
            time.sleep(1)
    
    def test_cleanup_analysis(self):
        """Test memory cleanup analysis"""
        print("\n🧹 Testing Memory Cleanup Analysis")
        print("=" * 50)
        
        try:
            response = requests.post(
                f"{BASE_URL}/cam/curated/cleanup/analyze",
                params={"entity_id": self.entity_id, "limit": 50},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                actions = result.get("cleanup_actions", [])
                summary = result.get("summary", {})
                
                details = f"Analyzed {result.get('memories_analyzed', 0)} memories, "
                details += f"Found {summary.get('total_actions', 0)} cleanup actions"
                
                self.log_test("Cleanup Analysis", True, details)
                
            else:
                self.log_test("Cleanup Analysis", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Cleanup Analysis", False, f"Exception: {str(e)}")
    
    def test_curation_stats(self):
        """Test curation statistics"""
        print("\n📊 Testing Curation Statistics")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{BASE_URL}/cam/curated/stats/{self.entity_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                stats = response.json()
                
                details = f"Total memories: {stats.get('total_memories', 0)}, "
                details += f"Avg confidence: {stats.get('average_confidence_score', 0):.2f}, "
                details += f"Avg access: {stats.get('average_access_count', 0):.1f}"
                
                self.log_test("Curation Statistics", True, details)
                
            else:
                self.log_test("Curation Statistics", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Curation Statistics", False, f"Exception: {str(e)}")
    
    def test_agent_preferences(self):
        """Test different agent preference configurations"""
        print("\n🎛️ Testing Agent Preferences")
        print("=" * 50)
        
        preference_configs = [
            {
                "name": "Conservative Technical Agent",
                "preferences": {
                    "priority_topics": ["technical_details", "code", "programming"],
                    "retention_bias": "conservative",
                    "privacy_sensitivity": "private",
                    "agent_personality": "technical_specialist"
                }
            },
            {
                "name": "Aggressive Personal Assistant",
                "preferences": {
                    "priority_topics": ["personal_info", "preferences", "daily_tasks"],
                    "retention_bias": "aggressive", 
                    "privacy_sensitivity": "personal",
                    "agent_personality": "personal_assistant"
                }
            }
        ]
        
        test_input = "I'm thinking about learning a new programming language, maybe Rust"
        test_response = "That's a great choice! Rust is excellent for systems programming."
        
        for config in preference_configs:
            try:
                request_data = {
                    "user_input": test_input,
                    "agent_response": test_response,
                    "conversation_context": "Learning discussion",
                    "curation_preferences": config["preferences"]
                }
                
                response = requests.post(
                    f"{BASE_URL}/cam/curated/analyze",
                    json=request_data,
                    timeout=20
                )
                
                if response.status_code == 200:
                    decision = response.json()
                    
                    details = f"Storage: {decision['should_store']}, "
                    details += f"Type: {decision.get('storage_type', 'N/A')}, "
                    details += f"Confidence: {decision.get('confidence_score', 0):.2f}"
                    
                    self.log_test(config["name"], True, details)
                    
                else:
                    self.log_test(config["name"], False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(config["name"], False, f"Exception: {str(e)}")
            
            time.sleep(1)
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 ENGRAM MEMORY CURATION TEST SUITE")
        print("=" * 60)
        
        # Run all test categories
        self.test_memory_analysis()
        self.test_curated_storage()
        self.test_intelligent_retrieval()
        self.test_cleanup_analysis()
        self.test_curation_stats()
        self.test_agent_preferences()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for test in self.test_results if test["passed"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test["passed"]]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Overall assessment
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED! Memory curation system is working perfectly!")
        elif passed >= total * 0.8:
            print(f"\n✅ Most tests passed ({passed}/{total}). System is mostly functional.")
        else:
            print(f"\n⚠️  Many tests failed ({total-passed}/{total}). System needs attention.")
        
        return passed, total


if __name__ == "__main__":
    tester = MemoryCurationTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if passed == total else 1)