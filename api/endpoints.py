"""
API endpoints for the FastAPI Documentation Assistant.
"""

import os
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException, Form

from models.requests import DocstringRequest, GenerateRequest
from models.responses import (
    ReportStatus, ScanResult, DocstringSaveResult, 
    GenerateResult, ProjectFilesResult
)
from services.scanner_service import scanner_service
from services.docstring_service import docstring_service
from services.report_service import report_service

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