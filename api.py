"""
FastAPI REST API for the Documentation Assistant frontend.
Provides endpoints for scanning projects and managing docstrings.
"""

import os
import json
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from fastdoc.scanner import scan_file
from scripts.patcher import apply_docitem_patch

# Initialize FastAPI app
app = FastAPI(title="FastAPI Documentation Assistant API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve frontend files directly from root
@app.get("/styles.css")
async def serve_css():
    return FileResponse("frontend/styles.css")

@app.get("/script.js")
async def serve_js():
    return FileResponse("frontend/script.js")

# Global variables
current_report_path = "comprehensive_report.json"
current_project_path = None

# Pydantic models
class DocstringRequest(BaseModel):
    item: Dict[str, Any]
    docstring: str

class GenerateRequest(BaseModel):
    item: Dict[str, Any]

class ReportStatus(BaseModel):
    exists: bool
    path: str
    item_count: int

class ScanResult(BaseModel):
    success: bool
    message: str
    items: List[Dict[str, Any]]
    total_files: int
    scan_time: float

# Root endpoint - serve the frontend
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

# Report status endpoint
@app.get("/report/status", response_model=ReportStatus)
async def get_report_status():
    """Check if a report file exists and return basic info."""
    if os.path.exists(current_report_path):
        try:
            with open(current_report_path, 'r') as f:
                data = json.load(f)
            return ReportStatus(
                exists=True,
                path=current_report_path,
                item_count=len(data)
            )
        except Exception:
            pass
    
    return ReportStatus(exists=False, path="", item_count=0)

# Get report data
@app.get("/report/data")
async def get_report_data():
    """Return the full report data."""
    if not os.path.exists(current_report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        with open(current_report_path, 'r') as f:
            data = json.load(f)
        return {"items": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading report: {str(e)}")

# Scan project endpoint
@app.post("/scan", response_model=ScanResult)
async def scan_project(
    project_path: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Scan uploaded Python files and generate documentation report."""
    import time
    start_time = time.time()
    
    try:
        # Create temporary directory for uploaded files
        temp_dir = tempfile.mkdtemp()
        global current_project_path
        current_project_path = temp_dir
        
        print(f"Created temp directory: {temp_dir}")
        print(f"Received {len(files)} files")
        
        # Save uploaded files
        file_paths = []
        for file in files:
            print(f"Processing file: {file.filename}")
            
            if not file.filename.endswith('.py'):
                print(f"Skipping non-Python file: {file.filename}")
                continue
            
            # Create subdirectories if needed (preserve structure)
            file_path = os.path.join(temp_dir, file.filename)
            file_dir = os.path.dirname(file_path)
            
            print(f"File path: {file_path}")
            print(f"File dir: {file_dir}")
            
            # Ensure directory exists
            if file_dir and file_dir != temp_dir:
                os.makedirs(file_dir, exist_ok=True)
                print(f"Created directory: {file_dir}")
            
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            
            file_paths.append(file_path)
            print(f"Saved file: {file_path}")
        
        print(f"Total Python files saved: {len(file_paths)}")
        
        if not file_paths:
            raise HTTPException(status_code=400, detail="No Python files found")
        
        # Scan all Python files
        all_items = []
        for file_path in file_paths:
            try:
                items = scan_file(file_path)
                all_items.extend(items)
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")
                continue
        
        # Convert to dictionaries for JSON serialization
        items_data = [item.__dict__ for item in all_items]
        
        # Save report
        with open(current_report_path, 'w') as f:
            json.dump(items_data, f, indent=2)
        
        scan_time = time.time() - start_time
        
        return ScanResult(
            success=True,
            message=f"Successfully scanned {len(file_paths)} files",
            items=items_data,
            total_files=len(file_paths),
            scan_time=round(scan_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scanning failed: {str(e)}")

# Save docstring endpoint
@app.post("/docstring/save")
async def save_docstring(request: DocstringRequest):
    """Save a docstring to the source file."""
    try:
        # Apply the docstring patch
        result = apply_docitem_patch(
            request.item,
            request.docstring,
            create_backup_file=True,
            base_path=current_project_path or "."
        )
        
        if result["success"]:
            # Update the report file
            if os.path.exists(current_report_path):
                with open(current_report_path, 'r') as f:
                    data = json.load(f)
                
                # Find and update the item
                for item in data:
                    if (item.get('qualname') == request.item.get('qualname') and
                        item.get('module') == request.item.get('module') and
                        item.get('lineno') == request.item.get('lineno')):
                        item['docstring'] = request.docstring
                        break
                
                # Save updated report
                with open(current_report_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            return {
                "success": True,
                "message": result["message"],
                "backup_path": result.get("backup_path")
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving docstring: {str(e)}")

# Generate docstring with AI
@app.post("/docstring/generate")
async def generate_docstring(request: GenerateRequest):
    """Generate a docstring using OpenAI API."""
    try:
        # This is a simplified version - you might want to integrate with OpenAI directly
        # For now, return a placeholder
        item = request.item
        
        # Extract basic info
        qualname = item.get('qualname', 'unknown')
        method_type = item.get('method', 'FUNCTION')
        signature = item.get('signature', '')
        
        # Generate a basic docstring template
        if method_type == 'FUNCTION':
            if signature:
                docstring = f"""Brief description of {qualname}.
                
Args:
    {signature.replace('self, ', '').replace('self', '') if 'self' in signature else signature}

Returns:
    Description of return value.

Raises:
    Exception: Description of when this exception is raised.
"""
            else:
                docstring = f"Brief description of {qualname}."
        elif method_type == 'CLASS':
            docstring = f"""Class {qualname}.
            
This class provides functionality for...

Attributes:
    attribute_name: Description of attribute.

Methods:
    method_name: Description of method.
"""
        else:
            docstring = f"Documentation for {qualname}."
        
        return {"docstring": docstring.strip()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating docstring: {str(e)}")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

# Get project files
@app.get("/project/files")
async def get_project_files():
    """Get list of Python files in the current project."""
    if not current_project_path or not os.path.exists(current_project_path):
        raise HTTPException(status_code=404, detail="No project loaded")
    
    files = []
    for root, _, filenames in os.walk(current_project_path):
        for filename in filenames:
            if filename.endswith('.py'):
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, current_project_path)
                files.append({
                    "name": filename,
                    "path": rel_path,
                    "full_path": full_path
                })
    
    return {"files": files}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting FastAPI Documentation Assistant...")
    print("📖 Frontend will be available at: http://localhost:8000")
    print("🔧 API docs will be available at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)