"""
Confluence integration service for publishing documentation.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from atlassian import Confluence
import re
from core.config import settings


class ConfluenceService:
    """Service for managing Confluence documentation publishing."""
    
    def __init__(self):
        """Initialize Confluence connection if credentials are available."""
        self.enabled = False
        self.confluence = None
        
        if all([
            settings.CONFLUENCE_URL,
            settings.CONFLUENCE_USERNAME,
            settings.CONFLUENCE_API_TOKEN,
            settings.CONFLUENCE_SPACE_KEY
        ]):
            try:
                self.confluence = Confluence(
                    url=settings.CONFLUENCE_URL,
                    username=settings.CONFLUENCE_USERNAME,
                    password=settings.CONFLUENCE_API_TOKEN
                )
                self.space_key = settings.CONFLUENCE_SPACE_KEY
                self.enabled = True
                print(f"Confluence connection established to {settings.CONFLUENCE_URL}")
            except Exception as e:
                print(f"Failed to connect to Confluence: {e}")
                self.enabled = False
        else:
            print("Confluence credentials not configured")
    
    def is_enabled(self) -> bool:
        """Check if Confluence integration is enabled."""
        return self.enabled
    
    def create_or_update_page(
        self, 
        title: str, 
        content: str, 
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update a Confluence page.
        
        Args:
            title: Page title
            content: Page content in Confluence storage format
            parent_id: Parent page ID (optional)
            
        Returns:
            Page information dict
        """
        if not self.enabled:
            raise Exception("Confluence integration is not enabled")
        
        # Convert Markdown to Confluence format if it looks like Markdown
        if content.strip().startswith('#') or '```' in content or '**' in content or '- ' in content:
            content = self.markdown_to_confluence_storage(content)
        
        # Check if page exists
        existing_page = self.confluence.get_page_by_title(
            space=self.space_key,
            title=title
        )
        
        if existing_page:
            # Update existing page
            page_id = existing_page['id']
            result = self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=content
            )
            print(f"Updated Confluence page: {title}")
        else:
            # Create new page
            result = self.confluence.create_page(
                space=self.space_key,
                title=title,
                body=content,
                parent_id=parent_id or settings.CONFLUENCE_PARENT_PAGE_ID
            )
            print(f"Created Confluence page: {title}")
        
        return result
    
    def markdown_to_confluence_storage(self, markdown_content: str) -> str:
        """
        Convert Markdown to Confluence storage format.
        
        Args:
            markdown_content: Markdown formatted text
            
        Returns:
            Confluence storage format XML/HTML
        """
        # Start with basic HTML wrapper
        html = markdown_content
        
        # Convert headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Convert bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Convert code blocks
        html = re.sub(r'```(\w+)?\n(.*?)\n```', lambda m: f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">{m.group(1) or "text"}</ac:parameter><ac:plain-text-body><![CDATA[{m.group(2)}]]></ac:plain-text-body></ac:structured-macro>', html, flags=re.DOTALL)
        
        # Convert inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Convert links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Convert unordered lists
        lines = html.split('\n')
        in_list = False
        new_lines = []
        
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    new_lines.append('<ul>')
                    in_list = True
                new_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list and not line.strip().startswith('- '):
                    new_lines.append('</ul>')
                    in_list = False
                new_lines.append(line)
        
        if in_list:
            new_lines.append('</ul>')
        
        html = '\n'.join(new_lines)
        
        # Convert tables
        html = re.sub(r'\|(.+)\|', lambda m: self._convert_table_row(m.group(0)), html)
        
        # Convert line breaks
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f'<p>{html}</p>'
        
        # Clean up empty paragraphs
        html = re.sub(r'<p>\s*</p>', '', html)
        html = re.sub(r'<p>(<h[1-6]>)', r'\1', html)
        html = re.sub(r'(</h[1-6]>)</p>', r'\1', html)
        
        return html
    
    def _convert_table_row(self, row: str) -> str:
        """Convert a markdown table row to HTML."""
        cells = row.strip('|').split('|')
        if all('---' in cell for cell in cells):
            return ''  # Skip separator rows
        
        cell_html = ''.join(f'<td>{cell.strip()}</td>' for cell in cells)
        return f'<tr>{cell_html}</tr>'
    
    def publish_endpoint_doc(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish FastAPI endpoint documentation to Confluence.
        
        Args:
            endpoint_data: Endpoint information from scanner
            
        Returns:
            Page information dict
        """
        title = f"API: {endpoint_data.get('method', 'GET')} {endpoint_data.get('path', '/unknown')}"
        content = self._render_endpoint_template(endpoint_data)
        
        return self.create_or_update_page(title, content)
    
    def publish_coverage_report(
        self, 
        items: List[Dict[str, Any]], 
        title_suffix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish documentation coverage report to Confluence.
        
        Args:
            items: List of documentation items from scanner
            title_suffix: Optional suffix for the title
            
        Returns:
            Page information dict
        """
        title = f"Documentation Coverage Report"
        if title_suffix:
            title += f" - {title_suffix}"
        else:
            title += f" - {datetime.now().strftime('%Y-%m-%d')}"
        
        content = self._render_coverage_template(items)
        
        return self.create_or_update_page(title, content)
    
    def publish_uml_diagram(
        self, 
        diagram_data: Dict[str, Any], 
        title_suffix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish UML diagram to Confluence with image attachments.
        
        Args:
            diagram_data: UML diagram information containing source and URLs
            title_suffix: Optional suffix for the title
            
        Returns:
            Page information dict
        """
        config_name = diagram_data.get('config_name', 'diagram')
        title = f"UML {config_name.title()} Diagram"
        if title_suffix:
            title += f" - {title_suffix}"
        else:
            title += f" - {datetime.now().strftime('%Y-%m-%d')}"
        
        # First create the page with basic content
        initial_content = self._render_uml_template(diagram_data, include_images=False)
        page_result = self.create_or_update_page(title, initial_content)
        page_id = page_result.get('id')
        
        if not page_id:
            return page_result
        
        # Upload images as attachments
        attachments = self._upload_diagram_attachments(page_id, diagram_data)
        
        # Update page content with image references
        final_content = self._render_uml_template(diagram_data, include_images=True, attachments=attachments)
        self.confluence.update_page(
            page_id=page_id,
            title=title,
            body=final_content
        )
        
        return page_result
    
    def _upload_diagram_attachments(self, page_id: str, diagram_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Upload UML diagram images as attachments to Confluence page.
        
        Args:
            page_id: Confluence page ID
            diagram_data: UML diagram information
            
        Returns:
            Dict mapping diagram types to attachment filenames
        """
        attachments = {}
        
        # Upload main diagram
        main_diagram = diagram_data.get('main_diagram', {})
        if main_diagram and main_diagram.get('url'):
            main_file_path = self._get_local_file_path(main_diagram['url'])
            if main_file_path and main_file_path.exists():
                config_name = diagram_data.get('config_name', 'diagram')
                filename = f"uml_{config_name}_main.png"
                
                try:
                    self.confluence.attach_file(
                        filename=str(main_file_path),
                        name=filename,
                        content_type="image/png",
                        page_id=page_id
                    )
                    attachments['main'] = filename
                    print(f"Uploaded main diagram as {filename}")
                except Exception as e:
                    print(f"Failed to upload main diagram: {e}")
        
        # Upload additional diagrams
        additional_diagrams = diagram_data.get('additional_diagrams', {})
        for diagram_type, diagram_info in additional_diagrams.items():
            if diagram_info and diagram_info.get('url'):
                file_path = self._get_local_file_path(diagram_info['url'])
                if file_path and file_path.exists():
                    config_name = diagram_data.get('config_name', 'diagram')
                    filename = f"uml_{config_name}_{diagram_type}.png"
                    
                    try:
                        self.confluence.attach_file(
                            filename=str(file_path),
                            name=filename,
                            content_type="image/png",
                            page_id=page_id
                        )
                        attachments[diagram_type] = filename
                        print(f"Uploaded {diagram_type} diagram as {filename}")
                    except Exception as e:
                        print(f"Failed to upload {diagram_type} diagram: {e}")
        
        return attachments
    
    def _get_local_file_path(self, url: str) -> Optional[Path]:
        """Convert API URL to local file path."""
        if '/api/uml/cache/' in url:
            # Extract filename from URL like /api/uml/cache/abc123.png
            filename = url.split('/api/uml/cache/')[-1]
            cache_dir = Path("reports/uml_cache")
            return cache_dir / filename
        return None
    
    def _render_endpoint_template(self, endpoint: Dict[str, Any]) -> str:
        """Render endpoint documentation in Confluence storage format."""
        method = endpoint.get('method', 'GET')
        path = endpoint.get('path', '/unknown')
        docstring = endpoint.get('docstring', 'No documentation available')
        
        # Parse docstring sections
        doc_sections = self._parse_docstring(docstring)
        
        # Build Confluence storage format content
        content = f"""
        <h2>Endpoint Details</h2>
        <table>
            <tbody>
                <tr>
                    <th>Method</th>
                    <td><code>{method}</code></td>
                </tr>
                <tr>
                    <th>Path</th>
                    <td><code>{path}</code></td>
                </tr>
                <tr>
                    <th>Module</th>
                    <td>{endpoint.get('module', 'N/A')}</td>
                </tr>
                <tr>
                    <th>Function</th>
                    <td><code>{endpoint.get('qualname', 'N/A')}</code></td>
                </tr>
            </tbody>
        </table>
        
        <h2>Description</h2>
        <p>{doc_sections.get('description', 'No description available')}</p>
        """
        
        # Add parameters section if available
        if doc_sections.get('args'):
            content += """
            <h2>Parameters</h2>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
            """
            for arg in doc_sections['args']:
                content += f"""
                    <tr>
                        <td><code>{arg['name']}</code></td>
                        <td>{arg['description']}</td>
                    </tr>
                """
            content += """
                </tbody>
            </table>
            """
        
        # Add returns section
        if doc_sections.get('returns'):
            content += f"""
            <h2>Returns</h2>
            <p>{doc_sections['returns']}</p>
            """
        
        # Add raises section
        if doc_sections.get('raises'):
            content += """
            <h2>Exceptions</h2>
            <ul>
            """
            for exc in doc_sections['raises']:
                content += f"""
                <li><code>{exc['type']}</code>: {exc['description']}</li>
                """
            content += """
            </ul>
            """
        
        # Add metadata
        content += f"""
        <h2>Metadata</h2>
        <table>
            <tbody>
                <tr>
                    <th>Documentation Coverage</th>
                    <td>{endpoint.get('coverage_score', 0)}%</td>
                </tr>
                <tr>
                    <th>Last Updated</th>
                    <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </tbody>
        </table>
        """
        
        return content
    
    def _render_coverage_template(self, items: List[Dict[str, Any]]) -> str:
        """Render coverage report in Confluence storage format."""
        total_items = len(items)
        documented_items = sum(1 for item in items if item.get('docstring'))
        coverage_percent = (documented_items / total_items * 100) if total_items > 0 else 0
        
        # Group by type
        by_type = {}
        for item in items:
            item_type = item.get('method', 'UNKNOWN')
            if item_type not in by_type:
                by_type[item_type] = {'total': 0, 'documented': 0}
            by_type[item_type]['total'] += 1
            if item.get('docstring'):
                by_type[item_type]['documented'] += 1
        
        content = f"""
        <h1>Documentation Coverage Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Overall Coverage</h2>
        <ac:structured-macro ac:name="panel" ac:schema-version="1">
            <ac:parameter ac:name="bgColor">#{"00875a" if coverage_percent >= 80 else "de350b" if coverage_percent < 50 else "ff991f"}</ac:parameter>
            <ac:rich-text-body>
                <h3 style="color: white;">{coverage_percent:.1f}% Coverage</h3>
                <p style="color: white;">{documented_items} of {total_items} items documented</p>
            </ac:rich-text-body>
        </ac:structured-macro>
        
        <h2>Coverage by Type</h2>
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Total</th>
                    <th>Documented</th>
                    <th>Coverage</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item_type, stats in by_type.items():
            coverage = (stats['documented'] / stats['total'] * 100) if stats['total'] > 0 else 0
            content += f"""
                <tr>
                    <td>{item_type}</td>
                    <td>{stats['total']}</td>
                    <td>{stats['documented']}</td>
                    <td>{coverage:.1f}%</td>
                </tr>
            """
        
        content += """
            </tbody>
        </table>
        
        <h2>Undocumented Items</h2>
        """
        
        # List undocumented items
        undocumented = [item for item in items if not item.get('docstring')]
        if undocumented:
            content += """
            <table>
                <thead>
                    <tr>
                        <th>Module</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>File</th>
                    </tr>
                </thead>
                <tbody>
            """
            for item in undocumented[:20]:  # Limit to first 20
                content += f"""
                    <tr>
                        <td>{item.get('module', 'N/A')}</td>
                        <td><code>{item.get('qualname', 'N/A')}</code></td>
                        <td>{item.get('method', 'N/A')}</td>
                        <td>{item.get('file_path', 'N/A')}</td>
                    </tr>
                """
            
            if len(undocumented) > 20:
                content += f"""
                    <tr>
                        <td colspan="4"><em>... and {len(undocumented) - 20} more undocumented items</em></td>
                    </tr>
                """
            
            content += """
                </tbody>
            </table>
            """
        else:
            content += "<p>All items are documented!</p>"
        
        return content
    
    def _parse_docstring(self, docstring: str) -> Dict[str, Any]:
        """Parse docstring into sections."""
        if not docstring:
            return {}
        
        sections = {
            'description': '',
            'args': [],
            'returns': '',
            'raises': []
        }
        
        lines = docstring.strip().split('\n')
        current_section = 'description'
        
        for line in lines:
            line = line.strip()
            
            if line.lower().startswith('args:') or line.lower().startswith('arguments:'):
                current_section = 'args'
            elif line.lower().startswith('returns:'):
                current_section = 'returns'
            elif line.lower().startswith('raises:'):
                current_section = 'raises'
            elif current_section == 'description' and line:
                sections['description'] += line + ' '
            elif current_section == 'args' and line and not line.endswith(':'):
                # Parse "name: description" format
                if ':' in line:
                    name, desc = line.split(':', 1)
                    sections['args'].append({
                        'name': name.strip(),
                        'description': desc.strip()
                    })
            elif current_section == 'returns' and line and not line.endswith(':'):
                sections['returns'] += line + ' '
            elif current_section == 'raises' and line and not line.endswith(':'):
                # Parse "ExceptionType: description" format
                if ':' in line:
                    exc_type, desc = line.split(':', 1)
                    sections['raises'].append({
                        'type': exc_type.strip(),
                        'description': desc.strip()
                    })
        
        return sections
    
    def _render_uml_template(self, diagram_data: Dict[str, Any], include_images: bool = True, attachments: Optional[Dict[str, str]] = None) -> str:
        """Render UML diagram in Confluence storage format."""
        config_name = diagram_data.get('config_name', 'diagram')
        main_diagram = diagram_data.get('main_diagram', {})
        additional_diagrams = diagram_data.get('additional_diagrams', {})
        analysis = diagram_data.get('analysis', {})
        
        content = f"""
        <h1>UML {config_name.title()} Diagram</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        # Add analysis summary if available
        if analysis:
            content += f"""
            <h2>Analysis Summary</h2>
            <ac:structured-macro ac:name="panel" ac:schema-version="1">
                <ac:parameter ac:name="bgColor">#deebff</ac:parameter>
                <ac:rich-text-body>
                    <ul>
                        <li><strong>Classes found:</strong> {analysis.get('classes_found', 'N/A')}</li>
                        <li><strong>Relationships found:</strong> {analysis.get('relationships_found', 'N/A')}</li>
                        <li><strong>Packages:</strong> {', '.join(analysis.get('packages', []))}</li>
                    </ul>
                </ac:rich-text-body>
            </ac:structured-macro>
            """
        
        # Add main diagram if available
        if main_diagram and main_diagram.get('url'):
            diagram_type = main_diagram.get('type', 'Main').title()
            content += f"""
            <h2>{diagram_type} Diagram</h2>
            """
            
            # Add image if attachments are available
            if include_images and attachments and 'main' in attachments:
                content += f"""
                <ac:image ac:alt="{diagram_type} Diagram">
                    <ri:attachment ri:filename="{attachments['main']}" />
                </ac:image>
                <p><em>Diagram automatically uploaded and displayed above.</em></p>
                """
            elif not include_images:
                content += "<p><em>Image will be uploaded as attachment after page creation.</em></p>"
            else:
                content += f"""
                <p><em>Note: The diagram image should be uploaded as an attachment.</em></p>
                <p><strong>Source URL:</strong> <code>{main_diagram.get('url')}</code></p>
                """
            
            # Include PlantUML source
            if main_diagram.get('source'):
                content += f"""
                <h3>PlantUML Source</h3>
                <ac:structured-macro ac:name="code" ac:schema-version="1">
                    <ac:parameter ac:name="language">plantuml</ac:parameter>
                    <ac:parameter ac:name="theme">Midnight</ac:parameter>
                    <ac:rich-text-body>
                        <![CDATA[{main_diagram.get('source')}]]>
                    </ac:rich-text-body>
                </ac:structured-macro>
                """
        
        # Add additional diagrams
        if additional_diagrams:
            content += "<h2>Additional Diagrams</h2>"
            for diagram_type, diagram_info in additional_diagrams.items():
                if diagram_info.get('url'):
                    content += f"""
                    <h3>{diagram_type.title()} Diagram</h3>
                    """
                    
                    # Add image if attachments are available
                    if include_images and attachments and diagram_type in attachments:
                        content += f"""
                        <ac:image ac:alt="{diagram_type.title()} Diagram">
                            <ri:attachment ri:filename="{attachments[diagram_type]}" />
                        </ac:image>
                        <p><em>Diagram automatically uploaded and displayed above.</em></p>
                        """
                    elif not include_images:
                        content += "<p><em>Image will be uploaded as attachment after page creation.</em></p>"
                    else:
                        content += f"""
                        <p><strong>Source URL:</strong> <code>{diagram_info.get('url')}</code></p>
                        """
        
        # Add usage instructions
        if include_images and attachments:
            content += """
            <h2>About This Diagram</h2>
            <ac:structured-macro ac:name="info" ac:schema-version="1">
                <ac:rich-text-body>
                    <p>This UML diagram was automatically generated from the codebase structure and uploaded to this page. 
                    The diagrams show the relationships between classes, methods, and modules in your project.</p>
                    <p>You can regenerate these diagrams at any time using the documentation system.</p>
                </ac:rich-text-body>
            </ac:structured-macro>
            """
        else:
            content += """
            <h2>Usage Instructions</h2>
            <ac:structured-macro ac:name="info" ac:schema-version="1">
                <ac:rich-text-body>
                    <p>This UML diagram was automatically generated from the codebase structure. 
                    The diagram images will be uploaded as attachments to this page.</p>
                </ac:rich-text-body>
            </ac:structured-macro>
            """
        
        return content


# Global confluence service instance
confluence_service = ConfluenceService()