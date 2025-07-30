"""
Markdown documentation generation service.
Generates structured Markdown files for Sphinx and Confluence.
"""

import os
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from fastdoc.models import DocItem
from core.config import settings
from services.business_service import business_service


class MarkdownService:
    """Service for generating Markdown documentation."""
    
    def __init__(self):
        """Initialize the Markdown service."""
        self.docs_dir = Path(settings.REPORTS_DIR) / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 for Markdown templates
        self.template_dir = Path("templates/markdown")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def generate_documentation(
        self,
        items: List[DocItem],
        project_name: str = "API Documentation",
        include_uml: bool = True,
        uml_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete Markdown documentation set.
        
        Args:
            items: List of documentation items
            project_name: Name of the project
            include_uml: Whether to include UML diagrams
            uml_data: Pre-generated UML diagram data
            
        Returns:
            Dictionary with file paths and metadata
        """
        try:
            print(f"Generating Markdown documentation for {len(items)} items")
            
            # Prepare data for templates
            context = self._prepare_context(items, project_name, uml_data)
            
            # Generate all documentation files
            generated_files = {}
            
            # 1. Index page
            generated_files['index'] = self._generate_index(context)
            
            # 2. Overview page
            generated_files['overview'] = self._generate_overview(context)
            
            # 3. Getting Started
            generated_files['getting_started'] = self._generate_getting_started(context)
            
            # 4. Code Structure
            generated_files['code_structure'] = self._generate_code_structure(context)
            
            # 5. Docstring Report
            generated_files['docstring_report'] = self._generate_docstring_report(context)
            
            # 6. UML Diagrams (if requested)
            if include_uml and uml_data:
                generated_files['uml_diagrams'] = self._generate_uml_page(context)
            
            # 7. API Reference
            generated_files['api_reference'] = self._generate_api_reference(context)
            
            # 8. FAQ
            generated_files['faq'] = self._generate_faq(context)
            
            # 9. Changelog
            generated_files['changelog'] = self._generate_changelog(context)
            
            # Create a master document for Confluence
            generated_files['confluence_master'] = self._generate_confluence_master(context)
            
            print(f"Successfully generated {len(generated_files)} Markdown files")
            
            return {
                "success": True,
                "files": generated_files,
                "docs_dir": str(self.docs_dir),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating Markdown documentation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_documentation_zip(
        self,
        items: List[DocItem],
        project_name: str = "API Documentation",
        include_uml: bool = True,
        uml_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate Markdown documentation and return as ZIP file.
        
        Args:
            items: List of documentation items
            project_name: Name of the project
            include_uml: Whether to include UML diagrams
            uml_data: Pre-generated UML diagram data
            
        Returns:
            Dictionary with ZIP file path and metadata
        """
        try:
            # Generate the documentation content
            result = self.generate_documentation(items, project_name, include_uml, uml_data)
            
            if not result.get('success'):
                return result
            
            # Create a temporary ZIP file
            temp_dir = Path(tempfile.mkdtemp())
            zip_filename = f"{project_name.replace(' ', '_')}_markdown_docs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = temp_dir / zip_filename
            
            # Create ZIP file with all generated content
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                generated_files = result.get('files', {})
                
                # Define file mapping (internal name -> filename in ZIP)
                file_mapping = {
                    'index': 'README.md',
                    'overview': 'docs/overview.md',
                    'getting_started': 'docs/getting_started.md',
                    'code_structure': 'docs/code_structure.md',
                    'docstring_report': 'docs/docstring_report.md',
                    'uml_diagrams': 'docs/uml_diagrams.md',
                    'api_reference': 'docs/api_reference.md',
                    'faq': 'docs/faq.md',
                    'changelog': 'docs/CHANGELOG.md',
                    'confluence_master': 'confluence/master_document.md'
                }
                
                # Add each generated file to the ZIP
                for internal_name, content in generated_files.items():
                    if internal_name in file_mapping and content:
                        zip_filename_inner = file_mapping[internal_name]
                        zipf.writestr(zip_filename_inner, content)
                
                # Add a project info file
                project_info = f"""# {project_name} Documentation

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total items documented: {len(items)}
Includes UML diagrams: {include_uml}

## Files in this package:

- README.md - Main documentation index
- docs/ - Detailed documentation pages
- confluence/ - Confluence-ready master document

## Usage:

1. Extract this ZIP file
2. Open README.md to start browsing the documentation
3. Use confluence/master_document.md for Confluence publishing
"""
                zipf.writestr('PROJECT_INFO.txt', project_info)
            
            print(f"Created ZIP file: {zip_path}")
            
            return {
                "success": True,
                "zip_path": str(zip_path),
                "zip_filename": zip_filename,
                "file_count": len(result.get('files', {})),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error creating documentation ZIP: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_context(
        self,
        items: List[DocItem],
        project_name: str,
        uml_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare context data for templates."""
        # Group items by type and module
        grouped_items = self._group_items(items)
        
        # Calculate statistics
        stats = self._calculate_stats(items)
        
        # Prepare module hierarchy
        module_tree = self._build_module_tree(items)
        
        # Get business overview
        business_overview = business_service.get_business_overview()
        
        return {
            "project_name": project_name,
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": items,
            "grouped_items": grouped_items,
            "stats": stats,
            "module_tree": module_tree,
            "uml_data": uml_data,
            "total_items": len(items),
            "business_overview": business_overview
        }
    
    def _group_items(self, items: List[DocItem]) -> Dict[str, List[DocItem]]:
        """Group items by type."""
        grouped = {
            "modules": [],
            "classes": [],
            "functions": [],
            "endpoints": []
        }
        
        for item in items:
            if item.method == "MODULE":
                grouped["modules"].append(item)
            elif item.method == "CLASS":
                grouped["classes"].append(item)
            elif item.method == "FUNCTION":
                grouped["functions"].append(item)
            elif item.method == "ENDPOINT":
                grouped["endpoints"].append(item)
        
        return grouped
    
    def _calculate_stats(self, items: List[DocItem]) -> Dict[str, Any]:
        """Calculate documentation statistics."""
        total = len(items)
        documented = sum(1 for item in items if item.docstring and item.docstring.strip())
        missing = total - documented
        coverage = (documented / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "documented": documented,
            "missing": missing,
            "coverage": round(coverage, 1),
            "by_type": {
                "modules": sum(1 for item in items if item.method == "MODULE"),
                "classes": sum(1 for item in items if item.method == "CLASS"),
                "functions": sum(1 for item in items if item.method == "FUNCTION"),
                "endpoints": sum(1 for item in items if item.method == "ENDPOINT")
            }
        }
    
    def _build_module_tree(self, items: List[DocItem]) -> Dict[str, Any]:
        """Build a hierarchical module tree."""
        tree = {}
        
        for item in items:
            if not item.module:
                continue
                
            parts = item.module.split('.')
            current = tree
            
            for part in parts:
                if part not in current:
                    current[part] = {"_items": [], "_children": {}}
                current = current[part]["_children"]
            
            # Add item to the deepest level
            parent = tree
            for part in parts[:-1]:
                parent = parent[part]["_children"]
            if parts:
                parent[parts[-1]]["_items"].append(item)
        
        return tree
    
    def _generate_index(self, context: Dict[str, Any]) -> str:
        """Generate index.md file."""
        content = f"""# {context['project_name']} Documentation

Welcome to the {context['project_name']} documentation. This documentation was automatically generated on {context['generation_date']}.

## Quick Navigation

- [📋 Overview](overview.md) - High-level project description
- [🚀 Getting Started](getting_started.md) - Installation and quick start guide
- [🏗️ Code Structure](code_structure.md) - Module and class organization
- [📊 Documentation Coverage](docstring_report.md) - Docstring coverage report
- [🔗 UML Diagrams](uml_diagrams.md) - Visual architecture diagrams
- [📡 API Reference](api_reference.md) - Detailed API documentation
- [❓ FAQ](faq.md) - Frequently asked questions
- [📝 Changelog](changelog.md) - Version history

## Documentation Statistics

- **Total Items**: {context['stats']['total']}
- **Documented**: {context['stats']['documented']} ({context['stats']['coverage']}%)
- **Missing Documentation**: {context['stats']['missing']}

### Coverage by Type

| Type | Count |
|------|-------|
| Modules | {context['stats']['by_type']['modules']} |
| Classes | {context['stats']['by_type']['classes']} |
| Functions | {context['stats']['by_type']['functions']} |
| Endpoints | {context['stats']['by_type']['endpoints']} |

## Quick Links

- [View on Confluence](confluence://documentation)
- [Download PDF Version](../latex/documentation.pdf)
- [View Source Code](https://github.com/your-repo)
"""
        
        file_path = self.docs_dir / "index.md"
        file_path.write_text(content)
        return str(file_path)
    
    def _generate_overview(self, context: Dict[str, Any]) -> str:
        """Generate overview.md file."""
        business_overview = context.get('business_overview')
        
        # Start with business overview if available
        content = f"""# Project Overview
"""
        
        if business_overview:
            content += f"""
## Business Overview
"""
            if business_overview.get('project_purpose'):
                content += f"""
**Project Purpose:** {business_overview['project_purpose']}
"""
            
            if business_overview.get('business_context'):
                content += f"""
**Business Context:** {business_overview['business_context']}
"""
            
            if business_overview.get('key_business_value'):
                content += f"""
**Key Business Value:** {business_overview['key_business_value']}
"""
        
        content += f"""
## Technical Overview

This project is a comprehensive API documentation system that automatically analyzes Python code and generates documentation in multiple formats.

## Key Features

- **Automatic Code Analysis**: Scans Python projects to extract functions, classes, and modules
- **Docstring Management**: Identifies missing documentation and helps maintain coverage
- **Multiple Output Formats**: 
  - PDF (technical documentation via LaTeX)
  - HTML (readable documentation via Sphinx)
  - Confluence (team collaboration)
  - JSON/YAML (for integrations)
- **Visual Architecture**: Generates UML diagrams for better understanding
- **Modern Dashboard**: Web-based interface for managing documentation

## Architecture Overview

The system follows a modular architecture:

1. **Scanner Service**: Parses Python code and extracts documentation items
2. **Documentation Services**: Generate output in various formats
3. **API Layer**: FastAPI-based REST API for all operations
4. **Dashboard**: Modern web interface for user interaction

## Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Documentation**: LaTeX, Sphinx, PlantUML
- **Frontend**: Vanilla JavaScript with modern CSS
- **Integrations**: Confluence API, OpenAI API

## Use Cases

1. **Development Teams**: Keep documentation in sync with code
2. **API Consumers**: Access up-to-date API documentation
3. **Project Managers**: Monitor documentation coverage
4. **New Team Members**: Quickly understand project structure
"""
        
        file_path = self.docs_dir / "overview.md"
        file_path.write_text(content)
        return str(file_path)
    
    def _generate_getting_started(self, context: Dict[str, Any]) -> str:
        """Generate getting_started.md file."""
        content = f"""# Getting Started

## Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)
- LaTeX distribution (for PDF generation)
- PlantUML (for diagram generation)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd docs_creator
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Quick Start

1. Start the server:
   ```bash
   poetry run python main.py
   ```

2. Open the dashboard:
   ```
   http://localhost:8200
   ```

3. Scan a project:
   - Enter the project path in the dashboard
   - Click "Scan Project"
   - Wait for analysis to complete

4. Generate documentation:
   - Choose your output format (PDF, HTML, Confluence)
   - Click the appropriate generation button
   - Download or view the results

## Configuration

### Confluence Integration

To enable Confluence publishing:

1. Set environment variables:
   ```bash
   CONFLUENCE_URL=https://your-domain.atlassian.net
   CONFLUENCE_USERNAME=your-email@example.com
   CONFLUENCE_API_TOKEN=your-api-token
   CONFLUENCE_SPACE_KEY=YOUR_SPACE
   ```

2. Test the connection in the dashboard

### OpenAI Integration

For AI-powered docstring generation:

1. Get an OpenAI API key
2. Add it in the dashboard settings
3. Use the "AI Generate" button when editing docstrings

## Next Steps

- [Explore the API Reference](api_reference.md)
- [View Code Structure](code_structure.md)
- [Check Documentation Coverage](docstring_report.md)
"""
        
        file_path = self.docs_dir / "getting_started.md"
        file_path.write_text(content)
        return str(file_path)
    
    def _generate_code_structure(self, context: Dict[str, Any]) -> str:
        """Generate code_structure.md file."""
        content = f"""# Code Structure

## Module Overview

This document provides a comprehensive view of the code structure, including all modules, classes, and functions.

## Module Hierarchy

"""
        # Add module tree visualization
        content += self._render_module_tree(context['module_tree'])
        
        content += f"""

## Detailed Structure

### Modules ({context['stats']['by_type']['modules']})

"""
        for item in context['grouped_items']['modules']:
            content += f"- **{item.module}** - {item.file_path}\n"
            if item.docstring:
                first_line = item.docstring.split('\n')[0]
                content += f"  - {first_line}\n"
        
        content += f"""

### Classes ({context['stats']['by_type']['classes']})

"""
        for item in context['grouped_items']['classes']:
            content += f"- **{item.qualname}** ({item.module})\n"
            if item.docstring:
                first_line = item.docstring.split('\n')[0]
                content += f"  - {first_line}\n"
        
        content += f"""

### Functions ({context['stats']['by_type']['functions']})

"""
        # Group functions by module
        functions_by_module = {}
        for item in context['grouped_items']['functions']:
            module = item.module or 'Unknown'
            if module not in functions_by_module:
                functions_by_module[module] = []
            functions_by_module[module].append(item)
        
        for module, functions in sorted(functions_by_module.items()):
            content += f"\n#### {module}\n\n"
            for func in functions:
                content += f"- `{func.qualname}()` - Line {getattr(func, 'line_number', 'N/A')}\n"
                if func.docstring:
                    first_line = func.docstring.split('\n')[0]
                    content += f"  - {first_line}\n"
        
        file_path = self.docs_dir / "code_structure.md"
        file_path.write_text(content)
        return str(file_path)
    
    def _render_module_tree(self, tree: Dict[str, Any], prefix: str = "") -> str:
        """Render module tree as text."""
        lines = []
        items = sorted(tree.items())
        
        for i, (name, data) in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            lines.append(f"{prefix}{current_prefix}{name}")
            
            # Add items in this module
            if data["_items"]:
                item_prefix = prefix + ("    " if is_last else "│   ")
                for j, item in enumerate(data["_items"]):
                    item_is_last = j == len(data["_items"]) - 1 and not data["_children"]
                    item_current = "└── " if item_is_last else "├── "
                    lines.append(f"{item_prefix}{item_current}{item.qualname} ({item.method})")
            
            # Recurse into children
            if data["_children"]:
                child_prefix = prefix + ("    " if is_last else "│   ")
                lines.append(self._render_module_tree(data["_children"], child_prefix))
        
        return "\n".join(lines)
    
    def _generate_docstring_report(self, context: Dict[str, Any]) -> str:
        """Generate docstring_report.md file."""
        content = f"""# Documentation Coverage Report

Generated on: {context['generation_date']}

## Summary

- **Total Items**: {context['stats']['total']}
- **Documented**: {context['stats']['documented']} ({context['stats']['coverage']}%)
- **Missing Documentation**: {context['stats']['missing']}

## Coverage Visualization

```
[{"█" * int(context['stats']['coverage'] / 10)}{"░" * (10 - int(context['stats']['coverage'] / 10))}] {context['stats']['coverage']}%
```

## Items Missing Documentation

The following items are missing documentation:

"""
        # List items without docstrings
        missing_items = [item for item in context['items'] if not item.docstring or not item.docstring.strip()]
        
        # Group by module
        missing_by_module = {}
        for item in missing_items:
            module = item.module or 'Unknown'
            if module not in missing_by_module:
                missing_by_module[module] = []
            missing_by_module[module].append(item)
        
        for module, items in sorted(missing_by_module.items()):
            content += f"\n### {module}\n\n"
            for item in items:
                content += f"- `{item.qualname}` ({item.method}) - Line {getattr(item, 'line_number', 'N/A')}\n"
        
        content += f"""

## Well-Documented Items

The following items have comprehensive documentation:

"""
        # List top documented items
        documented_items = [item for item in context['items'] if item.docstring and len(item.docstring) > 100]
        documented_items.sort(key=lambda x: len(x.docstring or ''), reverse=True)
        
        for item in documented_items[:10]:
            content += f"- `{item.qualname}` ({item.module}) - {len(item.docstring)} characters\n"
        
        file_path = self.docs_dir / "docstring_report.md"
        file_path.write_text(content)
        return str(file_path)
    
    def _generate_uml_page(self, context: Dict[str, Any]) -> str:
        """Generate uml_diagrams.md file."""
        content = f"""# UML Diagrams

## Architecture Overview

The following UML diagrams provide a visual representation of the system architecture.

"""
        
        if context.get('uml_data'):
            uml_data = context['uml_data']
            
            if uml_data.get('main_diagram'):
                content += f"""
### System Overview

![System Overview Diagram](../uml/{uml_data['main_diagram'].get('filename', 'overview.png')})

This diagram shows the high-level architecture and main components of the system.

"""
            
            if uml_data.get('detailed_diagrams'):
                content += """
### Detailed Component Diagrams

"""
                for diagram in uml_data['detailed_diagrams']:
                    content += f"""
#### {diagram.get('title', 'Component Diagram')}

![{diagram.get('title', 'Diagram')}](../uml/{diagram.get('filename', 'diagram.png')})

"""
        
        content += """
## Diagram Legend

- **Classes**: Represented as boxes with three sections (name, attributes, methods)
- **Inheritance**: Shown with empty arrows pointing to parent class
- **Composition**: Shown with filled diamonds
- **Association**: Shown with simple lines
- **Dependencies**: Shown with dashed arrows

## Generating Diagrams

These diagrams are automatically generated using PlantUML. To regenerate:

1. Go to the dashboard
2. Click "Generate UML Diagrams"
3. Select the diagram type
4. Wait for generation to complete
"""
        
        file_path = self.docs_dir / "uml_diagrams.md"
        file_path.write_text(content)
        return str(file_path)
    
    def _generate_api_reference(self, context: Dict[str, Any]) -> str:
        """Generate api_reference.md file."""
        content = f"""# API Reference

## Endpoints

This section documents all available API endpoints.

"""
        
        # Group endpoints by tag or module
        endpoints = context['grouped_items']['endpoints']
        
        if endpoints:
            for endpoint in endpoints:
                content += f"""
### {endpoint.qualname}

- **Method**: {endpoint.http_method if hasattr(endpoint, 'http_method') else 'GET'}
- **Path**: {endpoint.path if hasattr(endpoint, 'path') else endpoint.qualname}
- **Module**: {endpoint.module}

"""
                if endpoint.docstring:
                    content += f"{endpoint.docstring}\n\n"
                
                # Add parameter information if available
                if hasattr(endpoint, 'parameters') and endpoint.parameters:
                    content += "**Parameters:**\n\n"
                    for param in endpoint.parameters:
                        content += f"- `{param['name']}` ({param['type']}) - {param.get('description', 'No description')}\n"
                    content += "\n"
        else:
            content += """
No API endpoints found in the current documentation set.

## Available Services

"""
            # List service classes
            for class_item in context['grouped_items']['classes']:
                if 'service' in class_item.qualname.lower():
                    content += f"- **{class_item.qualname}** - {class_item.module}\n"
                    if class_item.docstring:
                        first_line = class_item.docstring.split('\n')[0]
                        content += f"  - {first_line}\n"
        
        content += """

## Usage Examples

For detailed usage examples, please refer to the [Getting Started](getting_started.md) guide.
"""
        
        file_path = self.docs_dir / "api_reference.md"
        file_path.write_text(content)
        return str(file_path)
    
    def _generate_faq(self, context: Dict[str, Any]) -> str:
        """Generate faq.md file."""
        content = f"""# Frequently Asked Questions

## General Questions

### What is {context['project_name']}?

{context['project_name']} is an automated documentation generation system that analyzes Python code and produces comprehensive documentation in multiple formats.

### What formats are supported?

- **PDF**: Technical documentation via LaTeX
- **HTML**: Readable documentation via Sphinx
- **Confluence**: Team collaboration pages
- **JSON/YAML**: Raw data for integrations

### How often should I regenerate documentation?

We recommend regenerating documentation:
- After each major feature release
- When documentation coverage drops below 80%
- Before onboarding new team members
- As part of your CI/CD pipeline

## Technical Questions

### How does the code scanner work?

The scanner uses Python's AST (Abstract Syntax Tree) to parse code and extract:
- Functions and their signatures
- Classes and their methods
- Module-level documentation
- Docstrings and their content

### Can I customize the generated documentation?

Yes! You can:
- Edit docstrings directly in the dashboard
- Modify Markdown templates
- Configure Sphinx themes
- Customize LaTeX templates

### What Python versions are supported?

The tool supports Python 3.8 and higher. It can analyze code written for any Python version.

## Integration Questions

### How do I set up Confluence integration?

1. Get an API token from Atlassian
2. Set environment variables (see [Getting Started](getting_started.md))
3. Configure space and parent page in settings

### Can I use this in CI/CD?

Yes! You can:
- Use the CLI mode for automation
- Call API endpoints directly
- Generate documentation as part of your build process

### Is there an API for external integrations?

Yes, all functionality is exposed via REST API. See the [API Reference](api_reference.md) for details.

## Troubleshooting

### Documentation generation fails

Common causes:
- Missing dependencies (LaTeX, PlantUML)
- Invalid Python syntax in scanned code
- Insufficient permissions on output directory

### UML diagrams are not showing

Ensure:
- PlantUML is installed and in PATH
- Java runtime is available
- Network access for PlantUML server (if using remote)

### Confluence publishing fails

Check:
- API credentials are correct
- You have write permissions to the space
- The parent page exists
"""
        
        file_path = self.docs_dir / "faq.md"
        file_path.write_text(content)
        return str(file_path)
    
    def _generate_changelog(self, context: Dict[str, Any]) -> str:
        """Generate changelog.md file."""
        content = f"""# Changelog

## Current Version

**Generated**: {context['generation_date']}  
**Total Items**: {context['total_items']}  
**Coverage**: {context['stats']['coverage']}%

## Documentation History

### Latest Changes

- Updated documentation for {context['stats']['total']} items
- Current coverage: {context['stats']['coverage']}%
- {context['stats']['missing']} items still need documentation

### Coverage Trend

| Date | Total Items | Documented | Coverage |
|------|-------------|------------|----------|
| {context['generation_date']} | {context['stats']['total']} | {context['stats']['documented']} | {context['stats']['coverage']}% |

## Recent Improvements

- Added modern dashboard interface
- Implemented LaTeX PDF generation
- Added Confluence integration
- Integrated OpenAI for docstring generation
- Added UML diagram support

## Upcoming Features

- [ ] Sphinx HTML documentation
- [ ] Automated CI/CD integration
- [ ] Documentation versioning
- [ ] Multi-language support
- [ ] Custom themes and templates

## Version History

### v2.0.0 - Modern Dashboard
- Complete UI redesign
- Added markdown generation
- Improved UML diagrams

### v1.5.0 - Confluence Integration
- Added Confluence publishing
- Improved image handling
- Better formatting support

### v1.0.0 - Initial Release
- Basic code scanning
- JSON report generation
- Simple web interface
"""
        
        file_path = self.docs_dir / "changelog.md"
        file_path.write_text(content)
        return str(file_path)
    
    def _generate_confluence_master(self, context: Dict[str, Any]) -> str:
        """Generate a master document optimized for Confluence."""
        business_overview = context.get('business_overview')
        
        content = f"""# {context['project_name']} Documentation

> **Generated**: {context['generation_date']}  
> **Coverage**: {context['stats']['coverage']}%  
> **Total Items**: {context['stats']['total']}

---
"""
        
        # Add business overview if available
        if business_overview:
            content += f"""
## 💼 Business Overview
"""
            if business_overview.get('project_purpose'):
                content += f"""
**Project Purpose:** {business_overview['project_purpose']}
"""
            
            if business_overview.get('business_context'):
                content += f"""
**Business Context:** {business_overview['business_context']}
"""
            
            if business_overview.get('key_business_value'):
                content += f"""
**Key Business Value:** {business_overview['key_business_value']}
"""
            content += f"""
---
"""
        
        content += f"""
## 📋 Technical Overview

{context['project_name']} is an automated documentation system that analyzes Python code and generates comprehensive documentation.

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Items | {context['stats']['total']} |
| Documented | {context['stats']['documented']} |
| Coverage | {context['stats']['coverage']}% |
| Modules | {context['stats']['by_type']['modules']} |
| Classes | {context['stats']['by_type']['classes']} |
| Functions | {context['stats']['by_type']['functions']} |

---

## 🏗️ Architecture

### Module Structure

```
{self._render_module_tree(context['module_tree'])}
```

---

## 📊 Documentation Coverage

### Summary
- ✅ Documented: {context['stats']['documented']} items
- ❌ Missing: {context['stats']['missing']} items
- 📈 Coverage: {context['stats']['coverage']}%

### Items Needing Documentation

"""
        # Add top 10 items missing documentation
        missing_items = [item for item in context['items'] if not item.docstring or not item.docstring.strip()][:10]
        
        for item in missing_items:
            content += f"- `{item.qualname}` ({item.module}) - Line {getattr(item, 'line_number', 'N/A')}\n"
        
        if len(missing_items) < context['stats']['missing']:
            content += f"\n*... and {context['stats']['missing'] - len(missing_items)} more items*\n"
        
        content += """

---

## 🚀 Quick Start

1. **Install dependencies**: `poetry install`
2. **Start server**: `poetry run python main.py`
3. **Open dashboard**: http://localhost:8200
4. **Scan project**: Enter path and click "Scan"

---

## 📡 API Endpoints

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scan-local` | POST | Scan a local project |
| `/api/report/data` | GET | Get current report data |
| `/api/docs/latex` | POST | Generate PDF documentation |
| `/api/confluence/publish` | POST | Publish to Confluence |

---

## 🔗 Links

- [View Dashboard](http://localhost:8200)
- [API Documentation](http://localhost:8200/docs)
- [Download PDF Report](../latex/documentation.pdf)

---

*This document was automatically generated. For the latest version, regenerate from the dashboard.*
"""
        
        file_path = self.docs_dir / "confluence_master.md"
        file_path.write_text(content)
        return content


# Singleton instance
markdown_service = MarkdownService()