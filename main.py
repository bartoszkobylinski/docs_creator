"""
Main application entry point for FastAPI Documentation Assistant.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from api.endpoints import router as api_router
from api.static_files import router as static_router
from models.responses import HealthResult


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Initialize FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        debug=settings.DEBUG
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files for frontend assets
    app.mount("/static", StaticFiles(directory=settings.FRONTEND_DIR), name="static")
    
    # Include API routes
    app.include_router(api_router, prefix="/api", tags=["API"])
    
    # Include static file routes (frontend)
    app.include_router(static_router, tags=["Frontend"])
    
    # Health check endpoint
    @app.get("/health", response_model=HealthResult, tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return HealthResult(status="healthy", version=settings.VERSION)
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting {settings.APP_NAME}...")
    print(f"Frontend will be available at: http://{settings.HOST}:{settings.PORT}")
    print(f"API docs will be available at: http://{settings.HOST}:{settings.PORT}/docs")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )