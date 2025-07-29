"""
API endpoints for the FastAPI Documentation Assistant.
"""

import os
from pathlib import Path
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
from services.uml_service import uml_service
from services.latex_service import latex_service
from services.markdown_service import markdown_service

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


@router.get("/current-data")
async def get_current_data():
    """Return current scan data for dashboard."""
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


@router.post("/confluence/save-settings")
async def save_confluence_settings(request: dict):
    """Save Confluence settings and test the connection."""
    url = request.get("url", "").strip()
    username = request.get("username", "").strip()
    token = request.get("token", "").strip()
    space_key = request.get("space_key", "").strip()
    
    if not all([url, username, token, space_key]):
        raise HTTPException(status_code=400, detail="All fields are required")
    
    try:
        # Test the connection and save settings
        result = confluence_service.save_and_test_settings(url, username, token, space_key)
        return {"success": True, "message": "Settings saved and tested successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save settings: {str(e)}")


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


@router.post("/confluence/publish-uml")
async def publish_uml_to_confluence(request: dict):
    """Publish UML diagram to Confluence."""
    if not confluence_service.is_enabled():
        raise HTTPException(status_code=400, detail="Confluence integration is not configured")
    
    diagram_data = request.get("diagram_data", {})
    title_suffix = request.get("title_suffix")
    
    if not diagram_data:
        raise HTTPException(status_code=400, detail="No diagram data provided")
    
    try:
        result = confluence_service.publish_uml_diagram(diagram_data, title_suffix)
        return {
            "success": True,
            "page_id": result.get('id'),
            "page_url": f"{settings.CONFLUENCE_URL}/wiki/spaces/{settings.CONFLUENCE_SPACE_KEY}/pages/{result.get('id')}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to Confluence: {str(e)}")


@router.post("/docs/latex")
async def generate_latex_documentation(request: dict):
    """Generate LaTeX documentation from current data."""
    try:
        # Get current report data
        data = report_service.get_report_data()
        if not data or not data.get("items"):
            raise HTTPException(status_code=400, detail="No documentation data available. Please scan a project first.")
        
        # Convert dictionary items back to DocItem objects
        from fastdoc.models import DocItem
        items = []
        for item_data in data["items"]:
            item = DocItem(**item_data)
            items.append(item)
        
        # Get optional parameters
        project_name = request.get("project_name", "API Documentation")
        include_uml = request.get("include_uml", False)
        
        # Get UML diagrams if requested
        uml_diagrams = None
        if include_uml:
            try:
                uml_result = uml_service.generate_uml_diagrams(items, "overview")
                if uml_result.get("success"):
                    uml_diagrams = uml_result
            except Exception as e:
                print(f"UML generation failed: {e}")
        
        # Generate LaTeX documentation
        result = latex_service.generate_complete_documentation(
            doc_items=items,
            project_name=project_name,
            uml_diagrams=uml_diagrams
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LaTeX generation failed: {str(e)}")


@router.get("/docs/latex/download/{filename}")
async def download_latex_file(filename: str):
    """Download generated LaTeX or PDF file."""
    from fastapi.responses import FileResponse
    import os
    
    # Security check - only allow files from latex output directory
    if not filename.replace('.', '').replace('_', '').replace('-', '').isalnum():
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    latex_dir = Path("reports/latex")
    file_path = latex_dir / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    if filename.endswith('.pdf'):
        media_type = "application/pdf"
    elif filename.endswith('.tex'):
        media_type = "text/plain"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )

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


@router.post("/uml/generate")
async def generate_uml_diagrams(request: dict):
    """Generate UML diagrams from current documentation items."""
    items_data = request.get("items", [])
    config_name = request.get("config", "overview")
    
    if not items_data:
        raise HTTPException(status_code=400, detail="No items provided for UML generation")
    
    # Convert dictionary items back to DocItem objects
    from fastdoc.models import DocItem
    items = []
    for item_data in items_data:
        item = DocItem(**item_data)
        items.append(item)
    
    try:
        result = uml_service.generate_uml_diagrams(items, config_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"UML generation failed: {str(e)}")


@router.post("/uml/generate-custom")
async def generate_custom_uml_diagram(request: dict):
    """Generate UML diagram with custom configuration."""
    items_data = request.get("items", [])
    custom_config = request.get("config", {})
    
    if not items_data:
        raise HTTPException(status_code=400, detail="No items provided for UML generation")
    
    # Convert dictionary items back to DocItem objects
    from fastdoc.models import DocItem
    items = []
    for item_data in items_data:
        item = DocItem(**item_data)
        items.append(item)
    
    try:
        result = uml_service.generate_custom_diagram(items, custom_config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Custom UML generation failed: {str(e)}")


@router.get("/uml/configurations")
async def get_uml_configurations():
    """Get available UML diagram configurations."""
    return uml_service.get_available_configurations()


@router.get("/uml/cache/{cache_key}")
@router.head("/uml/cache/{cache_key}")
async def get_cached_diagram(cache_key: str):
    """Serve cached UML diagram image."""
    from fastapi.responses import FileResponse
    from fastapi import Response
    
    print(f"Cache request for: {cache_key}")
    
    cached_file = uml_service.get_cached_diagram(cache_key)
    print(f"Cache file path: {cached_file}")
    
    if not cached_file:
        print(f"Cache file not found for key: {cache_key}")
        raise HTTPException(status_code=404, detail="Diagram not found in cache")
    
    print(f"Cache file exists: {cached_file.exists()}")
    print(f"Cache file size: {cached_file.stat().st_size if cached_file.exists() else 'N/A'}")
    
    # Determine media type based on file extension
    if cache_key.endswith('.svg'):
        media_type = "image/svg+xml"
    elif cache_key.endswith('.txt'):
        media_type = "text/plain"
    else:
        media_type = "image/png"
    
    print(f"Serving with media type: {media_type}")
    
    # Add CORS headers for image serving
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Headers": "*",
        "Cache-Control": "public, max-age=3600"
    }
    
    return FileResponse(
        cached_file,
        media_type=media_type,
        filename=cache_key,
        headers=headers
    )


@router.post("/docs/markdown")
async def generate_markdown_documentation(request: dict):
    """Generate Markdown documentation for Sphinx and Confluence."""
    try:
        # Get current report data
        data = report_service.get_report_data()
        if not data or not data.get("items"):
            raise HTTPException(status_code=400, detail="No documentation data available. Please scan a project first.")
        
        # Convert dictionary items back to DocItem objects
        from fastdoc.models import DocItem
        items = []
        for item_data in data["items"]:
            item = DocItem(**item_data)
            items.append(item)
        
        # Get optional parameters
        project_name = request.get("project_name", "API Documentation")
        include_uml = request.get("include_uml", True)
        
        # Get UML diagrams if requested
        uml_data = None
        if include_uml:
            try:
                uml_result = uml_service.generate_uml_diagrams(items, "overview")
                if uml_result.get("success"):
                    uml_data = uml_result
            except Exception as e:
                print(f"UML generation for Markdown failed: {e}")
        
        # Generate Markdown documentation
        result = markdown_service.generate_documentation(
            items=items,
            project_name=project_name,
            include_uml=include_uml,
            uml_data=uml_data
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Markdown generation failed: {str(e)}")


@router.post("/confluence/publish-markdown")
async def publish_markdown_to_confluence(request: dict):
    """Publish Markdown documentation to Confluence."""
    if not confluence_service.is_enabled():
        raise HTTPException(status_code=400, detail="Confluence integration is not configured")
    
    # First generate Markdown documentation
    markdown_result = await generate_markdown_documentation(request)
    
    if not markdown_result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to generate Markdown documentation")
    
    # Get the confluence master document
    confluence_master_path = Path(markdown_result["files"]["confluence_master"])
    
    try:
        # Read the master document content
        with open(confluence_master_path, 'r') as f:
            content = f.read()
        
        # Create the page title
        project_name = request.get("project_name", "API Documentation")
        title_suffix = request.get("title_suffix", None)
        title = f"{project_name} - Complete Documentation"
        if title_suffix:
            title = f"{title} - {title_suffix}"
        
        # Publish to Confluence
        result = confluence_service.create_or_update_page(
            title=title,
            content=content,
            parent_id=settings.CONFLUENCE_PARENT_PAGE_ID if hasattr(settings, 'CONFLUENCE_PARENT_PAGE_ID') else None
        )
        
        return {
            "success": True,
            "page_id": result.get('id'),
            "page_url": f"{settings.CONFLUENCE_URL}/wiki/spaces/{settings.CONFLUENCE_SPACE_KEY}/pages/{result.get('id')}",
            "markdown_files": markdown_result["files"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to Confluence: {str(e)}")


@router.get("/docs/markdown/download")
async def download_markdown_documentation(project_name: str = "API_Documentation"):
    """Download all Markdown documentation files as a ZIP archive."""
    from fastapi.responses import FileResponse
    import zipfile
    import tempfile
    from datetime import datetime
    
    docs_dir = Path("reports/docs")
    
    if not docs_dir.exists() or not any(docs_dir.iterdir()):
        raise HTTPException(status_code=404, detail="No Markdown documentation found. Please generate it first.")
    
    # Create filename with project name and timestamp
    timestamp = datetime.now().strftime("%d_%m_%Y")
    safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_project_name = safe_project_name.replace(' ', '_')
    if not safe_project_name:
        safe_project_name = "documentation"
    
    zip_filename = f"{safe_project_name}_markdown_{timestamp}.zip"
    
    # Create a temporary ZIP file
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.zip', delete=False) as tmp_file:
        zip_path = tmp_file.name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all markdown files to the ZIP
            for md_file in docs_dir.glob("*.md"):
                zipf.write(md_file, arcname=md_file.name)
        
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=zip_filename,
        headers={
            "Content-Disposition": f"attachment; filename={zip_filename}"
        }
    )
