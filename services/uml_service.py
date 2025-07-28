"""
UML generation service for creating PlantUML diagrams from documentation items.
Integrates with the existing scanner workflow and provides API endpoints.
"""

import base64
import hashlib
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import json

from fastdoc.uml_analyzer import UMLAnalyzer
from fastdoc.plantuml_generator import PlantUMLGenerator, DiagramConfig, DiagramType, create_diagram_configs
from fastdoc.models import DocItem
from core.config import settings


class UMLService:
    """Service for generating and managing UML diagrams."""
    
    def __init__(self):
        self.analyzer = UMLAnalyzer()
        self.generator = PlantUMLGenerator()
        self.configs = create_diagram_configs()
        
        # PlantUML server configuration with fallbacks
        self.plantuml_servers = [
            os.getenv("PLANTUML_SERVER", "http://www.plantuml.com/plantuml"),
            "https://kroki.io/plantuml",  # Alternative reliable server
            "http://plantuml.com:8080/plantuml"  # Another fallback
        ]
        self.current_server_index = 0
        self.use_local_plantuml = os.getenv("USE_LOCAL_PLANTUML", "false").lower() == "true"
        self.plantuml_jar_path = os.getenv("PLANTUML_JAR_PATH", "./plantuml.jar")
        
        # Cache directory for generated diagrams
        self.cache_dir = Path(settings.REPORTS_DIR) / "uml_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_uml_diagrams(self, items: List[DocItem], 
                            config_name: str = "overview") -> Dict[str, Any]:
        """Generate UML diagrams from documentation items."""
        try:
            # Debug: Print input items
            print(f"UML Generation received {len(items)} items:")
            method_counts = {}
            for item in items[:10]:  # Show first 10 items
                method_counts[item.method] = method_counts.get(item.method, 0) + 1
                print(f"  - {item.qualname} (method: {item.method}, module: {item.module})")
            print(f"Method counts: {method_counts}")
            
            # Analyze relationships
            analysis_result = self.analyzer.analyze_documentation_items(items)
            
            # Debug: Print analysis results
            print(f"UML Analysis found {len(analysis_result['classes'])} classes:")
            for name, cls in analysis_result['classes'].items():
                print(f"  - {name} (stereotype: {cls.stereotype})")
            print(f"Found {len(analysis_result['relationships'])} relationships")
            
            # Get configuration
            config = self.configs.get(config_name, self.configs["overview"])
            
            # Generate PlantUML source
            plantuml_source = self.generator.generate_diagram(analysis_result, config)
            
            # Generate diagram image
            diagram_url = self._render_plantuml(plantuml_source)
            print(f"Generated diagram URL: {diagram_url}")
            
            # Generate additional diagram types
            additional_diagrams = {}
            
            # Sequence diagram for main endpoints
            main_endpoints = [item for item in items if item.method in ["GET", "POST", "PUT", "DELETE"]]
            if main_endpoints:
                sequence_source = self.generator.generate_fastapi_sequence_diagram(
                    analysis_result, main_endpoints[0].qualname
                )
                additional_diagrams["sequence"] = {
                    "source": sequence_source,
                    "url": self._render_plantuml(sequence_source)
                }
            
            # Component diagram
            component_source = self.generator.generate_component_diagram(analysis_result)
            additional_diagrams["component"] = {
                "source": component_source,
                "url": self._render_plantuml(component_source)
            }
            
            return {
                "success": True,
                "main_diagram": {
                    "type": config_name,
                    "source": plantuml_source,
                    "url": diagram_url
                },
                "additional_diagrams": additional_diagrams,
                "analysis": {
                    "classes_found": len(analysis_result["classes"]),
                    "relationships_found": len(analysis_result["relationships"]),
                    "packages": list(set(cls.package for cls in analysis_result["classes"].values()))
                },
                "available_configs": list(self.configs.keys())
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "available_configs": list(self.configs.keys())
            }
    
    def generate_custom_diagram(self, items: List[DocItem], 
                              custom_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UML diagram with custom configuration."""
        try:
            # Create custom configuration
            config = DiagramConfig(
                diagram_type=DiagramType(custom_config.get("diagram_type", "class_overview")),
                include_methods=custom_config.get("include_methods", True),
                include_attributes=custom_config.get("include_attributes", True),
                include_private=custom_config.get("include_private", False),
                max_classes=custom_config.get("max_classes", 20),
                focus_packages=custom_config.get("focus_packages", []),
                exclude_packages=custom_config.get("exclude_packages", []),
                show_builtin_types=custom_config.get("show_builtin_types", False),
                group_by_package=custom_config.get("group_by_package", True),
                show_stereotypes=custom_config.get("show_stereotypes", True),
                color_by_type=custom_config.get("color_by_type", True),
                layout_direction=custom_config.get("layout_direction", "top to bottom direction")
            )
            
            # Analyze and generate
            analysis_result = self.analyzer.analyze_documentation_items(items)
            plantuml_source = self.generator.generate_diagram(analysis_result, config)
            diagram_url = self._render_plantuml(plantuml_source)
            
            return {
                "success": True,
                "diagram": {
                    "source": plantuml_source,
                    "url": diagram_url
                },
                "config_used": custom_config
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_configurations(self) -> Dict[str, Any]:
        """Get available diagram configurations with descriptions."""
        return {
            "overview": {
                "name": "Class Overview",
                "description": "High-level class relationships without method details",
                "best_for": "Understanding overall architecture"
            },
            "detailed": {
                "name": "Detailed Classes", 
                "description": "Complete class diagrams with methods and attributes",
                "best_for": "Code documentation and detailed analysis"
            },
            "services": {
                "name": "Service Layer",
                "description": "Focus on service classes and their relationships",
                "best_for": "Understanding business logic organization"
            },
            "models": {
                "name": "Data Models",
                "description": "Pydantic models and data structures",
                "best_for": "API data flow and validation understanding"
            },
            "fastapi": {
                "name": "FastAPI Architecture",
                "description": "FastAPI-specific components (routers, endpoints, dependencies)",
                "best_for": "Understanding API structure and routing"
            }
        }
    
    def _render_plantuml(self, plantuml_source: str) -> str:
        """Render PlantUML source to image URL."""
        # Create cache key
        cache_key = hashlib.md5(plantuml_source.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.png"
        
        # Return cached version if exists
        if cache_file.exists():
            return f"/api/uml/cache/{cache_key}.png"
        
        try:
            if self.use_local_plantuml and os.path.exists(self.plantuml_jar_path):
                return self._render_local_plantuml(plantuml_source, cache_file)
            else:
                return self._render_server_plantuml(plantuml_source, cache_file)
        except Exception as e:
            print(f"PlantUML rendering failed: {e}")
            return None
    
    def _render_server_plantuml(self, plantuml_source: str, cache_file: Path) -> str:
        """Render PlantUML using online server via POST request."""
        
        # Try different servers if one fails
        for server in self.plantuml_servers:
            try:
                result = self._try_plantuml_server(server, plantuml_source, cache_file)
                if result:
                    return result
            except Exception as e:
                print(f"Server {server} failed: {e}")
                continue
        
        print("All PlantUML servers failed")
        return None
    
    def _try_plantuml_server(self, server: str, plantuml_source: str, cache_file: Path) -> str:
        """Try a specific PlantUML server."""
        # Handle different server formats
        if "kroki.io" in server:
            url = f"{server}/png"
        else:
            url = f"{server}/png/"
        
        print(f"Trying PlantUML server: {server}")
        
        try:
            # Send PlantUML source as text in POST request
            response = requests.post(
                url, 
                data=plantuml_source.encode('utf-8'),
                headers={'Content-Type': 'text/plain'},
                timeout=30
            )
            print(f"Server {server} response status: {response.status_code}")
            
            response.raise_for_status()
            
            # Check if response is actually an image
            content_type = response.headers.get('content-type', '')
            print(f"Response content type: {content_type}")
            
            if 'image' not in content_type.lower() and 'png' not in content_type.lower():
                print(f"Warning: Response may not be an image. Content: {response.text[:200]}")
                # Try alternative approach with form data
                response = requests.post(
                    url,
                    data={'text': plantuml_source},
                    timeout=30
                )
                response.raise_for_status()
            
            # Save to cache
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            
            print(f"Successfully saved diagram from {server} to cache: {cache_file}")
            return f"/api/uml/cache/{cache_file.name}"
            
        except requests.RequestException as e:
            print(f"Server {server} failed: {e}")
            raise  # Re-raise to try next server
    
    def _render_local_plantuml(self, plantuml_source: str, cache_file: Path) -> str:
        """Render PlantUML using local JAR file."""
        import subprocess
        
        # Create temporary source file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False) as temp_file:
            temp_file.write(plantuml_source)
            temp_file_path = temp_file.name
        
        try:
            # Run PlantUML JAR
            cmd = [
                "java", "-jar", self.plantuml_jar_path,
                "-tpng",
                f"-o{cache_file.parent}",
                temp_file_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Move generated file to correct name
            generated_file = cache_file.parent / f"{Path(temp_file_path).stem}.png"
            if generated_file.exists():
                generated_file.rename(cache_file)
            
            return f"/api/uml/cache/{cache_file.name}"
            
        except subprocess.CalledProcessError as e:
            print(f"Local PlantUML rendering failed: {e}")
            raise
        finally:
            # Cleanup
            os.unlink(temp_file_path)
    
    def get_cached_diagram(self, cache_key: str) -> Optional[Path]:
        """Get cached diagram file."""
        cache_file = self.cache_dir / cache_key
        return cache_file if cache_file.exists() else None
    
    def create_confluence_uml_content(self, diagrams: Dict[str, Any]) -> str:
        """Create Confluence-compatible content with UML diagrams."""
        lines = [
            "<h2>UML Diagrams</h2>",
            "<p>Auto-generated UML diagrams showing the application architecture.</p>",
            ""
        ]
        
        # Main diagram
        main_diagram = diagrams.get("main_diagram", {})
        if main_diagram.get("url"):
            lines.extend([
                f"<h3>{main_diagram.get('type', 'Main').title()} Diagram</h3>",
                f"<img src=\"{main_diagram['url']}\" alt=\"Class Diagram\" />",
                "<details>",
                "<summary>PlantUML Source</summary>",
                "<pre><code>",
                main_diagram.get("source", ""),
                "</code></pre>",
                "</details>",
                ""
            ])
        
        # Additional diagrams
        additional = diagrams.get("additional_diagrams", {})
        for diagram_type, diagram_data in additional.items():
            if diagram_data.get("url"):
                lines.extend([
                    f"<h3>{diagram_type.title()} Diagram</h3>",
                    f"<img src=\"{diagram_data['url']}\" alt=\"{diagram_type} Diagram\" />",
                    "<details>",
                    "<summary>PlantUML Source</summary>", 
                    "<pre><code>",
                    diagram_data.get("source", ""),
                    "</code></pre>",
                    "</details>",
                    ""
                ])
        
        return "\n".join(lines)
    
    def export_diagrams(self, diagrams: Dict[str, Any], export_format: str = "png") -> Dict[str, str]:
        """Export diagrams to files."""
        exported_files = {}
        
        timestamp = str(int(time.time()))
        export_dir = self.cache_dir / "exports" / timestamp
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Export main diagram
        main_diagram = diagrams.get("main_diagram", {})
        if main_diagram.get("source"):
            filename = f"main_diagram.{export_format}"
            file_path = export_dir / filename
            
            if export_format == "puml":
                file_path.write_text(main_diagram["source"])
            else:
                # Would need actual image rendering here
                pass
            
            exported_files["main"] = str(file_path)
        
        # Export additional diagrams
        additional = diagrams.get("additional_diagrams", {})
        for diagram_type, diagram_data in additional.items():
            if diagram_data.get("source"):
                filename = f"{diagram_type}_diagram.{export_format}"
                file_path = export_dir / filename
                
                if export_format == "puml":
                    file_path.write_text(diagram_data["source"])
                else:
                    # Would need actual image rendering here
                    pass
                
                exported_files[diagram_type] = str(file_path)
        
        return exported_files


# Global UML service instance
uml_service = UMLService()