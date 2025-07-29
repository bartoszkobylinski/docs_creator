"""
UML diagram generation endpoints.
"""

from pathlib import Path
from flask import send_file
from flask_smorest import Blueprint as SmorestBlueprint

from api.schemas import UMLGenerateRequestSchema
from api.exceptions import APIError
from services.uml_service import uml_service


def create_uml_blueprint() -> SmorestBlueprint:
    """Create UML blueprint."""
    
    bp = SmorestBlueprint(
        'uml', __name__, 
        url_prefix='/uml',
        description='UML diagram endpoints'
    )
    
    @bp.route('/', methods=['POST'])
    @bp.arguments(UMLGenerateRequestSchema)
    @bp.response(200)
    def generate_uml_diagrams(json_data):
        """Generate UML diagrams from documentation items."""
        items_data = json_data['items']
        config_name = json_data.get('config', 'overview')
        
        if not items_data:
            raise APIError("No items provided for UML generation", status_code=400)
        
        try:
            # Convert dictionary items back to DocItem objects
            from fastdoc.models import DocItem
            items = []
            for item_data in items_data:
                item = DocItem(**item_data)
                items.append(item)
            
            result = uml_service.generate_uml_diagrams(items, config_name)
            return result
        except Exception as e:
            raise APIError(f"UML generation failed: {str(e)}", status_code=500)
    
    @bp.route('/custom', methods=['POST'])
    @bp.arguments({'items': {'type': 'array', 'required': True}, 'config': {'type': 'object', 'required': True}})
    @bp.response(200)
    def generate_custom_uml_diagram(json_data):
        """Generate UML diagram with custom configuration."""
        items_data = json_data['items']
        custom_config = json_data['config']
        
        if not items_data:
            raise APIError("No items provided for UML generation", status_code=400)
        
        try:
            # Convert dictionary items back to DocItem objects
            from fastdoc.models import DocItem
            items = []
            for item_data in items_data:
                item = DocItem(**item_data)
                items.append(item)
            
            result = uml_service.generate_custom_diagram(items, custom_config)
            return result
        except Exception as e:
            raise APIError(f"Custom UML generation failed: {str(e)}", status_code=500)
    
    @bp.route('/configurations', methods=['GET'])
    @bp.response(200)
    def get_uml_configurations():
        """Get available UML diagram configurations."""
        return uml_service.get_available_configurations()
    
    @bp.route('/cache/<cache_key>', methods=['GET', 'HEAD'])  
    def get_cached_diagram(cache_key):
        """Serve cached UML diagram image."""
        print(f"Cache request for: {cache_key}")
        
        cached_file = uml_service.get_cached_diagram(cache_key)
        print(f"Cache file path: {cached_file}")
        
        if not cached_file:
            print(f"Cache file not found for key: {cache_key}")
            raise APIError("Diagram not found in cache", status_code=404)
        
        print(f"Cache file exists: {cached_file.exists()}")
        if cached_file.exists():
            print(f"Cache file size: {cached_file.stat().st_size}")
        
        # Determine media type based on file extension
        if cache_key.endswith('.svg'):
            media_type = "image/svg+xml"
        elif cache_key.endswith('.txt'):
            media_type = "text/plain"
        else:
            media_type = "image/png"
        
        print(f"Serving with media type: {media_type}")
        
        return send_file(
            cached_file,
            mimetype=media_type,
            as_attachment=False,
            download_name=cache_key,
            conditional=True,  # Enable caching
            max_age=3600  # Cache for 1 hour
        )
    
    return bp