"""
Report service for managing documentation reports.
"""

import os
import json
from typing import Dict, List, Any

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
    
    def get_report_data(self) -> List[Dict[str, Any]]:
        """
        Return the full report data as a list of items.
        
        Returns:
            List of report items, empty list if no report exists
        """
        if not os.path.exists(settings.report_file_path):
            return []
        
        try:
            with open(settings.report_file_path, 'r') as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error reading report: {str(e)}")
            return []


# Global report service instance
report_service = ReportService()