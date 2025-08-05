import httpx
import logging
import os
from typing import List, Optional
import numpy as np

from core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using OpenAI"""
    
    def __init__(self):
        # Use OpenAI API for embeddings
        self.api_key = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
        self.model = "text-embedding-3-small"
        self.base_url = "https://api.openai.com/v1"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        if not self.api_key:
            logger.error("OpenAI API key not configured")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for given text using OpenAI"""
        if not self.api_key:
            logger.error("OpenAI API key not available")
            return None
            
        try:
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": text,
                    "encoding_format": "float"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data["data"][0]["embedding"]
                
                # OpenAI text-embedding-3-small uses 1536 dimensions
                expected_dims = 1536
                if len(embedding) != expected_dims:
                    logger.warning(
                        f"Embedding dimension mismatch: expected {expected_dims}, "
                        f"got {len(embedding)}"
                    )
                
                logger.debug(f"Generated embedding with {len(embedding)} dimensions")
                return embedding
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def combine_vectors(self, vectors: List[List[float]], weights: Optional[List[float]] = None) -> List[float]:
        """Combine multiple vectors with optional weights"""
        if not vectors:
            return []
        
        # Convert to numpy arrays
        vec_array = np.array(vectors)
        
        if weights:
            weights_array = np.array(weights)
            # Normalize weights
            weights_array = weights_array / weights_array.sum()
            # Weighted average
            combined = np.average(vec_array, axis=0, weights=weights_array)
        else:
            # Simple average
            combined = np.mean(vec_array, axis=0)
        
        # Normalize the combined vector
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        
        return combined.tolist()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global embedding service instance
embedding_service = EmbeddingService()