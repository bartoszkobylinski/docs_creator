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
    """Redirect to modern dashboard."""
    return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/legacy")
async def serve_legacy_frontend():
    """Serve the legacy frontend HTML file."""
    return FileResponse(f"{settings.FRONTEND_DIR}/index.html")


@router.get("/styles.css")
async def serve_css():
    """Serve the CSS file."""
    return FileResponse(f"{settings.FRONTEND_DIR}/styles.css")


@router.get("/script.js")
async def serve_js():
    """Serve the JavaScript file."""
    return FileResponse(f"{settings.FRONTEND_DIR}/script.js")

@router.get("/styles_new.css")
async def serve_new_css():
    """Serve the new modern CSS file."""
    return FileResponse(f"{settings.FRONTEND_DIR}/styles_new.css")

@router.get("/script_new.js")
async def serve_new_js():
    """Serve the new modern JavaScript file."""
    return FileResponse(f"{settings.FRONTEND_DIR}/script_new.js")