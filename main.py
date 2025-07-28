"""
Main application entry point for FastAPI Documentation Assistant.
"""

from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from core.config import settings
from api.endpoints import router as api_router
from api.static_files import router as static_router
from models.responses import HealthResult
from services.uml_service import uml_service
from services.report_service import report_service


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Initialize FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        debug=settings.DEBUG
    )
    
    # Initialize Jinja2 templates
    templates = Jinja2Templates(directory="templates")
    
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
    
    # UML page endpoints
    @app.get("/uml", response_class=HTMLResponse)
    async def uml_page(request: Request, show_source: bool = False):
        """Render UML diagrams page."""
        # Check if we have data available
        try:
            data = report_service.get_report_data()
            has_data = data and data.get("items")
        except:
            has_data = False
        
        return templates.TemplateResponse("uml.html", {
            "request": request,
            "has_data": has_data,
            "show_source": show_source,
            "selected_config": "overview",
            "result": None
        })
    
    @app.post("/uml", response_class=HTMLResponse)
    async def generate_uml(request: Request, config: str = Form("overview"), show_source: bool = Form(False)):
        """Generate and display UML diagram."""
        try:
            # Get current data
            data = report_service.get_report_data()
            if not data or not data.get("items"):
                return templates.TemplateResponse("uml.html", {
                    "request": request,
                    "has_data": False,
                    "show_source": show_source,
                    "selected_config": config,
                    "result": None
                })
            
            # Convert dictionary items back to DocItem objects
            from fastdoc.models import DocItem
            items = []
            for item_data in data["items"]:
                item = DocItem(**item_data)
                items.append(item)
            
            # Generate UML diagrams
            result = uml_service.generate_uml_diagrams(items, config)
            
            return templates.TemplateResponse("uml.html", {
                "request": request,
                "has_data": True,
                "show_source": show_source,
                "selected_config": config,
                "result": result
            })
            
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            return templates.TemplateResponse("uml.html", {
                "request": request,
                "has_data": True,
                "show_source": show_source,
                "selected_config": config,
                "result": error_result
            })
    
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