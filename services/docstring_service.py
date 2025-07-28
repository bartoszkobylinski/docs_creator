"""
Docstring service for managing docstring operations.
"""

import os
import json
from typing import Dict, Any

from fastapi import HTTPException

from services.patcher import apply_docitem_patch
from core.config import settings
from services.scanner_service import scanner_service


class DocstringService:
    """Service for managing docstring operations."""
    
    def save_docstring(
        self, 
        item: Dict[str, Any], 
        docstring: str
    ) -> Dict[str, Any]:
        """
        Save a docstring to the source file.
        
        Args:
            item: Documentation item containing file and location info
            docstring: The docstring content to save
            
        Returns:
            Dictionary with success status and details
            
        Raises:
            HTTPException: If saving fails
        """
        try:
            # Apply the docstring patch
            result = apply_docitem_patch(
                item,
                docstring,
                create_backup_file=True,
                base_path=scanner_service.current_project_path or "."
            )
            
            if result["success"]:
                # Update the report file
                self._update_report_file(item, docstring)
                
                return {
                    "success": True,
                    "message": result["message"],
                    "backup_path": result.get("backup_path")
                }
            else:
                raise HTTPException(status_code=500, detail=result["message"])
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving docstring: {str(e)}")
    
    def _update_report_file(self, item: Dict[str, Any], docstring: str) -> None:
        """Update the report file with new docstring."""
        if os.path.exists(settings.report_file_path):
            with open(settings.report_file_path, 'r') as f:
                data = json.load(f)
            
            # Find and update the item
            for report_item in data:
                if (report_item.get('qualname') == item.get('qualname') and
                    report_item.get('module') == item.get('module') and
                    report_item.get('lineno') == item.get('lineno')):
                    report_item['docstring'] = docstring
                    break
            
            # Save updated report
            with open(settings.report_file_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    def generate_ai_docstring(self, item: Dict[str, Any]) -> str:
        """
        Generate a docstring using AI or template.
        
        Args:
            item: Documentation item to generate docstring for
            
        Returns:
            Generated docstring
        """
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
        
        return docstring.strip()


# Global docstring service instance
docstring_service = DocstringService()