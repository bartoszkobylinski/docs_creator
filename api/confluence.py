"""
Confluence API endpoints for publishing documentation.
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any
from services.confluence_service import confluence_service
from api.schemas import validate_request


def create_confluence_blueprint() -> Blueprint:
    """Create and configure the Confluence API blueprint."""
    
    confluence_bp = Blueprint('confluence', __name__, url_prefix='/confluence')
    
    @confluence_bp.route('/publish-uml', methods=['POST'])
    @validate_request({
        "type": "object",
        "properties": {
            "diagram_data": {
                "type": "object",
                "required": True
            },
            "title_suffix": {
                "type": "string",
                "required": False
            }
        },
        "required": ["diagram_data"]
    })
    def publish_uml_diagram():
        """
        Publish UML diagram to Confluence.
        
        Expected payload:
        {
            "diagram_data": {
                "success": true,
                "main_diagram": {...},
                "additional_diagrams": {...},
                "analysis": {...}
            },
            "title_suffix": "optional suffix"
        }
        """
        try:
            data = request.get_json()
            diagram_data = data.get('diagram_data')
            title_suffix = data.get('title_suffix')
            
            # Validate Confluence is enabled
            if not confluence_service.is_enabled():
                return jsonify({
                    "success": False,
                    "error": "Confluence integration is not configured. Please configure Confluence settings first."
                }), 400
            
            # Publish the UML diagram
            result = confluence_service.publish_uml_diagram(
                diagram_data=diagram_data,
                title_suffix=title_suffix
            )
            
            if result.get('success'):
                # Build the page URL
                page_id = result.get('page_id')
                if page_id:
                    from core.config import settings
                    page_url = f"{settings.CONFLUENCE_URL}/wiki/spaces/{settings.CONFLUENCE_SPACE_KEY}/pages/{page_id}"
                else:
                    # If page_id isn't available, try to use the URL from the result
                    page_url = result.get('url', '')
                    if page_url and not page_url.startswith('http'):
                        from core.config import settings
                        page_url = f"{settings.CONFLUENCE_URL}/wiki{page_url}"
                
                return jsonify({
                    "success": True,
                    "page_id": page_id,
                    "page_url": page_url,
                    "title": result.get('title', 'UML Diagram')
                })
            else:
                return jsonify({
                    "success": False,
                    "error": result.get('error', 'Failed to publish UML diagram')
                }), 500
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error publishing UML diagram: {str(e)}"
            }), 500
    
    @confluence_bp.route('/status', methods=['GET'])
    def check_confluence_status():
        """Check if Confluence integration is enabled and configured."""
        try:
            enabled = confluence_service.is_enabled()
            return jsonify({
                "enabled": enabled,
                "configured": enabled
            })
        except Exception as e:
            return jsonify({
                "enabled": False,
                "configured": False,
                "error": str(e)
            }), 500
    
    return confluence_bp