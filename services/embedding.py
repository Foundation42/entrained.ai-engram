import httpx
import logging
from typing import List, Optional
import numpy as np

from core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Ollama"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_embedding_model
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for given text"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data.get("embedding", [])
                
                # Ensure correct dimensions
                if len(embedding) != settings.vector_dimensions:
                    logger.warning(
                        f"Embedding dimension mismatch: expected {settings.vector_dimensions}, "
                        f"got {len(embedding)}"
                    )
                
                return embedding
            else:
                logger.error(f"Failed to generate embedding: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
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