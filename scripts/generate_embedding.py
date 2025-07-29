#!/usr/bin/env python3
"""
Script to generate embeddings using Ollama for testing Engram
"""

import httpx
import json
import sys
import asyncio


async def generate_embedding(text: str, ollama_url: str = "http://localhost:11434"):
    """Generate embedding for given text using Ollama"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ollama_url}/api/embeddings",
            json={
                "model": "nomic-embed-text:latest",
                "prompt": text
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding", [])
            return embedding
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None


async def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_embedding.py <text>")
        print("Example: python generate_embedding.py 'Neural network efficiency'")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    print(f"Generating embedding for: '{text}'")
    
    embedding = await generate_embedding(text)
    
    if embedding:
        print(f"\nEmbedding generated successfully!")
        print(f"Dimensions: {len(embedding)}")
        print(f"\nFirst 10 values: {embedding[:10]}")
        
        # Save to file
        output = {
            "text": text,
            "embedding": embedding,
            "dimensions": len(embedding)
        }
        
        with open("embedding_output.json", "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\nFull embedding saved to: embedding_output.json")
    else:
        print("Failed to generate embedding")


if __name__ == "__main__":
    asyncio.run(main())