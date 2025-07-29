"""
Documentation generation API endpoints.
"""

from flask_smorest import Blueprint as SmorestBlueprint
from .latex import create_latex_blueprint
from .markdown import create_markdown_blueprint
from .uml import create_uml_blueprint


def create_docs_blueprint() -> SmorestBlueprint:
    """Create main docs blueprint."""
    
    bp = SmorestBlueprint(
        'docs', __name__, 
        url_prefix='/api/docs',
        description='Documentation generation endpoints'
    )
    
    # Register sub-blueprints
    latex_bp = create_latex_blueprint()
    markdown_bp = create_markdown_blueprint()
    uml_bp = create_uml_blueprint()
    
    bp.register_blueprint(latex_bp)
    bp.register_blueprint(markdown_bp)
    bp.register_blueprint(uml_bp)
    
    return bp