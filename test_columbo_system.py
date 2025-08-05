#!/usr/bin/env python3
"""
Test the new Columbo (Detective-style) AI Memory Curation System

This test verifies:
1. Curated storage with AI analysis 
2. Intelligent retrieval with intent analysis
3. Quality filtering (no weather/denials)
4. Technical assistant personality preferences
"""
import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

class ColumboSystemTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.user_id = "human-christian-kind-hare"
        self.agent_id = "agent-claude-prime"
        
    async def test_complete_flow(self):
        """Test the complete Columbo system flow"""
        print("🕵️ COLUMBO MEMORY SYSTEM TEST")
        print("=" * 60)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Test 1: Rich Introduction (Multiple facts)
            print("\n1. 🎯 Rich Introduction Test")
            print("-" * 40)
            
            rich_intro = (
                "Hi! My name is Christian and I live in Liversedge, West Yorkshire. "
                "I work on AI systems and love programming in Python. "
                "It's a bit rainy today, but I'm excited to test this new system!"
            )
            
            intro_response = await self._send_message(client, rich_intro, "rich-intro-test")
            print(f"👤 Christian: {rich_intro}")
            print(f"🤖 Agent: {intro_response}")
            
            # Wait for curation processing
            await asyncio.sleep(3)
            
            # Test 2: Name Recall
            print("\n2. 📝 Name Recall Test")
            print("-" * 40)
            
            name_query = "What is my name?"
            name_response = await self._send_message(client, name_query, "name-recall-test")
            print(f"👤 Christian: {name_query}")
            print(f"🤖 Agent: {name_response}")
            
            if "christian" in name_response.lower():
                print("✅ SUCCESS: Agent remembered Christian's name!")
            else:
                print("❌ FAILED: Agent did not remember the name")
            
            # Test 3: Location Recall
            print("\n3. 🏠 Location Recall Test")
            print("-" * 40)
            
            location_query = "Where do I live?"
            location_response = await self._send_message(client, location_query, "location-recall-test")
            print(f"👤 Christian: {location_query}")
            print(f"🤖 Agent: {location_response}")
            
            if "liversedge" in location_response.lower() and "west yorkshire" in location_response.lower():
                print("✅ SUCCESS: Agent remembered Christian's location!")
            elif "liversedge" in location_response.lower():
                print("🎯 PARTIAL: Agent remembered city but not full location")
            else:
                print("❌ FAILED: Agent did not remember the location")
            
            # Test 4: Technical Skills Recall
            print("\n4. 💻 Technical Skills Recall Test")
            print("-" * 40)
            
            skills_query = "What programming languages do I use?"
            skills_response = await self._send_message(client, skills_query, "skills-recall-test")
            print(f"👤 Christian: {skills_query}")
            print(f"🤖 Agent: {skills_response}")
            
            if "python" in skills_response.lower():
                print("✅ SUCCESS: Agent remembered Christian's Python skills!")
            else:
                print("❌ FAILED: Agent did not remember technical skills")
            
            # Test 5: Weather Filtering (Should NOT remember weather)
            print("\n5. 🌧️ Weather Filtering Test")
            print("-" * 40)
            
            weather_query = "What was the weather like when we first talked?"
            weather_response = await self._send_message(client, weather_query, "weather-filter-test")
            print(f"👤 Christian: {weather_query}")
            print(f"🤖 Agent: {weather_response}")
            
            if "rainy" in weather_response.lower() or "rain" in weather_response.lower():
                print("⚠️ WARNING: Agent remembered weather (should be filtered)")
            else:
                print("✅ SUCCESS: Weather information properly filtered!")
            
            # Test 6: Check Memory Quality via Direct API
            print("\n6. 📊 Memory Quality Analysis")
            print("-" * 40)
            
            await self._check_memory_stats(client)
            
    async def _send_message(self, client: httpx.AsyncClient, message: str, test_session: str) -> str:
        """Send a message to the agent and return the response"""
        try:
            response = await client.post(
                f"{self.base_url}/agent/invoke",
                json={
                    "input": {"text": message},
                    "metadata": {
                        "session_id": f"columbo-test-{test_session}",
                        "sender_id": self.user_id,
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
    
    async def _check_memory_stats(self, client: httpx.AsyncClient):
        """Check memory statistics via direct Engram API"""
        try:
            stats_response = await client.get(
                f"http://46.62.130.230:8000/cam/curated/stats/{self.user_id}"
            )
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print("📈 Memory Statistics:")
                print(f"   Total Memories: {stats.get('total_memories', 0)}")
                
                breakdown = stats.get('storage_type_breakdown', {})
                for storage_type, count in breakdown.items():
                    print(f"   {storage_type.title()}: {count}")
                
                avg_confidence = stats.get('average_confidence_score', 0)
                print(f"   Average Confidence: {avg_confidence:.2f}")
                
                if avg_confidence > 0.7:
                    print("✅ HIGH QUALITY: Memory confidence is excellent!")
                elif avg_confidence > 0.5:
                    print("🎯 GOOD QUALITY: Memory confidence is good")
                else:
                    print("⚠️ LOW QUALITY: Memory confidence needs improvement")
                    
            else:
                print(f"❌ Could not get memory stats: {stats_response.status_code}")
                
        except Exception as e:
            print(f"❌ Stats check failed: {e}")

    async def test_curation_analysis(self):
        """Test the curation analysis endpoint directly"""
        print("\n🔬 DIRECT CURATION ANALYSIS TEST")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            
            # Test mixed content (facts + ephemeral)
            test_cases = [
                {
                    "name": "Rich Factual Content",
                    "user_input": "I'm Christian, a software engineer from Liversedge who loves Python programming",
                    "agent_response": "Great to meet you Christian! I'll remember you're from Liversedge and work with Python."
                },
                {
                    "name": "Weather + Small Talk",
                    "user_input": "It's raining today and I'm feeling a bit tired",
                    "agent_response": "Sorry to hear about the weather and that you're tired. Hope your day gets better!"
                },
                {
                    "name": "Technical Discussion",
                    "user_input": "I'm working on implementing neural networks in PyTorch for my AI project",
                    "agent_response": "That sounds like an interesting AI project! PyTorch is excellent for neural networks."
                }
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n{i}. {test_case['name']}:")
                print("-" * 30)
                
                try:
                    analysis_response = await client.post(
                        "http://46.62.130.230:8000/cam/curated/analyze",
                        json={
                            "user_input": test_case["user_input"],
                            "agent_response": test_case["agent_response"],
                            "conversation_context": "Test analysis",
                            "curation_preferences": {
                                "priority_topics": ["technical_details", "personal_info"],
                                "retention_bias": "balanced",
                                "agent_personality": "technical_specialist"
                            }
                        }
                    )
                    
                    if analysis_response.status_code == 200:
                        analysis = analysis_response.json()
                        
                        print(f"Should Store: {analysis.get('should_store', False)}")
                        print(f"Storage Type: {analysis.get('storage_type', 'none')}")
                        print(f"Confidence: {analysis.get('confidence_score', 0):.2f}")
                        print(f"Reasoning: {analysis.get('reasoning', 'No reasoning')[:100]}...")
                        
                        observations = analysis.get('observations', [])
                        print(f"Observations: {len(observations)}")
                        for obs in observations[:3]:  # Show first 3
                            ephemeral = obs.get('ephemerality_score', 0)
                            content = obs.get('content', '')[:50] + "..."
                            print(f"  - {content} (ephemeral: {ephemeral:.2f})")
                            
                    else:
                        print(f"❌ Analysis failed: {analysis_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Analysis error: {e}")

async def main():
    """Run the complete Columbo system test suite"""
    print("🚀 Starting Columbo Memory System Tests...")
    
    tester = ColumboSystemTester()
    
    # Test 1: Complete agent flow
    await tester.test_complete_flow()
    
    # Test 2: Direct curation analysis
    await tester.test_curation_analysis()
    
    print("\n" + "="*60)
    print("🎉 COLUMBO SYSTEM TEST COMPLETE!")
    print("Check the results above to verify memory curation quality.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())