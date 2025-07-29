"""
API endpoints for the Flask Documentation Assistant.
"""

import os
from pathlib import Path
from typing import List, Optional

from flask import Blueprint, request, jsonify, send_file
from werkzeug.exceptions import BadRequest

from models.requests import DocstringRequest, GenerateRequest
from models.responses import (
    ReportStatus, ScanResult, DocstringSaveResult, 
    GenerateResult, ProjectFilesResult
)
from core.config import settings
from services.scanner_service import scanner_service
from services.docstring_service import docstring_service
from services.report_service import report_service
from services.confluence_service import confluence_service
from services.coverage_tracker import coverage_tracker
from services.uml_service import uml_service
from services.latex_service import latex_service
from services.markdown_service import markdown_service


def create_api_blueprint() -> Blueprint:
    """Create and configure the API blueprint."""
    
    bp = Blueprint('api', __name__)
    
    @bp.route("/report/status", methods=['GET'])
    def get_report_status():
        """Check if a report file exists and return basic info."""
        status_data = report_service.get_report_status()
        return jsonify(status_data)
    
    @bp.route("/report/data", methods=['GET'])
    def get_report_data():
        """Return the full report data."""
        return jsonify(report_service.get_report_data())
    
    @bp.route("/current-data", methods=['GET'])
    def get_current_data():
        """Return current scan data for dashboard."""
        return jsonify(report_service.get_report_data())
    
    @bp.route("/scan", methods=['POST'])
    def scan_project():
        """Scan uploaded Python files and generate documentation report."""
        try:
            project_path = request.form.get('project_path')
            files = request.files.getlist('files')
            
            if not project_path:
                return jsonify({"error": "project_path is required"}), 400
            
            if not files:
                return jsonify({"error": "files are required"}), 400
            
            items_data, total_files, scan_time = scanner_service.scan_uploaded_files(
                project_path, files
            )
            
            result = {
                "success": True,
                "message": f"Successfully scanned {total_files} files",
                "items": items_data,
                "total_files": total_files,
                "scan_time": scan_time
            }
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @bp.route("/docstring/save", methods=['POST'])
    def save_docstring():
        """Save a docstring to the source file."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400
            
            # Convert dict to DocstringRequest
            docstring_request = DocstringRequest(**data)
            result = docstring_service.save_docstring(docstring_request.item, docstring_request.docstring)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @bp.route("/docstring/generate", methods=['POST'])
    def generate_docstring():
        """Generate a docstring using AI or template."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400
            
            # Convert dict to GenerateRequest
            generate_request = GenerateRequest(**data)
            docstring = docstring_service.generate_ai_docstring(generate_request.item)
            return jsonify({"docstring": docstring})
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @bp.route("/project/files", methods=['GET'])
    def get_project_files():
        """Get list of Python files in the current project."""
        try:
            files = scanner_service.get_project_files()
            return jsonify({"files": files})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @bp.route("/scan-local", methods=['POST'])
    def scan_local_project():
        """Scan a local project path using the CLI scanner."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400
            
            project_path = data.get("project_path")
            
            if not project_path:
                return jsonify({"error": "project_path is required"}), 400
            
            if not os.path.exists(project_path):
                return jsonify({"error": f"Path does not exist: {project_path}"}), 400
            
            items_data, total_files, scan_time = scanner_service.scan_local_project(project_path)
            
            result = {
                "success": True,
                "message": f"Successfully scanned {total_files} files from {project_path}",
                "items": items_data,
                "total_files": total_files,
                "scan_time": scan_time
            }
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # UML Generation Endpoints
    @bp.route("/docs/uml/generate", methods=['POST'])
    def generate_uml():
        """Generate UML diagram based on current report data."""
        try:
            diagram_type = request.args.get('diagram_type', 'overview')
            
            # Get current data
            data = report_service.get_report_data()
            if not data or not data.get("items"):
                return jsonify({"error": "No scan data available. Please scan a project first."}), 400
            
            # Convert dictionary items back to DocItem objects
            from fastdoc.models import DocItem
            items = []
            for item_data in data["items"]:
                item = DocItem(**item_data)
                items.append(item)
            
            # Generate UML diagram
            result = uml_service.generate_uml_diagrams(items, diagram_type)
            
            if result.get('success') and result.get('image_path'):
                return send_file(result['image_path'], mimetype='image/png')
            else:
                return jsonify({"error": result.get('error', 'Failed to generate UML diagram')}), 500
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # LaTeX/PDF Generation Endpoints
    @bp.route("/docs/latex/generate", methods=['POST'])
    def generate_latex():
        """Generate LaTeX/PDF documentation."""
        try:
            data = request.get_json()
            project_name = data.get('project_name', 'API_Documentation') if data else 'API_Documentation'
            include_uml = data.get('include_uml', True) if data else True
            
            # Get current report data
            report_data = report_service.get_report_data()
            if not report_data or not report_data.get("items"):
                return jsonify({"error": "No scan data available. Please scan a project first."}), 400
            
            # Generate PDF
            result = latex_service.generate_pdf_documentation(
                report_data["items"], 
                project_name=project_name,
                include_uml=include_uml
            )
            
            if result.get('success') and result.get('pdf_path'):
                return send_file(
                    result['pdf_path'],
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"{project_name.replace(' ', '_')}_documentation.pdf"
                )
            else:
                return jsonify({"error": result.get('error', 'Failed to generate PDF')}), 500
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Markdown Generation Endpoints
    @bp.route("/docs/markdown/generate", methods=['POST'])
    def generate_markdown():
        """Generate Markdown documentation."""
        try:
            data = request.get_json()
            project_name = data.get('project_name', 'API_Documentation') if data else 'API_Documentation'
            include_uml = data.get('include_uml', True) if data else True
            publish_to_confluence = data.get('publish_to_confluence', False) if data else False
            
            # Get current report data
            report_data = report_service.get_report_data()
            if not report_data or not report_data.get("items"):
                return jsonify({"error": "No scan data available. Please scan a project first."}), 400
            
            # Generate Markdown documentation
            result = markdown_service.generate_markdown_documentation(
                report_data["items"],
                project_name=project_name,
                include_uml=include_uml
            )
            
            if not result.get('success'):
                return jsonify({"error": result.get('error', 'Failed to generate Markdown')}), 500
            
            # Publish to Confluence if requested
            if publish_to_confluence:
                try:
                    confluence_result = confluence_service.publish_markdown_to_confluence(
                        result.get('master_content', ''),
                        project_name
                    )
                    if not confluence_result.get('success'):
                        return jsonify({
                            "error": f"Markdown generated but Confluence publishing failed: {confluence_result.get('error')}"
                        }), 500
                except Exception as e:
                    return jsonify({
                        "error": f"Markdown generated but Confluence publishing failed: {str(e)}"
                    }), 500
            
            return jsonify({
                "success": True,
                "message": "Markdown documentation generated successfully",
                "files_generated": result.get('files_generated', []),
                "confluence_published": publish_to_confluence
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @bp.route("/docs/markdown/download", methods=['GET'])
    def download_markdown_documentation():
        """Download generated Markdown documentation as ZIP."""
        try:
            project_name = request.args.get('project_name', 'API_Documentation')
            
            # Generate ZIP file
            zip_path = markdown_service.create_markdown_zip(project_name)
            
            if not zip_path or not os.path.exists(zip_path):
                return jsonify({"error": "No Markdown files found to download"}), 404
            
            return send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name=os.path.basename(zip_path)
            )
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Confluence Endpoints
    @bp.route("/confluence/save-settings", methods=['POST'])
    def save_confluence_settings():
        """Save Confluence settings for runtime configuration."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400
            
            required_fields = ['url', 'username', 'token', 'space_key']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({"error": f"{field} is required"}), 400
            
            # Save settings and test connection
            result = confluence_service.save_and_test_settings(
                url=data['url'],
                username=data['username'],
                token=data['token'],
                space_key=data['space_key']
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return bp