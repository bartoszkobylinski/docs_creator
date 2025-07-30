"""
Business overview service for managing project business descriptions.
"""

import os
import json
from typing import Dict, Any, Optional
from core.config import settings


class BusinessService:
    """Service for managing business overview information."""
    
    def __init__(self):
        self.business_file_path = os.path.join(os.path.dirname(settings.report_file_path), "business_overview.json")
    
    def save_business_overview(
        self, 
        project_purpose: str, 
        business_context: str, 
        key_business_value: str
    ) -> Dict[str, Any]:
        """
        Save business overview information.
        
        Args:
            project_purpose: 2-3 sentences describing what the project does
            business_context: 2-3 sentences describing the business context
            key_business_value: 2-3 sentences describing the key business value
            
        Returns:
            Dictionary with success status and message
        """
        try:
            business_data = {
                "project_purpose": project_purpose.strip(),
                "business_context": business_context.strip(), 
                "key_business_value": key_business_value.strip(),
                "last_updated": self._get_current_timestamp()
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.business_file_path), exist_ok=True)
            
            # Save to JSON file
            with open(self.business_file_path, 'w', encoding='utf-8') as f:
                json.dump(business_data, f, indent=2, ensure_ascii=False)
                
            return {
                "success": True,
                "message": "Business overview saved successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error saving business overview: {str(e)}"
            }
    
    def get_business_overview(self) -> Optional[Dict[str, str]]:
        """
        Load business overview information.
        
        Returns:
            Dictionary with business overview data or None if not found
        """
        try:
            if os.path.exists(self.business_file_path):
                with open(self.business_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        "project_purpose": data.get("project_purpose", ""),
                        "business_context": data.get("business_context", ""),
                        "key_business_value": data.get("key_business_value", ""),
                        "last_updated": data.get("last_updated", "")
                    }
            return None
            
        except Exception as e:
            print(f"Error loading business overview: {e}")
            return None
    
    def has_business_overview(self) -> bool:
        """Check if business overview exists and has content."""
        data = self.get_business_overview()
        if not data:
            return False
            
        return bool(
            data.get("project_purpose", "").strip() or 
            data.get("business_context", "").strip() or 
            data.get("key_business_value", "").strip()
        )
    
    def get_formatted_business_overview(self) -> str:
        """
        Get business overview formatted for documentation output.
        
        Returns:
            Formatted string ready for inclusion in documentation
        """
        data = self.get_business_overview()
        if not data:
            return ""
            
        sections = []
        
        if data.get("project_purpose", "").strip():
            sections.append(f"**Project Purpose:**\n{data['project_purpose']}")
            
        if data.get("business_context", "").strip():
            sections.append(f"**Business Context:**\n{data['business_context']}")
            
        if data.get("key_business_value", "").strip():
            sections.append(f"**Key Business Value:**\n{data['key_business_value']}")
            
        if sections:
            return "# Business Overview\n\n" + "\n\n".join(sections) + "\n\n"
        
        return ""
    
    def get_latex_formatted_business_overview(self) -> str:
        """
        Get business overview formatted for LaTeX output.
        
        Returns:
            LaTeX-formatted string ready for inclusion in PDF documentation
        """
        data = self.get_business_overview()
        if not data:
            return ""
            
        sections = []
        
        if data.get("project_purpose", "").strip():
            sections.append(f"\\textbf{{Project Purpose:}} {self._escape_latex(data['project_purpose'])}")
            
        if data.get("business_context", "").strip():
            sections.append(f"\\textbf{{Business Context:}} {self._escape_latex(data['business_context'])}")
            
        if data.get("key_business_value", "").strip():
            sections.append(f"\\textbf{{Key Business Value:}} {self._escape_latex(data['key_business_value'])}")
            
        if sections:
            return "\\section{Business Overview}\n\n" + "\n\n".join(sections) + "\n\n"
        
        return ""
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        replacements = {
            '&': '\\&',
            '%': '\\%', 
            '$': '\\$',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '~': '\\textasciitilde{}',
            '\\': '\\textbackslash{}'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for tracking updates."""
        from datetime import datetime
        return datetime.now().isoformat()


# Global business service instance
business_service = BusinessService()