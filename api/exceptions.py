"""
API exceptions and error handling.
"""

from flask import jsonify
from marshmallow import ValidationError


class APIError(Exception):
    """Custom API exception."""
    
    def __init__(self, message, status_code=500, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload


def register_error_handlers(bp):
    """Register error handlers for the blueprint."""
    
    @bp.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors."""
        response = {
            'error': error.message,
            'status_code': error.status_code
        }
        if error.payload:
            response.update(error.payload)
        return jsonify(response), error.status_code
    
    @bp.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle Marshmallow validation errors."""
        return jsonify({
            'error': 'Validation failed',
            'message': error.messages,
            'status_code': 400
        }), 400
    
    @bp.errorhandler(ValueError)
    def handle_value_error(error):
        """Handle value errors as bad requests."""
        return jsonify({
            'error': 'Invalid input',
            'message': str(error),
            'status_code': 400
        }), 400
    
    @bp.errorhandler(FileNotFoundError)
    def handle_file_not_found(error):
        """Handle file not found errors."""
        return jsonify({
            'error': 'Resource not found',
            'message': str(error),
            'status_code': 404
        }), 404
    
    @bp.errorhandler(Exception)
    def handle_generic_error(error):
        """Handle unexpected errors."""
        return jsonify({
            'error': 'Internal server error',
            'message': str(error),
            'status_code': 500
        }), 500