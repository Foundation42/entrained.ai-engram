import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.redis_client_hash import redis_client
from core.redis_client_multi_entity import redis_multi_entity_client
from services.embedding import embedding_service
from api.endpoints import router
from api.multi_entity_endpoints import router as multi_entity_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Engram memory system...")
    
    # Connect to Redis
    redis_client.connect()
    redis_multi_entity_client.connect()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Engram...")
    redis_client.close()
    # Note: Add close method to multi-entity client if needed
    await embedding_service.close()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix=settings.api_prefix)
app.include_router(multi_entity_router, prefix="/cam")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.api_version,
        "status": "running",
        "description": "Content Addressable Memory system for AI agents",
        "features": ["single-agent", "multi-entity", "witness-based-access"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_client.client.ping()
        
        return {
            "status": "healthy",
            "redis": "connected",
            "vector_index": redis_client.vector_index_created
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )