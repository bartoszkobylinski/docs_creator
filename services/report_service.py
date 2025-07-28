"""
Report service for managing documentation reports.
"""

import os
import json
from typing import Dict, List, Any

from fastapi import HTTPException

from core.config import settings


class ReportService:
    """Service for managing documentation reports."""
    
    def get_report_status(self) -> Dict[str, Any]:
        """
        Check if a report file exists and return basic info.
        
        Returns:
            Dictionary with report status information
        """
        if os.path.exists(settings.report_file_path):
            try:
                with open(settings.report_file_path, 'r') as f:
                    data = json.load(f)
                return {
                    "exists": True,
                    "path": settings.report_file_path,
                    "item_count": len(data)
                }
            except Exception:
                pass
        
        return {
            "exists": False,
            "path": "",
            "item_count": 0
        }
    
    def get_report_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return the full report data.
        
        Returns:
            Dictionary containing report items
            
        Raises:
            HTTPException: If report not found or cannot be read
        """
        if not os.path.exists(settings.report_file_path):
            raise HTTPException(status_code=404, detail="Report not found")
        
        try:
            with open(settings.report_file_path, 'r') as f:
                data = json.load(f)
            return {"items": data}
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error reading report: {str(e)}"
            )


# Global report service instance
report_service = ReportService()