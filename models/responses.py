"""
Response models for the FastAPI Documentation Assistant API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ReportStatus(BaseModel):
    """Response model for report status."""
    exists: bool
    path: str
    item_count: int


class ScanResult(BaseModel):
    """Response model for scan results."""
    success: bool
    message: str
    items: List[Dict[str, Any]]
    total_files: int
    scan_time: float


class DocstringSaveResult(BaseModel):
    """Response model for docstring save operations."""
    success: bool
    message: str
    backup_path: Optional[str] = None


class GenerateResult(BaseModel):
    """Response model for AI docstring generation."""
    docstring: str


class HealthResult(BaseModel):
    """Response model for health check."""
    status: str
    version: str


class ProjectFile(BaseModel):
    """Model for project file information."""
    name: str
    path: str
    full_path: str


class ProjectFilesResult(BaseModel):
    """Response model for project files listing."""
    files: List[ProjectFile]