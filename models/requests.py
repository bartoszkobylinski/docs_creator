"""
Request models for the FastAPI Documentation Assistant API.
"""

from typing import Dict, Any
from pydantic import BaseModel


class DocstringRequest(BaseModel):
    """Request model for saving docstrings."""
    item: Dict[str, Any]
    docstring: str


class GenerateRequest(BaseModel):
    """Request model for generating docstrings with AI."""
    item: Dict[str, Any]