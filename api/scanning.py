"""
Scanning API endpoints.
"""

import os
from flask import Blueprint, request, jsonify

from api.exceptions import APIError
from services.scanner_service import scanner_service


def create_scanning_blueprint() -> Blueprint:
    """Create scanning blueprint."""
    
    bp = Blueprint('scanning', __name__, url_prefix='/scan')
    
    @bp.route('/upload', methods=['POST'])
    def scan_uploaded_files():
        """Scan uploaded Python files."""
        project_path = request.form.get('project_path')
        files = request.files.getlist('files')
        
        if not project_path:
            raise APIError("project_path is required", status_code=400)
        
        if not files:
            raise APIError("No files provided", status_code=400)
        
        try:
            items_data, total_files, scan_time = scanner_service.scan_uploaded_files(
                project_path, files
            )
            
            return jsonify({
                "success": True,
                "message": f"Successfully scanned {total_files} files",
                "items": items_data,
                "total_files": total_files,
                "scan_time": scan_time
            }), 201
            
        except Exception as e:
            raise APIError(f"Scan failed: {str(e)}", status_code=500)
    
    @bp.route('/local', methods=['POST'])
    def scan_local_project():
        """Scan a local project directory."""
        data = request.get_json()
        if not data:
            raise APIError("Request body is required", status_code=400)
            
        project_path = data.get('project_path')
        if not project_path:
            raise APIError("project_path is required", status_code=400)
        
        if not os.path.exists(project_path):
            raise APIError(f"Path does not exist: {project_path}", status_code=400)
        
        try:
            items_data, total_files, scan_time = scanner_service.scan_local_project(project_path)
            
            return jsonify({
                "success": True,
                "message": f"Successfully scanned {total_files} files from {project_path}",
                "items": items_data,
                "total_files": total_files,
                "scan_time": scan_time
            }), 201
            
        except Exception as e:
            raise APIError(f"Local scan failed: {str(e)}", status_code=500)
    
    @bp.route('/files', methods=['GET'])
    def get_project_files():
        """Get list of Python files in the current project."""
        try:
            files = scanner_service.get_project_files()
            return jsonify({"files": files})
        except Exception as e:
            raise APIError(f"Failed to get project files: {str(e)}", status_code=500)
    
    return bp