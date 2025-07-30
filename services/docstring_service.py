"""
Docstring service for managing docstring operations.
"""

import os
import json
from typing import Dict, Any

from services.patcher import apply_docitem_patch
from core.config import settings
from services.scanner_service import scanner_service
from services.cost_tracking_service import cost_tracking_service
from services.openai_service import openai_service

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


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
            Exception: If saving fails
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
                raise Exception(result["message"])
                
        except Exception as e:
            raise Exception(f"Error saving docstring: {str(e)}")
    
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
                    # Update has_docstring flag based on whether docstring exists and is not empty
                    report_item['has_docstring'] = bool(docstring and docstring.strip())
                    break
            
            # Save updated report
            with open(settings.report_file_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    def generate_ai_docstring(self, item: Dict[str, Any]) -> tuple[str, bool, Dict[str, Any]]:
        """
        Generate a docstring using AI or fallback to template.
        
        Args:
            item: Documentation item to generate docstring for
            
        Returns:
            tuple: (Generated docstring, True if AI was used, cost info dict)
        """
        # Check if we have valid OpenAI settings
        if not OPENAI_AVAILABLE:
            print("OpenAI library not available")
        else:
            openai_settings = openai_service.get_settings()
            if openai_settings:
                print(f"OpenAI settings found from {openai_settings.get('source', 'unknown')}")
                print(f"Using model: {openai_settings.get('model', 'unknown')}")
            else:
                print("No valid OpenAI settings found")
        
        if OPENAI_AVAILABLE and openai_service.has_valid_settings():
            try:
                docstring, cost_info = self._generate_openai_docstring(item)
                return docstring, True, cost_info
            except Exception as e:
                print(f"OpenAI generation failed: {e}, falling back to template")
        
        # Fallback to template generation
        docstring = self._generate_template_docstring(item)
        return docstring, False, {"cost": 0.0, "tokens_used": 0}
    
    def _generate_openai_docstring(self, item: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Generate docstring using OpenAI and track costs."""
        qualname = item.get('qualname', 'unknown')
        method_type = item.get('method', 'FUNCTION')
        signature = item.get('signature', '')
        source_code = item.get('source', '')
        file_path = item.get('file_path', '')
        
        # Get OpenAI settings
        openai_settings = openai_service.get_settings()
        if not openai_settings:
            raise Exception("No OpenAI settings found")
        
        # Build context for AI
        context = f"Function/Method: {qualname}\n"
        context += f"Type: {method_type}\n"
        if signature:
            context += f"Signature: {signature}\n"
        if file_path:
            context += f"File: {file_path}\n"
        if source_code:
            # Limit source code to prevent token overflow
            limited_source = source_code[:1000] + "..." if len(source_code) > 1000 else source_code
            context += f"Source Code:\n{limited_source}\n"
        
        # Create prompt for OpenAI
        prompt = f"""Write a Python docstring following PEP 257 and Google style format.

{context}

REQUIREMENTS:
1. First line: One sentence summary (what the function does)
2. Args section: List each parameter with type and description
3. Returns section: Describe what is returned and its type  
4. Raises section: List exceptions that can be raised
5. Use clear, simple language
6. No markdown formatting, just plain text

FORMAT EXAMPLE:
'''
Brief description of what this function does.

Args:
    param1 (str): Description of parameter 1.
    param2 (int, optional): Description of parameter 2. Defaults to None.

Returns:
    bool: True if successful, False otherwise.

Raises:
    ValueError: If param1 is empty.
    TypeError: If param1 is not a string.
'''

Return ONLY the docstring content WITHOUT the triple quotes. Do not include the triple quotes in your response."""

        # Call OpenAI API
        client = openai.OpenAI(api_key=openai_settings["api_key"])
        response = client.chat.completions.create(
            model=openai_settings["model"],
            messages=[
                {"role": "system", "content": "You are a Python expert. Write docstrings that follow PEP 257 and Google style. Be concise and clear. Focus on what the function does, its parameters, return value, and exceptions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=openai_settings["max_tokens"],
            temperature=openai_settings["temperature"]
        )
        
        # Extract usage information
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        
        # Track the cost
        cost_info = cost_tracking_service.track_usage(
            model=response.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            context=f"docstring_generation:{qualname}"
        )
        
        content = response.choices[0].message.content.strip()
        
        # Defensive: Strip any triple quotes that AI might have added despite our prompt
        content = content.strip('"""').strip("'''")
        
        return content, cost_info
    
    def _generate_template_docstring(self, item: Dict[str, Any]) -> str:
        """Generate docstring using template fallback."""
        qualname = item.get('qualname', 'unknown')
        method_type = item.get('method', 'FUNCTION')
        signature = item.get('signature', '')
        
        # Generate a basic docstring template
        if method_type == 'FUNCTION':
            if signature:
                # Parse parameters from signature
                params = []
                if '(' in signature and ')' in signature:
                    param_str = signature.split('(')[1].split(')')[0].strip()
                    if param_str and param_str != 'self':
                        param_str = param_str.replace('self, ', '').replace('self', '').strip()
                        if param_str:
                            params = [p.split(':')[0].split('=')[0].strip() for p in param_str.split(',') if p.strip()]
                
                docstring = f"""Brief description of {qualname}.

Args:"""
                if params:
                    for param in params:
                        if param:
                            docstring += f"\n    {param} (type): Description of {param} parameter."
                else:
                    docstring += "\n    None"
                    
                docstring += f"""

Returns:
    type: Description of return value.
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