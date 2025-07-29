"""
Main application entry point for Flask Documentation Assistant.
"""

from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, url_for, flash, send_file
from flask_cors import CORS
import os

from core.config import settings
from api.endpoints import create_api_blueprint
from models.responses import HealthResult
from services.uml_service import uml_service
from services.report_service import report_service
from services.latex_service import latex_service
from services.markdown_service import markdown_service
from services.confluence_service import confluence_service
from services.docstring_service import docstring_service


def create_app() -> Flask:
    """Create and configure the Flask application."""
    
    # Initialize Flask app with default static folder
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='frontend'  # Use frontend as static folder
    )
    
    # Configure Flask
    app.config['DEBUG'] = settings.DEBUG
    app.config['SECRET_KEY'] = 'dev-secret-key'  # In production, use environment variable
    
    # Add CORS middleware
    CORS(app, origins=settings.CORS_ORIGINS)
    
    # Register API blueprint
    api_bp = create_api_blueprint()
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Frontend routes
    @app.route('/', methods=['GET', 'POST'])
    def index():
        """Serve the main interface with server-side rendering."""
        if request.method == 'POST':
            # Handle project scanning
            if 'scan_project' in request.form:
                project_path = request.form.get('project_path', '').strip()
                if project_path:
                    try:
                        # Call the scan service directly
                        from services.scanner_service import scanner_service
                        items_data, total_files, scan_time = scanner_service.scan_local_project(project_path)
                        
                        # Save to session or redirect to dashboard
                        flash(f'Successfully scanned {total_files} files!', 'success')
                        return redirect(url_for('serve_dashboard'))
                    except Exception as e:
                        flash(f'Scan failed: {str(e)}', 'error')
                else:
                    flash('Please enter a project path', 'error')
            
            # Handle Confluence settings
            elif 'save_confluence' in request.form:
                try:
                    result = confluence_service.save_and_test_settings(
                        url=request.form.get('confluence_url'),
                        username=request.form.get('confluence_username'),
                        token=request.form.get('confluence_token'),
                        space_key=request.form.get('confluence_space')
                    )
                    if result.get('success'):
                        flash('Confluence settings saved successfully!', 'success')
                    else:
                        flash(f'Failed to save settings: {result.get("error")}', 'error')
                except Exception as e:
                    flash(f'Error saving settings: {str(e)}', 'error')
        
        return render_template('index.html')
    
    @app.route('/dashboard', methods=['GET', 'POST'])
    def serve_dashboard():
        """Serve the dashboard interface with server-side rendering."""
        # Get report data
        items = report_service.get_report_data()
        
        # Calculate statistics
        total_items = len(items)
        documented_items = len([item for item in items if item.get('docstring') and item.get('docstring').strip()])
        coverage = round((documented_items / total_items * 100) if total_items > 0 else 0, 1)
        missing_docs = total_items - documented_items
        
        if request.method == 'POST':
            # Handle UML generation
            if 'generate_uml' in request.form:
                diagram_type = request.form.get('diagram_type', 'overview')
                return redirect(url_for('generate_uml_endpoint', diagram_type=diagram_type))
            
            # Handle PDF generation
            elif 'generate_pdf' in request.form:
                project_name = request.form.get('project_name', 'API_Documentation')
                include_uml = request.form.get('include_uml') == 'on'
                # Generate PDF and trigger download
                try:
                    result = latex_service.generate_pdf_documentation(
                        items, 
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
                        flash(f"PDF generation failed: {result.get('error', 'Unknown error')}", 'error')
                except Exception as e:
                    flash(f"PDF generation failed: {str(e)}", 'error')
            
            
            # Handle Markdown generation
            elif 'generate_markdown' in request.form:
                project_name = request.form.get('project_name', 'API_Documentation')
                include_uml = request.form.get('include_uml') == 'on'
                publish_confluence = request.form.get('publish_confluence') == 'on'
                
                try:
                    result = markdown_service.generate_markdown_documentation(
                        items,
                        project_name=project_name,
                        include_uml=include_uml
                    )
                    
                    if result.get('success'):
                        if publish_confluence:
                            confluence_result = confluence_service.publish_markdown_to_confluence(
                                result.get('master_content', ''),
                                project_name
                            )
                            if confluence_result.get('success'):
                                flash('Markdown generated and published to Confluence!', 'success')
                            else:
                                flash('Markdown generated but Confluence publishing failed', 'warning')
                        else:
                            flash('Markdown documentation generated successfully!', 'success')
                            # Trigger ZIP download
                            zip_path = markdown_service.create_markdown_zip(project_name)
                            if zip_path:
                                return send_file(
                                    zip_path,
                                    mimetype='application/zip',
                                    as_attachment=True,
                                    download_name=os.path.basename(zip_path)
                                )
                    else:
                        flash(f"Markdown generation failed: {result.get('error', 'Unknown error')}", 'error')
                except Exception as e:
                    flash(f"Markdown generation failed: {str(e)}", 'error')
        
        return render_template('dashboard_simple.html',
            items=items,
            total_items=total_items,
            documented_items=documented_items,
            coverage=coverage,
            missing_docs=missing_docs,
            has_data=total_items > 0,
            project_name="API_Documentation"
        )
    
    @app.route('/edit-docstring/<int:item_index>', methods=['GET', 'POST'])
    def edit_docstring(item_index):
        """Edit docstring for a specific item."""
        # Get current items
        items = report_service.get_report_data()
        
        if item_index < 0 or item_index >= len(items):
            flash('Invalid item index', 'error')
            return redirect(url_for('serve_dashboard'))
        
        item = items[item_index]
        generated_docstring = None
        
        if request.method == 'POST':
            # Handle save docstring
            if 'save_docstring' in request.form:
                try:
                    new_docstring = request.form.get('docstring', '').strip()
                    result = docstring_service.save_docstring(item, new_docstring)
                    
                    if result.get('success'):
                        flash('Docstring saved successfully!', 'success')
                        return redirect(url_for('serve_dashboard'))
                    else:
                        flash(f'Failed to save docstring: {result.get("message")}', 'error')
                        
                except Exception as e:
                    flash(f'Error saving docstring: {str(e)}', 'error')
            
            # Handle AI generation
            elif 'generate_ai_docstring' in request.form:
                try:
                    generated_docstring = docstring_service.generate_ai_docstring(item)
                    flash('AI docstring generated! Review and save if you like it.', 'success')
                except Exception as e:
                    flash(f'Error generating docstring: {str(e)}', 'error')
        
        return render_template('edit_docstring.html',
            item=item,
            item_index=item_index,
            generated_docstring=generated_docstring
        )
    
    # UML cache serving route
    @app.route('/api/uml/cache/<cache_key>', methods=['GET', 'HEAD'])
    def serve_uml_cache(cache_key):
        """Serve cached UML diagram images."""
        try:
            cached_file = uml_service.get_cached_diagram(cache_key)
            
            if not cached_file or not cached_file.exists():
                flash(f'UML diagram not found: {cache_key}', 'error')
                return "Diagram not found", 404
            
            # Determine media type based on file extension
            if cache_key.endswith('.svg'):
                media_type = "image/svg+xml"
            elif cache_key.endswith('.txt'):
                media_type = "text/plain"
            else:
                media_type = "image/png"
            
            return send_file(
                cached_file,
                mimetype=media_type,
                as_attachment=False,
                download_name=cache_key,
                conditional=True,
                max_age=3600  # Cache for 1 hour
            )
        except Exception as e:
            print(f"Error serving UML cache {cache_key}: {e}")
            return "Error serving diagram", 500
    
    # Static files are now handled by Flask's default static handling
    
    # UML page endpoints
    @app.route('/uml', methods=['GET', 'POST'])
    def uml_page():
        """Render and handle UML diagrams page."""
        if request.method == 'GET':
            show_source = request.args.get('show_source', False, type=bool)
            
            # Check if we have data available
            try:
                data = report_service.get_report_data()
                has_data = data and len(data) > 0
            except:
                has_data = False
            
            return render_template("uml.html", 
                has_data=has_data,
                show_source=show_source,
                selected_config="overview",
                result=None
            )
        
        # POST request - generate UML
        config = request.form.get('config', 'overview')
        show_source = request.form.get('show_source', False, type=bool)
        
        try:
            # Get current data
            items_data = report_service.get_report_data()
            if not items_data or len(items_data) == 0:
                return render_template("uml.html",
                    has_data=False,
                    show_source=show_source,
                    selected_config=config,
                    result=None
                )
            
            # Convert dictionary items back to DocItem objects
            from fastdoc.models import DocItem
            items = []
            for item_data in items_data:
                item = DocItem(**item_data)
                items.append(item)
            
            # Generate UML diagrams
            result = uml_service.generate_uml_diagrams(items, config)
            
            return render_template("uml.html",
                has_data=True,
                show_source=show_source,
                selected_config=config,
                result=result
            )
            
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            return render_template("uml.html",
                has_data=True,
                show_source=show_source,
                selected_config=config,
                result=error_result
            )
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "version": settings.VERSION})
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME}...")
    print(f"Frontend will be available at: http://{settings.HOST}:{settings.PORT}")
    print(f"Dashboard will be available at: http://{settings.HOST}:{settings.PORT}/dashboard")
    
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    )