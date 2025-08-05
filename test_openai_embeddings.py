#!/usr/bin/env python3
"""
Test OpenAI embedding service integration
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.embedding import embedding_service
from core.config import settings

async def test_openai_embeddings():
    """Test OpenAI embedding generation"""
    print("🧪 TESTING OPENAI EMBEDDING SERVICE")
    print("=" * 50)
    
    test_texts = [
        "Hello, my name is Christian and I live in Liversedge.",
        "I am a software engineer who loves Python programming.",
        "The weather is nice today and I feel great.",
        "Machine learning and AI are fascinating topics."
    ]
    
    print(f"📊 Configuration:")
    print(f"   Vector dimensions: {settings.vector_dimensions}")
    print(f"   OpenAI API key configured: {'✅' if settings.openai_api_key else '❌'}")
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n🔍 Test {i}: {text[:50]}...")
        
        try:
            embedding = await embedding_service.generate_embedding(text)
            
            if embedding:
                print(f"   ✅ Generated embedding: {len(embedding)} dimensions")
                print(f"   📊 Sample values: {embedding[:5]}...")
                
                # Verify dimensions match configuration
                if len(embedding) == settings.vector_dimensions:
                    print(f"   ✅ Dimensions match configuration: {settings.vector_dimensions}")
                else:
                    print(f"   ❌ Dimension mismatch: expected {settings.vector_dimensions}, got {len(embedding)}")
            else:
                print(f"   ❌ Failed to generate embedding")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test with longer text
    print(f"\n🔍 Test with longer text...")
    long_text = "This is a much longer text that contains multiple sentences and concepts. It talks about software development, artificial intelligence, machine learning, and various technical topics that might be more challenging to embed effectively."
    
    try:
        embedding = await embedding_service.generate_embedding(long_text)
        if embedding:
            print(f"   ✅ Long text embedding: {len(embedding)} dimensions")
        else:
            print(f"   ❌ Failed to generate embedding for long text")
    except Exception as e:
        print(f"   ❌ Error with long text: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 OpenAI Embedding Test Complete")

if __name__ == "__main__":
    asyncio.run(test_openai_embeddings())