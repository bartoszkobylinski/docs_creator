"""
Confluence integration service for publishing documentation.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from atlassian import Confluence
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
        Publish UML diagram to Confluence.
        
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
        
        content = self._render_uml_template(diagram_data)
        
        return self.create_or_update_page(title, content)
    
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
    
    def _render_uml_template(self, diagram_data: Dict[str, Any]) -> str:
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
            # Note: In real implementation, you'd need to upload the image as attachment
            # For now, we'll include the PlantUML source
            content += f"""
            <h2>{diagram_type} Diagram</h2>
            <p><em>Note: The diagram image should be uploaded as an attachment and referenced here.</em></p>
            <p><strong>Diagram URL:</strong> <code>{main_diagram.get('url')}</code></p>
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
                    <p><strong>Diagram URL:</strong> <code>{diagram_info.get('url')}</code></p>
                    """
        
        # Add usage instructions
        content += """
        <h2>Usage Instructions</h2>
        <ac:structured-macro ac:name="info" ac:schema-version="1">
            <ac:rich-text-body>
                <p>This UML diagram was automatically generated from the codebase structure. 
                To view the actual diagrams:</p>
                <ol>
                    <li>Access the documentation system at the provided URLs</li>
                    <li>Use the diagram URLs above to download the images</li>
                    <li>Upload the images as attachments to this page and reference them</li>
                </ol>
            </ac:rich-text-body>
        </ac:structured-macro>
        """
        
        return content


# Global confluence service instance
confluence_service = ConfluenceService()