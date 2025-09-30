#!/usr/bin/env python3
"""
Comprehensive production test suite for Engram after security cleanup
Tests all major functionality to give agent team confidence
"""

import requests
import json
import time
from datetime import datetime
import random

BASE_URL = "http://46.62.130.230:8000"
ADMIN_USER = "admin"
ADMIN_PASS = "engram-admin-2025"

class ProductionTestSuite:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, passed, details=""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        
        self.test_results.append(result)
        print(result)
        
    def test_system_health(self):
        """Test basic system health and connectivity"""
        print("\n🏥 SYSTEM HEALTH TESTS")
        print("=" * 50)
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("System Health Check", True, f"Status: {health_data['status']}")
                self.log_test("Redis Connection", health_data.get('redis') == 'connected', f"Redis: {health_data.get('redis')}")
                self.log_test("Vector Index Status", health_data.get('vector_index', False), f"Index: {health_data.get('vector_index')}")
            else:
                self.log_test("System Health Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("System Health Check", False, str(e))
            
    def test_admin_endpoints(self):
        """Test admin functionality"""
        print("\n👑 ADMIN ENDPOINTS TESTS")
        print("=" * 50)
        
        # Test admin status
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/admin/status",
                auth=(ADMIN_USER, ADMIN_PASS),
                timeout=10
            )
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("Admin Status Endpoint", True, f"Status: {status_data['status']}")
                self.log_test("Memory Counts Available", 'memory_counts' in status_data, f"Counts: {status_data.get('memory_counts', {})}")
            else:
                self.log_test("Admin Status Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Admin Status Endpoint", False, str(e))
            
    def test_multi_entity_storage(self):
        """Test multi-entity memory storage"""
        print("\n💾 MULTI-ENTITY STORAGE TESTS")
        print("=" * 50)
        
        test_memories = [
            {
                "witnessed_by": ["human-christian-test", "agent-claude-test"],
                "situation_type": "production_test",
                "content": {
                    "text": "This is a production test memory for the agent team",
                    "speakers": {
                        "human-christian-test": "Testing storage functionality",
                        "agent-claude-test": "Confirming memory persistence"
                    },
                    "summary": "Production test validation"
                },
                "primary_vector": [round(random.uniform(-1, 1), 3) for _ in range(768)],
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "interaction_quality": 1.0,
                    "topic_tags": ["production", "test", "validation"]
                }
            },
            {
                "witnessed_by": ["user-alice", "user-bob", "agent-system"],
                "situation_type": "team_meeting",
                "content": {
                    "text": "Team discussed quarterly objectives and project milestones",
                    "speakers": {
                        "user-alice": "We need to focus on user experience improvements",
                        "user-bob": "The backend performance metrics look good",
                        "agent-system": "I can help track the action items"
                    },
                    "summary": "Q4 planning meeting with action items"
                },
                "primary_vector": [round(random.uniform(-1, 1), 3) for _ in range(768)],
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "interaction_quality": 0.9,
                    "topic_tags": ["meeting", "planning", "team"]
                }
            }
        ]
        
        stored_memory_ids = []
        
        for i, memory in enumerate(test_memories):
            try:
                response = requests.post(
                    f"{BASE_URL}/cam/multi/store",
                    json=memory,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memory_id = result.get('memory_id')
                    stored_memory_ids.append(memory_id)
                    self.log_test(f"Store Memory {i+1}", True, f"ID: {memory_id}")
                else:
                    self.log_test(f"Store Memory {i+1}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Store Memory {i+1}", False, str(e))
                
        return stored_memory_ids
        
    def test_multi_entity_retrieval(self, stored_memory_ids):
        """Test multi-entity memory retrieval"""
        print("\n🔍 MULTI-ENTITY RETRIEVAL TESTS")
        print("=" * 50)
        
        # Test retrieval for different entities
        test_entities = [
            "human-christian-test",
            "agent-claude-test", 
            "user-alice",
            "user-bob",
            "agent-system"
        ]
        
        for entity in test_entities:
            try:
                retrieval_request = {
                    "requesting_entity": entity,
                    "resonance_vectors": [{
                        "vector": [round(random.uniform(-1, 1), 3) for _ in range(768)],
                        "weight": 1.0
                    }],
                    "retrieval_options": {
                        "top_k": 10,
                        "similarity_threshold": 0.0  # Get all accessible memories
                    }
                }
                
                response = requests.post(
                    f"{BASE_URL}/cam/multi/retrieve",
                    json=retrieval_request,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memory_count = len(result.get('memories', []))
                    self.log_test(f"Retrieve for {entity}", True, f"Found {memory_count} memories")
                    
                    # Verify memory structure
                    if memory_count > 0:
                        first_memory = result['memories'][0]
                        required_fields = ['memory_id', 'situation_summary', 'co_participants', 'content_preview']
                        has_all_fields = all(field in first_memory for field in required_fields)
                        self.log_test(f"Memory Structure for {entity}", has_all_fields, f"Fields: {list(first_memory.keys())}")
                else:
                    self.log_test(f"Retrieve for {entity}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Retrieve for {entity}", False, str(e))
                
    def test_access_control(self):
        """Test witness-based access control"""
        print("\n🔐 ACCESS CONTROL TESTS")
        print("=" * 50)
        
        # Store a private memory
        private_memory = {
            "witnessed_by": ["secret-user-1", "secret-user-2"],
            "situation_type": "private_conversation",
            "content": {
                "text": "This is a private conversation that should not be accessible to others",
                "speakers": {
                    "secret-user-1": "This information is confidential",
                    "secret-user-2": "Agreed, this stays between us"
                },
                "summary": "Confidential discussion"
            },
            "primary_vector": [round(random.uniform(-1, 1), 3) for _ in range(768)],
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "interaction_quality": 1.0,
                "topic_tags": ["private", "confidential"]
            }
        }
        
        # Store the private memory
        try:
            response = requests.post(f"{BASE_URL}/cam/multi/store", json=private_memory, timeout=15)
            if response.status_code == 200:
                private_memory_id = response.json()['memory_id']
                self.log_test("Store Private Memory", True, f"ID: {private_memory_id}")
                
                # Test that witnesses can access it
                for witness in ["secret-user-1", "secret-user-2"]:
                    retrieval_request = {
                        "requesting_entity": witness,
                        "resonance_vectors": [{"vector": [0.5] * 1536, "weight": 1.0}],
                        "retrieval_options": {"top_k": 10, "similarity_threshold": 0.0}
                    }
                    
                    response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=retrieval_request, timeout=10)
                    if response.status_code == 200:
                        memories = response.json().get('memories', [])
                        found_private = any(m['memory_id'] == private_memory_id for m in memories)
                        self.log_test(f"Witness {witness} Access", found_private, f"Can access private memory: {found_private}")
                    else:
                        self.log_test(f"Witness {witness} Access", False, f"HTTP {response.status_code}")
                
                # Test that non-witnesses CANNOT access it
                for non_witness in ["human-christian-test", "agent-claude-test", "random-user"]:
                    retrieval_request = {
                        "requesting_entity": non_witness,
                        "resonance_vectors": [{"vector": [0.5] * 1536, "weight": 1.0}],
                        "retrieval_options": {"top_k": 10, "similarity_threshold": 0.0}
                    }
                    
                    response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=retrieval_request, timeout=10)
                    if response.status_code == 200:
                        memories = response.json().get('memories', [])
                        found_private = any(m['memory_id'] == private_memory_id for m in memories)
                        self.log_test(f"Non-witness {non_witness} Blocked", not found_private, f"Cannot access private memory: {not found_private}")
                    else:
                        self.log_test(f"Non-witness {non_witness} Blocked", False, f"HTTP {response.status_code}")
                        
            else:
                self.log_test("Store Private Memory", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Access Control Test", False, str(e))
            
    def test_vector_search_quality(self):
        """Test vector similarity search quality"""
        print("\n🎯 VECTOR SEARCH QUALITY TESTS")
        print("=" * 50)
        
        # Store memories with known similar content
        similar_memories = [
            {
                "witnessed_by": ["test-user"],
                "situation_type": "technical_discussion",
                "content": {
                    "text": "We discussed machine learning algorithms and neural networks",
                    "speakers": {"test-user": "Neural networks are fascinating"},
                    "summary": "AI and ML discussion"
                },
                "primary_vector": [1.0, 0.8, 0.6, 0.4, 0.2] + [0.0] * 763,  # Similar pattern
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "interaction_quality": 1.0,
                    "topic_tags": ["ai", "ml", "neural-networks"]
                }
            },
            {
                "witnessed_by": ["test-user"],
                "situation_type": "technical_discussion", 
                "content": {
                    "text": "Artificial intelligence and deep learning models are advancing rapidly",
                    "speakers": {"test-user": "Deep learning is the future"},
                    "summary": "AI advancement discussion"
                },
                "primary_vector": [0.9, 0.7, 0.5, 0.3, 0.1] + [0.0] * 763,  # Very similar pattern
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "interaction_quality": 1.0,
                    "topic_tags": ["ai", "deep-learning", "advancement"]
                }
            },
            {
                "witnessed_by": ["test-user"],
                "situation_type": "casual_chat",
                "content": {
                    "text": "The weather is really nice today, perfect for a walk in the park",
                    "speakers": {"test-user": "Beautiful sunny day"},
                    "summary": "Weather conversation"
                },
                "primary_vector": [0.1, 0.2, 0.3, 0.4, 0.5] + [1.0] * 763,  # Very different pattern
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "interaction_quality": 1.0,
                    "topic_tags": ["weather", "casual", "outdoors"]
                }
            }
        ]
        
        # Store the memories
        stored_ids = []
        for i, memory in enumerate(similar_memories):
            try:
                response = requests.post(f"{BASE_URL}/cam/multi/store", json=memory, timeout=15)
                if response.status_code == 200:
                    stored_ids.append(response.json()['memory_id'])
                    self.log_test(f"Store Search Test Memory {i+1}", True)
                else:
                    self.log_test(f"Store Search Test Memory {i+1}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Store Search Test Memory {i+1}", False, str(e))
        
        # Test vector similarity search
        if len(stored_ids) >= 3:
            # Search with AI-related vector (should find first two memories)
            ai_search_vector = [0.95, 0.75, 0.55, 0.35, 0.15] + [0.0] * 763
            
            retrieval_request = {
                "requesting_entity": "test-user",
                "resonance_vectors": [{"vector": ai_search_vector, "weight": 1.0}],
                "retrieval_options": {"top_k": 5, "similarity_threshold": 0.0}
            }
            
            try:
                response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=retrieval_request, timeout=15)
                if response.status_code == 200:
                    results = response.json().get('memories', [])
                    self.log_test("Vector Search Results", len(results) >= 2, f"Found {len(results)} memories")
                    
                    # Check if AI-related memories are ranked higher than weather memory
                    if len(results) >= 2:
                        top_memories = results[:2]
                        ai_topics_found = sum(1 for m in top_memories if any(tag in ['ai', 'ml', 'neural-networks', 'deep-learning'] for tag in m.get('topic_tags', [])))
                        self.log_test("Semantic Relevance Ranking", ai_topics_found >= 1, f"AI topics in top results: {ai_topics_found}")
                else:
                    self.log_test("Vector Search Results", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Vector Search Results", False, str(e))
                
    def test_performance(self):
        """Test system performance"""
        print("\n⚡ PERFORMANCE TESTS")
        print("=" * 50)
        
        # Test storage performance
        start_time = time.time()
        quick_memory = {
            "witnessed_by": ["perf-test-user"],
            "situation_type": "performance_test",
            "content": {
                "text": "Performance test memory",
                "speakers": {"perf-test-user": "Testing speed"},
                "summary": "Speed test"
            },
            "primary_vector": [0.5] * 1536,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "interaction_quality": 1.0,
                "topic_tags": ["performance"]
            }
        }
        
        try:
            response = requests.post(f"{BASE_URL}/cam/multi/store", json=quick_memory, timeout=10)
            storage_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_test("Storage Performance", storage_time < 5.0, f"Storage took {storage_time:.2f}s")
            else:
                self.log_test("Storage Performance", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Storage Performance", False, str(e))
            
        # Test retrieval performance
        start_time = time.time()
        retrieval_request = {
            "requesting_entity": "perf-test-user",
            "resonance_vectors": [{"vector": [0.5] * 1536, "weight": 1.0}],
            "retrieval_options": {"top_k": 10, "similarity_threshold": 0.0}
        }
        
        try:
            response = requests.post(f"{BASE_URL}/cam/multi/retrieve", json=retrieval_request, timeout=10)
            retrieval_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_test("Retrieval Performance", retrieval_time < 3.0, f"Retrieval took {retrieval_time:.2f}s")
            else:
                self.log_test("Retrieval Performance", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Retrieval Performance", False, str(e))
            
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 ENGRAM PRODUCTION COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"Testing server: {BASE_URL}")
        print(f"Test started: {datetime.utcnow().isoformat()}Z")
        print("=" * 60)
        
        # Run all test categories
        self.test_system_health()
        self.test_admin_endpoints()
        stored_memory_ids = self.test_multi_entity_storage()
        self.test_multi_entity_retrieval(stored_memory_ids)
        self.test_access_control()
        self.test_vector_search_quality()
        self.test_performance()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        for result in self.test_results:
            print(result)
            
        print("\n" + "=" * 60)
        print(f"🎯 OVERALL RESULTS: {self.passed_tests}/{self.total_tests} tests passed")
        
        if self.passed_tests == self.total_tests:
            print("🎉 ALL TESTS PASSED! System is ready for agent team use.")
        elif self.passed_tests >= self.total_tests * 0.9:
            print("✅ MOSTLY FUNCTIONAL! Minor issues detected but system is usable.")
        elif self.passed_tests >= self.total_tests * 0.7:
            print("⚠️  SOME ISSUES! System has functionality but needs attention.")
        else:
            print("❌ CRITICAL ISSUES! System needs significant fixes before use.")
            
        print("=" * 60)
        
        return self.passed_tests, self.total_tests

if __name__ == "__main__":
    test_suite = ProductionTestSuite()
    passed, total = test_suite.run_comprehensive_test()