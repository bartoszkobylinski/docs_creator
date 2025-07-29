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
    """Serve the main interface."""
    return FileResponse(f"{settings.FRONTEND_DIR}/index.html")


@router.get("/styles.css")
async def serve_css():
    """Serve the CSS file."""
    return FileResponse(f"{settings.FRONTEND_DIR}/styles.css")


@router.get("/script.js")
async def serve_js():
    """Serve the JavaScript file."""
    return FileResponse(f"{settings.FRONTEND_DIR}/script.js")


@router.get("/dashboard")
async def serve_dashboard():
    """Serve the dashboard interface."""
    return FileResponse("templates/dashboard.html")


@router.get("/static/styles.css")
async def serve_dashboard_css():
    """Serve CSS for dashboard."""
    return FileResponse(f"{settings.FRONTEND_DIR}/styles.css")


@router.get("/static/script.js")
async def serve_dashboard_js():
    """Serve JavaScript for dashboard."""
    return FileResponse("static/dashboard.js")


@router.get("/dashboard/static/script.js")
async def serve_dashboard_specific_js():
    """Serve JavaScript specifically for dashboard route."""
    return FileResponse("static/dashboard.js")