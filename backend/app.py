"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.config.Setting import settings
from apps.config.CorsConfig import cors_config
from apps.config.Tracing import get_logger
from apps.core.domain.controller.ConversationController import router as conversation_router
from apps.core.domain.controller.AlgorithmController import router as algorithm_router
from apps.core.domain.controller.ProductController import router as product_router
from apps.database.Mongo import MongoDB

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Recommendation Agent",
    description="AI-powered recommendation system using LangGraph, RecBole, and Ollama",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# Include routers
app.include_router(conversation_router)
app.include_router(algorithm_router)
app.include_router(product_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting up application...")
    
    # Connect to MongoDB
    try:
        MongoDB.connect()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Continue anyway - MongoDB might not be critical for startup
    
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application...")
    MongoDB.disconnect()
    logger.info("Application shut down")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Recommendation Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mongodb": "connected" if MongoDB._client else "disconnected"
    }

