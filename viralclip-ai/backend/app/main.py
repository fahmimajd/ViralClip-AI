"""
ViralClip AI - FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from loguru import logger
import uvicorn

from app.core.config import settings
from app.api.routes import router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Initialize FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered viral clip generator for YouTube videos",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create necessary directories
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    
    # Mount static files for serving outputs
    app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
    
    # Include API routes
    app.include_router(router)
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"📁 Upload directory: {settings.UPLOAD_DIR}")
        logger.info(f"📁 Output directory: {settings.OUTPUT_DIR}")
        logger.info(f"🔗 API prefix: {settings.API_PREFIX}")
        
        # Log configuration
        if settings.DEBUG:
            logger.warning("⚠️  DEBUG mode is enabled")
        
        if not settings.GROQ_API_KEY and not settings.OPENAI_API_KEY:
            logger.warning("⚠️  No LLM API key configured. LLM features will use fallback scoring.")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("👋 Shutting down application")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
            "health": f"{settings.API_PREFIX}/health"
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1  # Set to number of CPU cores in production
    )
