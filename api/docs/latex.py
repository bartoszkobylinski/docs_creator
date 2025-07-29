"""
LaTeX documentation generation endpoints.
"""

from pathlib import Path
from flask import send_file
from flask_smorest import Blueprint as SmorestBlueprint

from api.schemas import DocumentationGenerateSchema
from api.exceptions import APIError
from services.report_service import report_service
from services.latex_service import latex_service
from services.uml_service import uml_service


def create_latex_blueprint() -> SmorestBlueprint:
    """Create LaTeX blueprint."""
    
    bp = SmorestBlueprint(
        'latex', __name__, 
        url_prefix='/latex',
        description='LaTeX documentation endpoints'
    )
    
    @bp.route('/', methods=['POST'])
    @bp.arguments(DocumentationGenerateSchema)
    @bp.response(200)
    def generate_latex_documentation(json_data):
        """Generate LaTeX documentation from current data."""
        # Get current report data
        data = report_service.get_report_data()
        if not data:
            raise APIError("No documentation data available. Please scan a project first.", 
                          status_code=400)
        
        try:
            # Convert to DocItem objects if needed
            from fastdoc.models import DocItem
            items = []
            for item_data in data:
                if isinstance(item_data, dict):
                    item = DocItem(**item_data)
                    items.append(item)
                else:
                    items.append(item_data)
            
            project_name = json_data.get("project_name", "API Documentation")
            include_uml = json_data.get("include_uml", False)
            
            # Generate UML diagrams if requested
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
            
        except Exception as e:
            raise APIError(f"LaTeX generation failed: {str(e)}", status_code=500)
    
    @bp.route('/download/<filename>', methods=['GET'])
    def download_latex_file(filename):
        """Download generated LaTeX or PDF file."""
        # Security check - only allow alphanumeric, dots, dashes, underscores
        if not filename.replace('.', '').replace('_', '').replace('-', '').isalnum():
            raise APIError("Invalid filename", status_code=400)
        
        latex_dir = Path("reports/latex")
        file_path = latex_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            raise APIError("File not found", status_code=404)
        
        # Determine media type
        media_type = "application/octet-stream"
        if filename.endswith('.pdf'):
            media_type = "application/pdf"
        elif filename.endswith('.tex'):
            media_type = "text/plain"
        
        return send_file(
            file_path,
            mimetype=media_type,
            as_attachment=True,
            download_name=filename
        )
    
    return bp