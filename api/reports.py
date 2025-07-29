"""
Reports API endpoints.
"""

from flask import Blueprint, jsonify

from services.report_service import report_service
from api.exceptions import APIError


def create_reports_blueprint() -> Blueprint:
    """Create reports blueprint."""
    
    bp = Blueprint('reports', __name__, url_prefix='/reports')
    
    @bp.route('/status', methods=['GET'])
    def get_report_status():
        """Get current report status."""
        try:
            status_data = report_service.get_report_status()
            return jsonify(status_data)
        except Exception as e:
            raise APIError(f"Failed to get report status: {str(e)}", status_code=500)
    
    @bp.route('/', methods=['GET'])
    def get_reports():
        """Get all report data."""
        try:
            data = report_service.get_report_data()
            return jsonify(data)
        except Exception as e:
            raise APIError(f"Failed to get report data: {str(e)}", status_code=500)
    
    @bp.route('/current', methods=['GET'])
    def get_current_report():
        """Get current scan data (alias for /reports)."""
        try:
            data = report_service.get_report_data()
            return jsonify(data)
        except Exception as e:
            raise APIError(f"Failed to get current data: {str(e)}", status_code=500)
    
    return bp