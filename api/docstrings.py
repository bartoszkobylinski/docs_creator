"""
Docstring management API endpoints.
"""

from flask import Blueprint, request, jsonify

from api.exceptions import APIError
from services.docstring_service import docstring_service


def create_docstrings_blueprint() -> Blueprint:
    """Create docstrings blueprint."""
    
    bp = Blueprint('docstrings', __name__, url_prefix='/docstrings')
    
    @bp.route('/', methods=['POST'])
    def save_docstring():
        """Save a docstring to the source file."""
        data = request.get_json()
        if not data:
            raise APIError("Request body is required", status_code=400)
            
        item = data.get('item')
        docstring = data.get('docstring')
        
        if not item:
            raise APIError("item is required", status_code=400)
        if docstring is None:
            raise APIError("docstring is required", status_code=400)
            
        try:
            result = docstring_service.save_docstring(item, docstring)
            return jsonify(result), 201
            
        except Exception as e:
            raise APIError(f"Failed to save docstring: {str(e)}", status_code=500)
    
    @bp.route('/generate', methods=['POST'])
    def generate_docstring():
        """Generate a docstring using AI or template."""
        data = request.get_json()
        if not data:
            raise APIError("Request body is required", status_code=400)
            
        item = data.get('item')
        if not item:
            raise APIError("item is required", status_code=400)
            
        try:
            docstring = docstring_service.generate_ai_docstring(item)
            return jsonify({"docstring": docstring})
            
        except Exception as e:
            raise APIError(f"Failed to generate docstring: {str(e)}", status_code=500)
    
    return bp