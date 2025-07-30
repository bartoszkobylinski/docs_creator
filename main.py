"""
Main application entry point for Flask Documentation Assistant.
"""

from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, url_for, flash, send_file, session
from flask_cors import CORS
import os
import json

from core.config import settings
from api.endpoints import create_api_blueprint
from models.responses import HealthResult
from services.uml_service import uml_service
from services.report_service import report_service
from services.latex_service import latex_service
from services.markdown_service import markdown_service
from services.confluence_service import confluence_service
from services.docstring_service import docstring_service
from services.scanner_service import scanner_service
from services.business_service import business_service
from services.openai_service import openai_service
from services.cost_tracking_service import cost_tracking_service

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def create_app() -> Flask:
    """Create and configure the Flask application."""
    
    # Initialize Flask app with default static folder
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='frontend'  # Use frontend as static folder
    )
    
    # In demo mode, clear any existing report data on startup
    if os.environ.get('DEMO_MODE') == 'true':
        try:
            # Clear the report file to start fresh
            if os.path.exists(settings.report_file_path):
                with open(settings.report_file_path, 'w') as f:
                    json.dump([], f)
            print("Demo mode: Cleared existing report data")
        except Exception as e:
            print(f"Warning: Could not clear report data: {e}")
    
    # Configure Flask
    app.config['DEBUG'] = settings.DEBUG
    app.config['SECRET_KEY'] = 'dev-secret-key'  # In production, use environment variable
    
    # Add CORS middleware
    CORS(app, origins=settings.CORS_ORIGINS)
    
    # Register API blueprint
    api_bp = create_api_blueprint()
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Demo login functionality
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Demo login page."""
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            # Simple demo credentials check
            if username == 'demo' and password == 'demo123':
                session['demo_authenticated'] = True
                flash('🎉 Welcome to the Docs Creator demo!', 'success')
                return redirect(url_for('index'))
            else:
                flash('❌ Invalid credentials. Please use: demo / demo123', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """Logout from demo."""
        session.pop('demo_authenticated', None)
        flash('👋 You have been logged out of the demo.', 'success')
        return redirect(url_for('login'))
    
    def require_demo_auth():
        """Check if user is authenticated for demo."""
        return session.get('demo_authenticated', False)
    
    # Frontend routes
    @app.route('/', methods=['GET', 'POST'])
    def index():
        """Serve the main interface with server-side rendering."""
        # Check demo authentication
        if not require_demo_auth():
            return redirect(url_for('login'))
            
        if request.method == 'POST':
            # Handle project scanning
            if 'scan_project' in request.form:
                project_path = request.form.get('project_path', '').strip()
                
                # In demo mode, always use the demo project
                if os.environ.get('DEMO_MODE') == 'true' or project_path == 'demo':
                    project_path = '/app/demo_sample_project'
                    flash('🔍 Scanning e-commerce sample project...', 'info')
                
                if project_path:
                    try:
                        # Reset cost tracking for new project
                        cost_tracking_service.set_current_project(project_path, reset_costs=True)
                        
                        # Call the scan service directly
                        from services.scanner_service import scanner_service
                        items_data, total_files, scan_time = scanner_service.scan_local_project(project_path)
                        
                        # Save to session or redirect to dashboard
                        flash(f'Successfully scanned {total_files} files! Cost tracking reset for new project.', 'success')
                        return redirect(url_for('serve_dashboard'))
                    except Exception as e:
                        flash(f'Scan failed: {str(e)}', 'error')
                else:
                    flash('Please enter a project path', 'error')
            
            # Handle Business Overview
            elif 'save_business_overview' in request.form:
                try:
                    result = business_service.save_business_overview(
                        project_purpose=request.form.get('project_purpose', ''),
                        business_context=request.form.get('business_context', ''),
                        key_business_value=request.form.get('key_business_value', '')
                    )
                    if result.get('success'):
                        flash('Business overview saved successfully!', 'success')
                    else:
                        flash(f'Failed to save business overview: {result.get("error")}', 'error')
                except Exception as e:
                    flash(f'Error saving business overview: {str(e)}', 'error')
            
            # Handle OpenAI Settings
            elif 'save_openai' in request.form:
                try:
                    result = openai_service.save_settings(
                        api_key=request.form.get('openai_api_key', ''),
                        model=request.form.get('openai_model', 'gpt-4.1-nano'),
                        max_tokens=int(request.form.get('max_tokens', 400)),
                        temperature=0.1
                    )
                    if result.get('success'):
                        flash('OpenAI settings saved successfully!', 'success')
                    else:
                        flash(f'Failed to save OpenAI settings: {result.get("message")}', 'error')
                except Exception as e:
                    flash(f'Error saving OpenAI settings: {str(e)}', 'error')
            
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
        
        # Check for existing project data
        existing_data = report_service.get_report_data()
        
        # In demo mode, filter out non-demo data
        if os.environ.get('DEMO_MODE') == 'true':
            existing_data = [item for item in existing_data 
                           if item.get('file_path', '').startswith('/app/demo_sample_project')]
        
        has_existing_data = len(existing_data) > 0
        
        # Show demo mode message if no demo data exists
        if os.environ.get('DEMO_MODE') == 'true' and not has_existing_data:
            flash('👋 Welcome to Docs Creator Demo! Click "Scan E-commerce Sample Project" below to get started.', 'info')
        
        if has_existing_data:
            # Calculate basic stats for existing data
            total_items = len(existing_data)
            documented_items = len([item for item in existing_data if item.get('docstring') and item.get('docstring').strip()])
            coverage = round((documented_items / total_items * 100) if total_items > 0 else 0, 1)
            
            # Try to get the project path from the first item
            project_path = ""
            if existing_data:
                first_item = existing_data[0]
                file_path = first_item.get('file_path', '')
                if file_path:
                    # Extract project path by removing file-specific parts
                    project_path = os.path.dirname(file_path)
                    # Find common parent directory
                    while project_path and not os.path.exists(os.path.join(project_path, 'main.py')):
                        parent = os.path.dirname(project_path)
                        if parent == project_path:  # reached root
                            break
                        project_path = parent
        else:
            total_items = documented_items = coverage = 0
            project_path = ""
        
        # Get business overview data
        business_overview = business_service.get_business_overview()
        
        # Get OpenAI settings and cost stats
        openai_settings = openai_service.get_settings()
        cost_stats = cost_tracking_service.get_cost_stats()
        
        return render_template('index.html', 
            has_existing_data=has_existing_data,
            total_items=total_items,
            documented_items=documented_items,
            coverage=coverage,
            project_path=project_path,
            business_overview=business_overview,
            openai_settings=openai_settings,
            cost_stats=cost_stats
        )
    
    @app.route('/dashboard', methods=['GET', 'POST'])
    def serve_dashboard():
        """Serve the dashboard interface with server-side rendering."""
        # Check demo authentication
        if not require_demo_auth():
            return redirect(url_for('login'))
            
        # Get report data
        all_items = report_service.get_report_data()
        
        # In demo mode, filter out non-demo data
        if os.environ.get('DEMO_MODE') == 'true':
            all_items = [item for item in all_items 
                        if item.get('file_path', '').startswith('/app/demo_sample_project')]
        
        # Set current project for cost tracking based on existing data
        if all_items:
            first_item = all_items[0]
            file_path = first_item.get('file_path', '')
            if file_path:
                # Extract project path by finding the project root
                project_path = os.path.dirname(file_path)
                while project_path and project_path != '/' and not any(
                    os.path.exists(os.path.join(project_path, marker)) 
                    for marker in ['pyproject.toml', 'requirements.txt', 'setup.py', '.git']
                ):
                    project_path = os.path.dirname(project_path)
                
                if project_path and project_path != '/':
                    # Set current project without resetting costs (we just want to track for this project)
                    cost_tracking_service.set_current_project(project_path, reset_costs=False)
        
        # Scanner now properly skips non-documentable items, so no filtering needed
        items = all_items
        
        # Calculate statistics with improved docstring detection
        def has_actual_docstring(item):
            """Check if item actually has a docstring, including from source file."""
            # First check the stored docstring
            stored_docstring = item.get('docstring')
            if stored_docstring and stored_docstring.strip():
                return True
            
            # If no stored docstring, try to detect from source
            full_source = item.get('full_source', '')
            if full_source:
                # Simple check for triple quotes in source
                lines = full_source.split('\n')
                for i, line in enumerate(lines):
                    if i == 0:  # Skip the function/class definition line
                        continue
                    stripped = line.strip()
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        return True
                    elif stripped and not stripped.startswith('#'):
                        # Hit non-comment code before docstring
                        break
            return False
        
        total_items = len(items)
        documented_items = len([item for item in items if has_actual_docstring(item)])
        coverage = round((documented_items / total_items * 100) if total_items > 0 else 0, 1)
        missing_docs = total_items - documented_items
        
        if request.method == 'POST':
            # Handle UML generation
            if 'generate_uml' in request.form:
                diagram_type = request.form.get('diagram_type', 'overview')
                return redirect(url_for('uml_page', config=diagram_type))
            
            # Handle PDF generation
            elif 'generate_pdf' in request.form:
                project_name = request.form.get('project_name', 'API_Documentation')
                pdf_filename = request.form.get('pdf_filename', f"{project_name}_documentation")
                include_uml = request.form.get('include_uml') == 'on'
                # Generate PDF and trigger download
                try:
                    # Generate UML diagrams if requested
                    uml_diagrams = None
                    if include_uml:
                        try:
                            from fastdoc.models import DocItem
                            doc_items = []
                            for item_data in items:
                                item = DocItem(**item_data)
                                doc_items.append(item)
                            uml_result = uml_service.generate_uml_diagrams(doc_items, "overview")
                            if uml_result.get("success"):
                                uml_diagrams = uml_result
                        except Exception as e:
                            print(f"UML generation failed: {e}")
                    
                    # Convert items to DocItem objects
                    from fastdoc.models import DocItem
                    doc_items = []
                    for item_data in items:
                        item = DocItem(**item_data)
                        doc_items.append(item)
                    
                    result = latex_service.generate_complete_documentation(
                        doc_items=doc_items,
                        project_name=project_name,
                        uml_diagrams=uml_diagrams
                    )
                    if result.get('success') and result.get('pdf_file'):
                        # Clean filename to remove special characters
                        clean_filename = "".join(c for c in pdf_filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        clean_filename = clean_filename.replace(' ', '_')
                        if not clean_filename:
                            clean_filename = "documentation"
                        
                        return send_file(
                            result['pdf_file'],
                            mimetype='application/pdf',
                            as_attachment=True,
                            download_name=f"{clean_filename}.pdf"
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
                    # Generate UML data if requested
                    uml_data = None
                    if include_uml:
                        try:
                            from fastdoc.models import DocItem
                            doc_items = []
                            for item_data in items:
                                item = DocItem(**item_data)
                                doc_items.append(item)
                            uml_result = uml_service.generate_uml_diagrams(doc_items, "overview")
                            if uml_result.get("success"):
                                uml_data = uml_result
                        except Exception as e:
                            print(f"UML generation failed: {e}")
                    
                    # Convert items to DocItem objects
                    from fastdoc.models import DocItem
                    doc_items = []
                    for item_data in items:
                        item = DocItem(**item_data)
                        doc_items.append(item)
                    
                    if publish_confluence:
                        # For Confluence, just generate content without ZIP
                        result = markdown_service.generate_documentation(
                            items=doc_items,
                            project_name=project_name,
                            include_uml=include_uml,
                            uml_data=uml_data
                        )
                        
                        if result.get('success'):
                            confluence_content = result.get('files', {}).get('confluence_master', '')
                            confluence_result = confluence_service.publish_markdown_to_confluence(
                                confluence_content,
                                project_name
                            )
                            if confluence_result.get('success'):
                                page_url = confluence_result.get('page_url', '')
                                if page_url:
                                    # Create full URL if it's a relative path
                                    if page_url.startswith('/'):
                                        full_url = f"{settings.CONFLUENCE_URL}/wiki{page_url}"
                                    else:
                                        full_url = page_url
                                    
                                    flash(f'Markdown generated and published to Confluence! <a href="{full_url}" target="_blank" style="color: #0066cc; text-decoration: underline;">View page</a>', 'success')
                                else:
                                    flash('Markdown generated and published to Confluence!', 'success')
                            else:
                                error_msg = confluence_result.get('error', 'Unknown error')
                                flash(f'Markdown generated but Confluence publishing failed: {error_msg}', 'warning')
                        else:
                            flash(f"Markdown generation failed: {result.get('error', 'Unknown error')}", 'error')
                    else:
                        # For regular download, create ZIP file
                        result = markdown_service.create_documentation_zip(
                            items=doc_items,
                            project_name=project_name,
                            include_uml=include_uml,
                            uml_data=uml_data
                        )
                        
                        if result.get('success') and result.get('zip_path'):
                            return send_file(
                                result['zip_path'],
                                mimetype='application/zip',
                                as_attachment=True,
                                download_name=result.get('zip_filename', f"{project_name}_docs.zip")
                            )
                        else:
                            flash(f"Markdown generation failed: {result.get('error', 'Unknown error')}", 'error')
                except Exception as e:
                    flash(f"Markdown generation failed: {str(e)}", 'error')
        
        # Get cost stats for dashboard
        cost_stats = cost_tracking_service.get_cost_stats()
        
        return render_template('dashboard_simple.html',
            items=items,
            total_items=total_items,
            documented_items=documented_items,
            coverage=coverage,
            missing_docs=missing_docs,
            has_data=total_items > 0,
            project_name="API_Documentation",
            cost_stats=cost_stats
        )
    
    @app.route('/edit-docstring/<int:item_index>', methods=['GET', 'POST'])
    def edit_docstring(item_index):
        """Edit docstring for a specific item."""
        # Check demo authentication
        if not require_demo_auth():
            return redirect(url_for('login'))
            
        # Get current items
        items = report_service.get_report_data()
        
        # In demo mode, filter out non-demo data
        if os.environ.get('DEMO_MODE') == 'true':
            items = [item for item in items 
                    if item.get('file_path', '').startswith('/app/demo_sample_project')]
        
        if item_index < 0 or item_index >= len(items):
            flash('Invalid item index', 'error')
            return redirect(url_for('serve_dashboard'))
        
        item = items[item_index]
        print(f"DEBUG: Editing item {item_index}: {item.get('qualname')} at line {item.get('lineno')} in {item.get('file_path')}")
        generated_docstring = None
        
        if request.method == 'POST':
            # Handle save docstring
            if 'save_docstring' in request.form:
                try:
                    new_docstring = request.form.get('docstring', '').strip()
                    result = docstring_service.save_docstring(item, new_docstring)
                    
                    if result.get('success'):
                        flash('Docstring saved successfully! Re-scanning project to update line numbers...', 'success')
                        
                        # Automatically re-scan the project to update line numbers
                        try:
                            # Get the project path from the item's file path
                            file_path = item.get('file_path', '')
                            if file_path:
                                # Extract project root from file path (go up to find the project root)
                                import os
                                project_path = os.path.dirname(file_path)
                                while project_path and project_path != '/' and not any(
                                    os.path.exists(os.path.join(project_path, marker)) 
                                    for marker in ['pyproject.toml', 'requirements.txt', 'setup.py', '.git']
                                ):
                                    project_path = os.path.dirname(project_path)
                                
                                if project_path and project_path != '/':
                                    print(f"Re-scanning project at: {project_path}")
                                    scanner_service.scan_local_project(project_path)
                                    flash('Project re-scanned successfully!', 'success')
                                else:
                                    flash('Docstring saved, but could not auto-detect project path for re-scanning. Please manually re-scan if needed.', 'warning')
                            else:
                                flash('Docstring saved, but could not determine project path for re-scanning. Please manually re-scan if needed.', 'warning')
                                
                        except Exception as scan_error:
                            print(f"Auto re-scan failed: {scan_error}")
                            flash('Docstring saved, but auto re-scan failed. Please manually re-scan the project.', 'warning')
                        
                        return redirect(url_for('serve_dashboard'))
                    else:
                        flash(f'Failed to save docstring: {result.get("message")}', 'error')
                        
                except Exception as e:
                    flash(f'Error saving docstring: {str(e)}', 'error')
            
            # Handle AI generation
            elif 'generate_ai_docstring' in request.form:
                try:
                    generated_docstring, used_ai, cost_info = docstring_service.generate_ai_docstring(item)
                    if used_ai:
                        if cost_info.get('success'):
                            cost_display = cost_info.get('formatted_cost', '$0.00')
                            tokens_used = cost_info.get('tokens_used', 0)
                            flash(f'🤖 AI docstring generated! Cost: {cost_display} ({tokens_used} tokens). Review and save if you like it.', 'success')
                        else:
                            flash('🤖 AI docstring generated! Review and save if you like it.', 'success')
                    else:
                        flash('⚠️ AI not available (check OpenAI API key). Generated template instead.', 'warning')
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
    
    # UML Confluence publishing route
    @app.route('/api/confluence/publish-uml', methods=['POST'])
    def publish_uml_to_confluence():
        """Publish UML diagram to Confluence."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            diagram_data = data.get('diagram_data')
            title_suffix = data.get('title_suffix', '')
            
            if not diagram_data or not diagram_data.get('success'):
                return jsonify({"error": "Invalid diagram data"}), 400
            
            # Generate title with project name
            items = report_service.get_report_data()
            project_name = "API_Documentation"  # Default name
            if items:
                # Try to get project name from first item's file path
                first_item = items[0]
                if 'file_path' in first_item:
                    import os
                    project_name = os.path.basename(os.path.dirname(first_item['file_path']))
            
            title = f"{project_name} - UML Diagram"
            if title_suffix:
                title += f" ({title_suffix})"
            
            # Create Confluence content with diagram
            confluence_content = f"""
<h1>{title}</h1>

<h2>UML Diagram Analysis</h2>
"""
            
            if diagram_data.get('analysis'):
                analysis = diagram_data['analysis']
                confluence_content += f"""
<ul>
<li>Classes found: {analysis.get('classes_found', 0)}</li>
<li>Relationships found: {analysis.get('relationships_found', 0)}</li>
<li>Packages: {', '.join(analysis.get('packages', []))}</li>
</ul>
"""
            
            # Add main diagram
            if diagram_data.get('main_diagram') and diagram_data['main_diagram'].get('url'):
                diagram_url = diagram_data['main_diagram']['url']
                # Convert relative URL to absolute
                if diagram_url.startswith('/'):
                    diagram_url = f"http://{request.host}{diagram_url}"
                
                confluence_content += f"""
<h2>Main Diagram</h2>
<p><img src="{diagram_url}" alt="UML Diagram" /></p>
"""
            
            # Add PlantUML source if available
            if diagram_data.get('main_diagram') and diagram_data['main_diagram'].get('source'):
                source = diagram_data['main_diagram']['source']
                confluence_content += f"""
<h2>PlantUML Source</h2>
<pre><code>{source}</code></pre>
"""
            
            # Publish to Confluence
            result = confluence_service.create_or_update_page(
                title=title,
                content=confluence_content
            )
            
            if result.get('success'):
                # Get the full page URL
                page_id = result.get('page_id')
                confluence_url = confluence_service.confluence_url
                space_key = confluence_service.space_key
                page_url = f"{confluence_url}/spaces/{space_key}/pages/{page_id}"
                
                return jsonify({
                    "success": True,
                    "page_id": page_id,
                    "page_url": page_url,
                    "message": "UML diagram published successfully"
                })
            else:
                return jsonify({"error": result.get('message', 'Failed to publish')}), 500
                
        except Exception as e:
            print(f"Error publishing UML to Confluence: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Static files are now handled by Flask's default static handling
    
    # UML page endpoints
    @app.route('/uml', methods=['GET', 'POST'])
    def uml_page():
        """Render and handle UML diagrams page."""
        # Check demo authentication
        if not require_demo_auth():
            return redirect(url_for('login'))
            
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
    
    # Debug endpoint for OpenAI settings
    @app.route('/api/debug/openai')
    def debug_openai():
        """Debug endpoint to check OpenAI configuration."""
        openai_settings = openai_service.get_settings()
        has_valid = openai_service.has_valid_settings()
        
        if openai_settings:
            # Mask the API key for security
            masked_key = openai_settings["api_key"][:8] + "..." + openai_settings["api_key"][-4:]
            openai_settings["api_key"] = masked_key
        
        return jsonify({
            "has_valid_settings": has_valid,
            "settings": openai_settings,
            "env_key_exists": bool(settings.OPENAI_API_KEY),
            "env_key_starts_with_sk": settings.OPENAI_API_KEY.startswith("sk-") if settings.OPENAI_API_KEY else False,
            "openai_library_available": OPENAI_AVAILABLE
        })
    
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