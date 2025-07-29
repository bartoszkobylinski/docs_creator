"""
Static file serving routes for the frontend.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

from core.config import settings

# Create router for static files
router = APIRouter()


@router.get("/")
async def serve_frontend():
    """Serve the main dashboard interface."""
    return FileResponse(f"{settings.FRONTEND_DIR}/index.html")

@router.get("/dashboard")
async def serve_dashboard():
    """Serve the main dashboard interface."""
    return FileResponse(f"{settings.FRONTEND_DIR}/index.html")


@router.get("/styles.css")
async def serve_css():
    """Serve the CSS file."""
    return FileResponse(f"{settings.FRONTEND_DIR}/styles.css")


@router.get("/script.js")
async def serve_js():
    """Serve the JavaScript file."""
    return FileResponse(f"{settings.FRONTEND_DIR}/script.js")