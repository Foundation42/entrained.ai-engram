#!/usr/bin/env python3
"""
Comments-as-Engrams Prototype Test

Demonstrates the revolutionary comment system that leverages our Engram infrastructure
for semantic threading, agent participation, and editorial intelligence.
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import List, Dict

class CommentEngramsDemo:
    def __init__(self, engram_url: str = "http://46.62.130.230:8000"):
        self.engram_url = engram_url
        
        # Sample article and users for testing
        self.article_id = "reticle-lithography-breakthrough"
        self.article_title = "Revolutionary Advances in Reticle Lithography"
        
        self.test_users = [
            {"id": "user-alice-photonics", "name": "Alice Chen"},
            {"id": "user-bob-semiconductor", "name": "Bob Martinez"}, 
            {"id": "user-carol-research", "name": "Carol Thompson"},
            {"id": "agent-luna", "name": "Agent Luna"}
        ]
        
    async def run_demo(self):
        """Run the complete Comments-as-Engrams demonstration"""
        print("🧬 COMMENTS-AS-ENGRAMS PROTOTYPE DEMONSTRATION")
        print("=" * 80)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            
            # Phase 1: Store diverse comments
            print("\n📋 PHASE 1: Storing Comments as Engrams")
            print("-" * 50)
            await self._store_sample_comments(client)
            
            # Phase 2: Demonstrate thread reconstruction
            print("\n📋 PHASE 2: Thread Reconstruction")
            print("-" * 50)
            await self._demonstrate_threading(client)
            
            # Phase 3: Semantic similarity search
            print("\n📋 PHASE 3: Semantic Comment Discovery")
            print("-" * 50)
            await self._demonstrate_semantic_search(client)
            
            # Phase 4: Editorial intelligence
            print("\n📋 PHASE 4: Editorial Intelligence")
            print("-" * 50)
            await self._demonstrate_editorial_insights(client)
            
        print("\n" + "=" * 80)
        print("🎯 COMMENTS-AS-ENGRAMS DEMO COMPLETE")
        print("✅ Revolutionary comment system operational!")
        print("=" * 80)
    
    async def _store_sample_comments(self, client: httpx.AsyncClient):
        """Store a variety of sample comments"""
        
        comments = [
            {
                "author": "user-alice-photonics",
                "text": "This breakthrough could revolutionize semiconductor manufacturing! The precision improvements are incredible.",
                "comment_type": "root_comment",
                "resonance_score": 0.9,
                "tags": ["breakthrough", "semiconductor", "manufacturing"]
            },
            {
                "author": "user-bob-semiconductor", 
                "text": "What specific wavelength improvements are we seeing? The paper mentions 193nm but doesn't give specifics.",
                "comment_type": "root_comment",
                "resonance_score": 0.8,
                "tags": ["technical-question", "wavelength", "specifications"]
            },
            {
                "author": "user-carol-research",
                "text": "Has anyone tested this with extreme UV lithography? I'm curious about compatibility.",
                "comment_type": "root_comment", 
                "resonance_score": 0.85,
                "tags": ["question", "EUV", "compatibility"]
            },
            {
                "author": "agent-luna",
                "text": "Great question! EUV compatibility testing is ongoing. I can provide some preliminary data if you're interested.",
                "comment_type": "agent_response",
                "resonance_score": 0.7,
                "tags": ["agent-response", "EUV", "data-offer"],
                "reply_to": None  # Will be set to Carol's comment ID
            }
        ]
        
        stored_comment_ids = []
        
        for i, comment_data in enumerate(comments):
            print(f"💾 Storing comment {i+1}: {comment_data['text'][:50]}...")
            
            # Set reply_to for agent response
            if comment_data["author"] == "agent-luna" and stored_comment_ids:
                comment_data["reply_to"] = stored_comment_ids[-1]  # Reply to Carol's comment
            
            request_data = {
                "author_id": comment_data["author"],
                "article_id": self.article_id,
                "comment_text": comment_data["text"],
                "comment_type": comment_data["comment_type"],
                "article_section": "main",
                "resonance_score": comment_data["resonance_score"],
                "topic_tags": comment_data["tags"],
                "reply_to_comment": comment_data.get("reply_to"),
                "situation_type": "public_discussion"
            }
            
            try:
                response = await client.post(
                    f"{self.engram_url}/cam/comments/store",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    stored_comment_ids.append(result["memory_id"])
                    print(f"  ✅ Stored as memory: {result['memory_id']}")
                    print(f"     Thread ID: {result.get('thread_id', 'N/A')}")
                    print(f"     Reply depth: {result.get('reply_depth', 0)}")
                else:
                    print(f"  ❌ Failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    async def _demonstrate_threading(self, client: httpx.AsyncClient):
        """Show how comments are automatically threaded"""
        print(f"🧵 Reconstructing comment thread for article: {self.article_id}")
        
        try:
            response = await client.get(
                f"{self.engram_url}/cam/comments/article/{self.article_id}/thread",
                params={
                    "include_agents": True,
                    "max_depth": 10,
                    "sort_by": "timestamp"
                }
            )
            
            if response.status_code == 200:
                thread_comments = response.json()
                print(f"📊 Found {len(thread_comments)} comments in thread")
                
                for comment in thread_comments:
                    indent = "  " * comment.get("depth", 0)
                    author_name = self._get_user_name(comment["author_id"])
                    comment_preview = comment["comment_text"][:60] + "..." if len(comment["comment_text"]) > 60 else comment["comment_text"]
                    resonance = comment.get("resonance_score", 0)
                    
                    print(f"{indent}🧠 {author_name}: {comment_preview}")
                    print(f"{indent}   Resonance: {resonance:.2f} | Tags: {comment.get('topic_tags', [])}")
                    
                    if comment.get("handled_by_agent"):
                        print(f"{indent}   🤖 Handled by: {comment['handled_by_agent']}")
                    
            else:
                print(f"❌ Failed to get thread: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Threading error: {e}")
    
    async def _demonstrate_semantic_search(self, client: httpx.AsyncClient):
        """Show semantic comment discovery"""
        search_queries = [
            "wavelength measurements and specifications",
            "EUV lithography compatibility testing", 
            "manufacturing process improvements"
        ]
        
        for query in search_queries:
            print(f"🔍 Searching for comments similar to: '{query}'")
            
            try:
                response = await client.post(
                    f"{self.engram_url}/cam/comments/semantic/similar",
                    params={
                        "comment_text": query,
                        "similarity_threshold": 0.6,
                        "limit": 5,
                        "cross_article": False
                    }
                )
                
                if response.status_code == 200:
                    similar_comments = response.json()
                    print(f"  📊 Found {len(similar_comments)} semantically similar comments")
                    
                    for comment in similar_comments:
                        author_name = self._get_user_name(comment["author_id"])
                        preview = comment["comment_text"][:50] + "..."
                        resonance = comment.get("resonance_score", 0)
                        
                        print(f"    💭 {author_name}: {preview} (resonance: {resonance:.2f})")
                else:
                    print(f"  ❌ Semantic search failed: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Search error: {e}")
    
    async def _demonstrate_editorial_insights(self, client: httpx.AsyncClient):
        """Show editorial intelligence capabilities"""
        insight_types = ["unanswered_gems", "trending_topics", "agent_opportunities"]
        
        for insight_type in insight_types:
            print(f"📈 Generating editorial insights: {insight_type}")
            
            try:
                request_data = {
                    "query_type": insight_type,
                    "article_id": self.article_id,
                    "resonance_threshold": 0.7,
                    "limit": 10
                }
                
                response = await client.post(
                    f"{self.engram_url}/cam/comments/editorial/insights",
                    json=request_data
                )
                
                if response.status_code == 200:
                    insights = response.json()
                    print(f"  📊 Generated {len(insights)} insights")
                    
                    for insight in insights:
                        print(f"    💡 {insight['title']}")
                        print(f"       {insight['description']}")
                        print(f"       Priority: {insight['priority_score']:.2f}")
                        if insight.get('action_suggestions'):
                            print(f"       Actions: {', '.join(insight['action_suggestions'])}")
                else:
                    print(f"  ❌ Insights failed: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Insights error: {e}")
    
    def _get_user_name(self, user_id: str) -> str:
        """Get display name for user ID"""
        for user in self.test_users:
            if user["id"] == user_id:
                return user["name"]
        return user_id


async def main():
    """Run the Comments-as-Engrams demonstration"""
    demo = CommentEngramsDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())