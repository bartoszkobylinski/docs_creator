"""
Modern Flask API with proper structure and validation.
"""

from flask import Blueprint, jsonify

from api.exceptions import register_error_handlers
from api.reports import create_reports_blueprint
from api.scanning import create_scanning_blueprint
from api.docstrings import create_docstrings_blueprint
from api.confluence import create_confluence_blueprint
# from api.docs import create_docs_blueprint  # TODO: Fix docs module


def create_api_blueprint() -> Blueprint:
    """Create and configure the main API blueprint with sub-blueprints."""
    
    # Create main API blueprint
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    
    # Create sub-blueprints
    reports_bp = create_reports_blueprint()
    scanning_bp = create_scanning_blueprint()
    docstrings_bp = create_docstrings_blueprint()
    confluence_bp = create_confluence_blueprint()
    # docs_bp = create_docs_blueprint()  # TODO: Fix docs module
    
    # Register error handlers
    register_error_handlers(api_bp)
    
    # Register sub-blueprints
    api_bp.register_blueprint(reports_bp)
    api_bp.register_blueprint(scanning_bp)
    api_bp.register_blueprint(docstrings_bp)
    api_bp.register_blueprint(confluence_bp)
    # api_bp.register_blueprint(docs_bp)  # TODO: Fix docs module
    
    @api_bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy", 
            "version": "1.0.0",
            "service": "Flask Documentation Assistant"
        })
    
    return api_bp