"""
API endpoints for the FastAPI Documentation Assistant.
"""

import os
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Form

from models.requests import DocstringRequest, GenerateRequest
from models.responses import (
    ReportStatus, ScanResult, DocstringSaveResult, 
    GenerateResult, ProjectFilesResult
)
from core.config import settings
from services.scanner_service import scanner_service
from services.docstring_service import docstring_service
from services.report_service import report_service
from services.confluence_service import confluence_service
from services.coverage_tracker import coverage_tracker

# Create API router
router = APIRouter()


@router.get("/report/status", response_model=ReportStatus)
async def get_report_status():
    """Check if a report file exists and return basic info."""
    status_data = report_service.get_report_status()
    return ReportStatus(**status_data)


@router.get("/report/data")
async def get_report_data():
    """Return the full report data."""
    return report_service.get_report_data()


@router.post("/scan", response_model=ScanResult)
async def scan_project(
    project_path: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Scan uploaded Python files and generate documentation report."""
    items_data, total_files, scan_time = await scanner_service.scan_uploaded_files(
        project_path, files
    )
    
    return ScanResult(
        success=True,
        message=f"Successfully scanned {total_files} files",
        items=items_data,
        total_files=total_files,
        scan_time=scan_time
    )


@router.post("/docstring/save", response_model=DocstringSaveResult)
async def save_docstring(request: DocstringRequest):
    """Save a docstring to the source file."""
    result = docstring_service.save_docstring(request.item, request.docstring)
    return DocstringSaveResult(**result)


@router.post("/docstring/generate", response_model=GenerateResult)
async def generate_docstring(request: GenerateRequest):
    """Generate a docstring using AI or template."""
    docstring = docstring_service.generate_ai_docstring(request.item)
    return GenerateResult(docstring=docstring)


@router.get("/project/files", response_model=ProjectFilesResult)
async def get_project_files():
    """Get list of Python files in the current project."""
    files = scanner_service.get_project_files()
    return ProjectFilesResult(files=files)


@router.post("/scan-local", response_model=ScanResult)
async def scan_local_project(request: dict):
    """Scan a local project path using the CLI scanner."""
    project_path = request.get("project_path")
    
    if not project_path:
        raise HTTPException(status_code=400, detail="project_path is required")
    
    if not os.path.exists(project_path):
        raise HTTPException(status_code=400, detail=f"Path does not exist: {project_path}")
    
    try:
        items_data, total_files, scan_time = await scanner_service.scan_local_project(project_path)
        
        return ScanResult(
            success=True,
            message=f"Successfully scanned {total_files} files from {project_path}",
            items=items_data,
            total_files=total_files,
            scan_time=scan_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/confluence/status")
async def get_confluence_status():
    """Check if Confluence integration is enabled and configured."""
    return {
        "enabled": confluence_service.is_enabled(),
        "url": settings.CONFLUENCE_URL if confluence_service.is_enabled() else None,
        "space_key": settings.CONFLUENCE_SPACE_KEY if confluence_service.is_enabled() else None
    }


@router.post("/confluence/publish-endpoint")
async def publish_endpoint_to_confluence(endpoint_data: dict):
    """Publish a single endpoint documentation to Confluence."""
    if not confluence_service.is_enabled():
        raise HTTPException(status_code=400, detail="Confluence integration is not configured")
    
    try:
        result = confluence_service.publish_endpoint_doc(endpoint_data)
        return {
            "success": True,
            "page_id": result.get('id'),
            "page_url": f"{settings.CONFLUENCE_URL}/wiki/spaces/{settings.CONFLUENCE_SPACE_KEY}/pages/{result.get('id')}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to Confluence: {str(e)}")


@router.post("/confluence/publish-coverage")
async def publish_coverage_to_confluence(request: dict):
    """Publish coverage report to Confluence."""
    if not confluence_service.is_enabled():
        raise HTTPException(status_code=400, detail="Confluence integration is not configured")
    
    items = request.get("items", [])
    title_suffix = request.get("title_suffix")
    
    try:
        result = confluence_service.publish_coverage_report(items, title_suffix)
        return {
            "success": True,
            "page_id": result.get('id'),
            "page_url": f"{settings.CONFLUENCE_URL}/wiki/spaces/{settings.CONFLUENCE_SPACE_KEY}/pages/{result.get('id')}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to Confluence: {str(e)}")

@router.get("/coverage/history")
async def get_coverage_history(
    project_path: Optional[str] = None,
    limit: Optional[int] = 10
):
    """Get coverage history records."""
    history = coverage_tracker.get_coverage_history(project_path, limit)
    return {"history": history, "total_records": len(history)}


@router.get("/coverage/trends")
async def get_coverage_trends(
    project_path: Optional[str] = None,
    days: int = 30
):
    """Get coverage trends over specified period."""
    trends = coverage_tracker.get_coverage_trends(project_path, days)
    return trends


@router.get("/coverage/progress-report")
async def get_progress_report(project_path: Optional[str] = None):
    """Get comprehensive progress report."""
    report = coverage_tracker.generate_progress_report(project_path)
    return report
