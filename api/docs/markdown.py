"""
Markdown documentation generation endpoints.
"""

import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from flask import send_file
from flask_smorest import Blueprint as SmorestBlueprint

from api.schemas import DocumentationGenerateSchema, ConfluencePublishSchema
from api.exceptions import APIError
from services.report_service import report_service
from services.markdown_service import markdown_service
from services.confluence_service import confluence_service
from services.uml_service import uml_service
from core.config import settings


def create_markdown_blueprint() -> SmorestBlueprint:
    """Create Markdown blueprint."""
    
    bp = SmorestBlueprint(
        'markdown', __name__, 
        url_prefix='/markdown',
        description='Markdown documentation endpoints'
    )
    
    @bp.route('/', methods=['POST'])
    @bp.arguments(DocumentationGenerateSchema)
    @bp.response(200)
    def generate_markdown_documentation(json_data):
        """Generate Markdown documentation for Sphinx and Confluence."""
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
            include_uml = json_data.get("include_uml", True)
            
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
            
        except Exception as e:
            raise APIError(f"Markdown generation failed: {str(e)}", status_code=500)
    
    @bp.route('/download', methods=['GET'])
    @bp.arguments({'project_name': {'type': 'string', 'required': False, 'default': 'API_Documentation'}}, location='query')
    def download_markdown_documentation(query_args):
        """Download all Markdown documentation files as a ZIP archive."""
        project_name = query_args.get('project_name', 'API_Documentation')
        
        docs_dir = Path("reports/docs")
        
        if not docs_dir.exists() or not any(docs_dir.iterdir()):
            raise APIError("No Markdown documentation found. Please generate it first.", 
                          status_code=404)
        
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
        
        return send_file(
            zip_path,
            mimetype="application/zip",
            as_attachment=True,
            download_name=zip_filename
        )
    
    @bp.route('/publish/confluence', methods=['POST'])
    @bp.arguments(ConfluencePublishSchema)
    @bp.response(200)
    def publish_markdown_to_confluence(json_data):
        """Publish Markdown documentation to Confluence."""
        if not confluence_service.is_enabled():
            raise APIError("Confluence integration is not configured", status_code=400)
        
        # First generate Markdown documentation
        markdown_result = generate_markdown_documentation(json_data)
        
        if not markdown_result.get("success"):
            raise APIError("Failed to generate Markdown documentation", status_code=500)
        
        # Get the confluence master document
        confluence_master_path = Path(markdown_result["files"]["confluence_master"])
        
        try:
            # Read the master document content
            with open(confluence_master_path, 'r') as f:
                content = f.read()
            
            # Create the page title
            project_name = json_data.get("project_name", "API Documentation")
            title_suffix = json_data.get("title_suffix")
            title = f"{project_name} - Complete Documentation"
            if title_suffix:
                title = f"{title} - {title_suffix}"
            
            # Publish to Confluence
            result = confluence_service.create_or_update_page(
                title=title,
                content=content,
                parent_id=getattr(settings, 'CONFLUENCE_PARENT_PAGE_ID', None)
            )
            
            return {
                "success": True,
                "page_id": result.get('id'),
                "page_url": f"{settings.CONFLUENCE_URL}/wiki/spaces/{settings.CONFLUENCE_SPACE_KEY}/pages/{result.get('id')}",
                "markdown_files": markdown_result["files"]
            }
        except Exception as e:
            raise APIError(f"Failed to publish to Confluence: {str(e)}", status_code=500)
    
    return bp