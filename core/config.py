import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application settings
    app_name: str = "entrained.ai-engram"
    api_version: str = "v1"
    debug: bool = False
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_decode_responses: bool = False
    
    # Vector settings
    vector_dimensions: int = 768  # nomic-embed-text uses 768 dimensions
    vector_index_name: str = "engram_vector_idx"
    vector_distance_metric: str = "COSINE"
    vector_algorithm: str = "HNSW"
    
    # Performance settings
    max_connections: int = 50
    connection_timeout: int = 20
    socket_keepalive: bool = True
    
    # API settings
    api_prefix: str = "/cam"
    cors_origins: list = ["*"]
    
    # Embedding service (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text:latest"
    
    class Config:
        env_file = ".env"
        env_prefix = "ENGRAM_"


settings = Settings()