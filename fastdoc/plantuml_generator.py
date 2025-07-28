"""
PlantUML diagram generator with intelligent filtering and layout optimization.
Creates readable, meaningful UML diagrams from relationship analysis.
"""

from typing import Dict, List, Set, Optional, Any
from enum import Enum
from dataclasses import dataclass

from .uml_analyzer import UMLAnalyzer, UMLClass, UMLRelationship, RelationshipType


class DiagramType(Enum):
    """Types of UML diagrams that can be generated."""
    CLASS_OVERVIEW = "class_overview"        # High-level class relationships
    CLASS_DETAILED = "class_detailed"        # Detailed class diagrams with methods
    PACKAGE_STRUCTURE = "package_structure"  # Package/module organization
    FASTAPI_ARCHITECTURE = "fastapi_arch"    # FastAPI-specific architecture
    SERVICE_LAYER = "service_layer"          # Service layer relationships
    DATA_MODEL = "data_model"                # Pydantic models and relationships


@dataclass
class DiagramConfig:
    """Configuration for PlantUML diagram generation."""
    diagram_type: DiagramType
    include_methods: bool = True
    include_attributes: bool = True
    include_private: bool = False
    max_classes: int = 20
    focus_packages: List[str] = None
    exclude_packages: List[str] = None
    show_builtin_types: bool = False
    group_by_package: bool = True
    show_stereotypes: bool = True
    color_by_type: bool = True
    layout_direction: str = "top to bottom direction"
    
    def __post_init__(self):
        if self.focus_packages is None:
            self.focus_packages = []
        if self.exclude_packages is None:
            self.exclude_packages = ["builtins", "typing", "collections"]


class PlantUMLGenerator:
    """Generates PlantUML diagrams from UML analysis results."""
    
    def __init__(self):
        self.color_scheme = {
            "service": "#E1F5FE",      # Light blue
            "model": "#E8F5E8",        # Light green  
            "repository": "#FFF3E0",   # Light orange
            "controller": "#F3E5F5",   # Light purple
            "configuration": "#FFEBEE", # Light red
            "interface": "#F1F8E9",    # Light lime
            "default": "#FFFFFF"       # White
        }
        
        self.stereotype_colors = {
            "<<service>>": "#2196F3",
            "<<model>>": "#4CAF50", 
            "<<repository>>": "#FF9800",
            "<<controller>>": "#9C27B0",
            "<<configuration>>": "#F44336",
            "<<interface>>": "#8BC34A"
        }
    
    def generate_diagram(self, analysis_result: Dict[str, Any], config: DiagramConfig) -> str:
        """Generate PlantUML diagram based on analysis and configuration."""
        classes = analysis_result["classes"]
        relationships = analysis_result["relationships"]
        
        # Filter classes and relationships based on config
        filtered_classes = self._filter_classes(classes, config)
        filtered_relationships = self._filter_relationships(relationships, filtered_classes, config)
        
        # Generate PlantUML content
        plantuml_lines = []
        
        # Header
        plantuml_lines.extend(self._generate_header(config))
        
        # Styling
        if config.color_by_type:
            plantuml_lines.extend(self._generate_styling())
        
        # Layout direction
        plantuml_lines.append(config.layout_direction)
        plantuml_lines.append("")
        
        # Package groupings
        if config.group_by_package:
            plantuml_lines.extend(self._generate_package_groups(filtered_classes, config))
        else:
            plantuml_lines.extend(self._generate_classes(filtered_classes, config))
        
        # Relationships
        plantuml_lines.append("")
        plantuml_lines.extend(self._generate_relationships(filtered_relationships))
        
        # Footer
        plantuml_lines.extend(self._generate_footer())
        
        return "\n".join(plantuml_lines)
    
    def _filter_classes(self, classes: Dict[str, UMLClass], config: DiagramConfig) -> Dict[str, UMLClass]:
        """Filter classes based on configuration."""
        filtered = {}
        
        for name, uml_class in classes.items():
            # Skip if package is excluded
            if any(exc in uml_class.package for exc in config.exclude_packages):
                continue
            
            # Include only if package is in focus (if focus_packages specified)
            if config.focus_packages and not any(focus in uml_class.package for focus in config.focus_packages):
                continue
            
            # Skip private classes if not included
            if not config.include_private and name.startswith("_"):
                continue
            
            # Filter based on diagram type
            if config.diagram_type == DiagramType.SERVICE_LAYER:
                if not (uml_class.stereotype in ["service", "repository"] or "service" in name.lower()):
                    continue
            elif config.diagram_type == DiagramType.DATA_MODEL:
                if not (uml_class.stereotype == "model" or "model" in name.lower() or "schema" in name.lower()):
                    continue
            elif config.diagram_type == DiagramType.FASTAPI_ARCHITECTURE:
                if not any(keyword in name.lower() for keyword in 
                          ["router", "endpoint", "service", "model", "schema", "dependency"]):
                    continue
            
            filtered[name] = uml_class
            
            # Respect max_classes limit
            if len(filtered) >= config.max_classes:
                break
        
        return filtered
    
    def _filter_relationships(self, relationships: List[UMLRelationship], 
                            filtered_classes: Dict[str, UMLClass], 
                            config: DiagramConfig) -> List[UMLRelationship]:
        """Filter relationships to only include those between filtered classes."""
        class_names = set(filtered_classes.keys())
        
        filtered = []
        for rel in relationships:
            # Include relationship only if both source and target are in filtered classes
            if rel.source in class_names and rel.target in class_names:
                filtered.append(rel)
        
        return filtered
    
    def _generate_header(self, config: DiagramConfig) -> List[str]:
        """Generate PlantUML header."""
        return [
            "@startuml",
            f"!theme plain",
            "skinparam classAttributeIconSize 0",
            "skinparam classFontSize 12",
            "skinparam packageStyle rectangle",
            ""
        ]
    
    def _generate_styling(self) -> List[str]:
        """Generate PlantUML styling directives."""
        lines = []
        
        # Color classes by stereotype
        for stereotype, color in self.stereotype_colors.items():
            lines.append(f"skinparam class{stereotype}BackgroundColor {self.color_scheme.get(stereotype.strip('<>'), '#FFFFFF')}")
            lines.append(f"skinparam class{stereotype}BorderColor {color}")
        
        return lines + [""]
    
    def _generate_package_groups(self, classes: Dict[str, UMLClass], config: DiagramConfig) -> List[str]:
        """Generate classes grouped by packages."""
        lines = []
        
        # Group classes by package
        packages = {}
        for name, uml_class in classes.items():
            package = uml_class.package
            if package not in packages:
                packages[package] = []
            packages[package].append((name, uml_class))
        
        # Generate package groups
        for package, package_classes in packages.items():
            lines.append(f"package {package} {{")
            
            for name, uml_class in package_classes:
                class_lines = self._generate_single_class(name, uml_class, config)
                lines.extend([f"  {line}" for line in class_lines])
            
            lines.append("}")
            lines.append("")
        
        return lines
    
    def _generate_classes(self, classes: Dict[str, UMLClass], config: DiagramConfig) -> List[str]:
        """Generate class definitions without package grouping."""
        lines = []
        
        for name, uml_class in classes.items():
            lines.extend(self._generate_single_class(name, uml_class, config))
            lines.append("")
        
        return lines
    
    def _generate_single_class(self, name: str, uml_class: UMLClass, config: DiagramConfig) -> List[str]:
        """Generate a single class definition."""
        lines = []
        
        # Class declaration
        class_type = "abstract class" if uml_class.is_abstract else "class"
        stereotype_part = f" <<{uml_class.stereotype}>>" if config.show_stereotypes and uml_class.stereotype else ""
        lines.append(f"{class_type} {name}{stereotype_part} {{")
        
        # Attributes
        if config.include_attributes and uml_class.attributes:
            for attr in uml_class.attributes:
                if config.include_private or not attr.name.startswith("_"):
                    lines.append(f"  {attr.to_plantuml()}")
        
        # Separator between attributes and methods
        if (config.include_attributes and uml_class.attributes and 
            config.include_methods and uml_class.methods):
            lines.append("  --")
        
        # Methods
        if config.include_methods and uml_class.methods:
            for method in uml_class.methods:
                if config.include_private or not method.name.startswith("_"):
                    # Simplify method display for overview diagrams
                    if config.diagram_type == DiagramType.CLASS_OVERVIEW:
                        method_display = f"  + {method.name}()"
                        if method.is_async:
                            method_display = f"  + async {method.name}()"
                        lines.append(method_display)
                    else:
                        lines.append(f"  {method.to_plantuml()}")
        
        lines.append("}")
        
        return lines
    
    def _generate_relationships(self, relationships: List[UMLRelationship]) -> List[str]:
        """Generate relationship definitions."""
        lines = []
        
        # Group relationships by type for better organization
        by_type = {}
        for rel in relationships:
            rel_type = rel.relationship_type
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append(rel)
        
        # Generate relationships in logical order
        type_order = [
            RelationshipType.INHERITANCE,
            RelationshipType.IMPLEMENTATION, 
            RelationshipType.COMPOSITION,
            RelationshipType.AGGREGATION,
            RelationshipType.ASSOCIATION,
            RelationshipType.DEPENDENCY
        ]
        
        for rel_type in type_order:
            if rel_type in by_type:
                lines.append(f"' {rel_type.value.title()} relationships")
                for rel in by_type[rel_type]:
                    lines.append(rel.to_plantuml())
                lines.append("")
        
        return lines
    
    def _generate_footer(self) -> List[str]:
        """Generate PlantUML footer."""
        return ["@enduml"]
    
    def generate_fastapi_sequence_diagram(self, analysis_result: Dict[str, Any], 
                                        endpoint_name: str) -> str:
        """Generate sequence diagram for FastAPI endpoint flow."""
        lines = [
            "@startuml",
            f"title {endpoint_name} Request Flow",
            "",
            "participant Client",
            "participant Router", 
            "participant Endpoint",
            "participant Service",
            "participant Repository",
            "participant Database",
            "",
            "Client -> Router : HTTP Request",
            "Router -> Endpoint : route()",
            "Endpoint -> Service : process()",
            "Service -> Repository : save()",
            "Repository -> Database : execute()",
            "Database --> Repository : result",
            "Repository --> Service : data",
            "Service --> Endpoint : response",
            "Endpoint --> Router : HTTP Response",
            "Router --> Client : JSON Response",
            "",
            "@enduml"
        ]
        
        return "\n".join(lines)
    
    def generate_component_diagram(self, analysis_result: Dict[str, Any]) -> str:
        """Generate component diagram showing high-level architecture."""
        lines = [
            "@startuml",
            "!include <C4/C4_Component>",
            "",
            "title FastAPI Application Architecture",
            "",
            "Container_Boundary(api, \"API Layer\") {",
            "  Component(router, \"Routers\", \"FastAPI\", \"HTTP endpoint routing\")",
            "  Component(middleware, \"Middleware\", \"FastAPI\", \"Request/response processing\")",
            "}",
            "",
            "Container_Boundary(service, \"Service Layer\") {",
            "  Component(services, \"Services\", \"Python\", \"Business logic\")",
            "  Component(deps, \"Dependencies\", \"FastAPI\", \"Dependency injection\")",
            "}",
            "",
            "Container_Boundary(data, \"Data Layer\") {",
            "  Component(models, \"Models\", \"Pydantic\", \"Data validation\")",
            "  Component(repo, \"Repositories\", \"Python\", \"Data access\")",
            "}",
            "",
            "Container_Boundary(external, \"External\") {",
            "  Component(db, \"Database\", \"Database\", \"Data storage\")",
            "  Component(confluence, \"Confluence\", \"Atlassian\", \"Documentation\")",
            "}",
            "",
            "Rel(router, services, \"calls\")",
            "Rel(services, models, \"validates\")",
            "Rel(services, repo, \"queries\")",
            "Rel(repo, db, \"persists\")",
            "Rel(services, confluence, \"publishes\")",
            "",
            "@enduml"
        ]
        
        return "\n".join(lines)


def create_diagram_configs() -> Dict[str, DiagramConfig]:
    """Create predefined diagram configurations for different use cases."""
    configs = {
        "overview": DiagramConfig(
            diagram_type=DiagramType.CLASS_OVERVIEW,
            include_methods=False,
            include_attributes=False,
            max_classes=15,
            layout_direction="left to right direction"
        ),
        
        "detailed": DiagramConfig(
            diagram_type=DiagramType.CLASS_DETAILED,
            include_methods=True,
            include_attributes=True,
            include_private=False,
            max_classes=10
        ),
        
        "services": DiagramConfig(
            diagram_type=DiagramType.SERVICE_LAYER,
            include_methods=True,
            include_attributes=False,
            focus_packages=["services"],
            max_classes=12
        ),
        
        "models": DiagramConfig(
            diagram_type=DiagramType.DATA_MODEL,
            include_methods=False,
            include_attributes=True,
            focus_packages=["models", "schemas"],
            max_classes=15
        ),
        
        "fastapi": DiagramConfig(
            diagram_type=DiagramType.FASTAPI_ARCHITECTURE,
            include_methods=True,
            include_attributes=False,
            show_stereotypes=True,
            color_by_type=True,
            max_classes=20
        )
    }
    
    return configs