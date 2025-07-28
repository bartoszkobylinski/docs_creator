"""
Enhanced UML relationship analyzer for generating comprehensive PlantUML diagrams.
Extends the base scanner with relationship detection for proper UML generation.
"""

import ast
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .models import DocumentationItem


class RelationshipType(Enum):
    """Types of relationships between classes/modules."""
    INHERITANCE = "inheritance"          # is-a (A extends B)
    COMPOSITION = "composition"          # has-a (A owns B)
    AGGREGATION = "aggregation"         # has-a (A uses B)
    DEPENDENCY = "dependency"           # uses (A depends on B)
    ASSOCIATION = "association"         # uses (A calls B methods)
    IMPLEMENTATION = "implementation"    # implements (A implements interface B)
    IMPORT = "import"                   # imports (A imports B)


@dataclass
class UMLRelationship:
    """Represents a relationship between two UML elements."""
    source: str                    # Source class/module name
    target: str                    # Target class/module name
    relationship_type: RelationshipType
    multiplicity: Optional[str] = None  # "1", "*", "0..1", etc.
    label: Optional[str] = None         # Relationship label
    stereotype: Optional[str] = None    # <<service>>, <<model>>, etc.
    
    def to_plantuml(self) -> str:
        """Convert relationship to PlantUML syntax."""
        arrows = {
            RelationshipType.INHERITANCE: "--|>",
            RelationshipType.COMPOSITION: "*--",
            RelationshipType.AGGREGATION: "o--",
            RelationshipType.DEPENDENCY: "..>",
            RelationshipType.ASSOCIATION: "-->",
            RelationshipType.IMPLEMENTATION: "..|>",
            RelationshipType.IMPORT: "..>"
        }
        
        arrow = arrows[self.relationship_type]
        label_part = f" : {self.label}" if self.label else ""
        multiplicity_part = f" \"{self.multiplicity}\"" if self.multiplicity else ""
        
        return f"{self.source} {arrow} {self.target}{multiplicity_part}{label_part}"


@dataclass 
class UMLClass:
    """Represents a class in UML with full relationship context."""
    name: str
    package: str
    stereotype: Optional[str] = None    # <<service>>, <<model>>, <<interface>>
    visibility: str = "public"          # public, private, protected
    is_abstract: bool = False
    attributes: List['UMLAttribute'] = None
    methods: List['UMLMethod'] = None
    relationships: List[UMLRelationship] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = []
        if self.methods is None:
            self.methods = []
        if self.relationships is None:
            self.relationships = []
    
    def to_plantuml(self) -> str:
        """Convert class to PlantUML class definition."""
        lines = []
        
        # Class declaration with stereotype
        class_type = "abstract class" if self.is_abstract else "class"
        stereotype_part = f" <<{self.stereotype}>>" if self.stereotype else ""
        lines.append(f"{class_type} {self.name}{stereotype_part} {{")
        
        # Attributes
        for attr in self.attributes:
            lines.append(f"  {attr.to_plantuml()}")
        
        if self.attributes and self.methods:
            lines.append("  --")  # Separator between attributes and methods
        
        # Methods
        for method in self.methods:
            lines.append(f"  {method.to_plantuml()}")
        
        lines.append("}")
        
        return "\n".join(lines)


@dataclass
class UMLAttribute:
    """UML class attribute with type and visibility."""
    name: str
    type_annotation: Optional[str] = None
    visibility: str = "public"          # +, -, #, ~
    is_static: bool = False
    default_value: Optional[str] = None
    
    def to_plantuml(self) -> str:
        """Convert to PlantUML attribute syntax."""
        visibility_map = {"public": "+", "private": "-", "protected": "#", "package": "~"}
        vis_symbol = visibility_map.get(self.visibility, "+")
        
        static_part = "{static} " if self.is_static else ""
        type_part = f" : {self.type_annotation}" if self.type_annotation else ""
        default_part = f" = {self.default_value}" if self.default_value else ""
        
        return f"{vis_symbol} {static_part}{self.name}{type_part}{default_part}"


@dataclass
class UMLMethod:
    """UML class method with parameters and return type."""
    name: str
    parameters: List[str] = None
    return_type: Optional[str] = None
    visibility: str = "public"
    is_static: bool = False
    is_abstract: bool = False
    is_async: bool = False
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
    
    def to_plantuml(self) -> str:
        """Convert to PlantUML method syntax."""
        visibility_map = {"public": "+", "private": "-", "protected": "#", "package": "~"}
        vis_symbol = visibility_map.get(self.visibility, "+")
        
        static_part = "{static} " if self.is_static else ""
        abstract_part = "{abstract} " if self.is_abstract else ""
        async_part = "async " if self.is_async else ""
        
        params_str = ", ".join(self.parameters)
        return_part = f" : {self.return_type}" if self.return_type else ""
        
        return f"{vis_symbol} {static_part}{abstract_part}{async_part}{self.name}({params_str}){return_part}"


class UMLAnalyzer:
    """Enhanced analyzer for extracting UML relationships from documentation items."""
    
    def __init__(self):
        self.classes: Dict[str, UMLClass] = {}
        self.relationships: List[UMLRelationship] = []
        self.imports: Dict[str, Set[str]] = {}  # module -> imported modules
        self.type_registry: Dict[str, str] = {}  # type_name -> module
    
    def analyze_documentation_items(self, items: List[DocumentationItem]) -> Dict[str, Any]:
        """Analyze documentation items and extract UML relationships."""
        # Phase 1: Build class registry and basic info
        self._build_class_registry(items)
        
        # Phase 2: Analyze relationships
        self._analyze_inheritance_relationships(items)
        self._analyze_composition_relationships(items)
        self._analyze_dependency_relationships(items)
        self._analyze_association_relationships(items)
        
        # Phase 3: Enhance with FastAPI-specific patterns
        self._analyze_fastapi_patterns(items)
        
        return {
            "classes": self.classes,
            "relationships": self.relationships,
            "imports": self.imports,
            "type_registry": self.type_registry
        }
    
    def _build_class_registry(self, items: List[DocumentationItem]):
        """Build registry of all classes with their attributes and methods."""
        current_class = None
        
        for item in items:
            if item.method == "class":
                # Create new UML class
                stereotype = self._determine_class_stereotype(item)
                uml_class = UMLClass(
                    name=item.qualname,
                    package=item.module,
                    stereotype=stereotype,
                    is_abstract=self._is_abstract_class(item)
                )
                self.classes[item.qualname] = uml_class
                current_class = uml_class
                
            elif item.method in ["function", "async_function"] and current_class:
                # Add method to current class
                method = self._create_uml_method(item)
                current_class.methods.append(method)
                
            elif item.method == "property" and current_class:
                # Add property as attribute
                attr = self._create_uml_attribute_from_property(item)
                current_class.attributes.append(attr)
    
    def _analyze_inheritance_relationships(self, items: List[DocumentationItem]):
        """Analyze inheritance relationships from class signatures."""
        for item in items:
            if item.method == "class" and "inherits=" in (item.signature or ""):
                # Extract base classes from signature
                base_classes = self._extract_base_classes(item.signature)
                for base_class in base_classes:
                    relationship = UMLRelationship(
                        source=item.qualname,
                        target=base_class,
                        relationship_type=RelationshipType.INHERITANCE
                    )
                    self.relationships.append(relationship)
    
    def _analyze_composition_relationships(self, items: List[DocumentationItem]):
        """Analyze composition relationships from constructor parameters and field types."""
        for item in items:
            if item.method == "function" and item.qualname.endswith(".__init__"):
                # Analyze constructor parameters for composition
                class_name = item.qualname[:-9]  # Remove .__init__
                for param_name, param_type in (item.param_types or {}).items():
                    if self._is_custom_type(param_type):
                        relationship = UMLRelationship(
                            source=class_name,
                            target=param_type,
                            relationship_type=RelationshipType.COMPOSITION,
                            label=param_name
                        )
                        self.relationships.append(relationship)
    
    def _analyze_dependency_relationships(self, items: List[DocumentationItem]):
        """Analyze dependency relationships from FastAPI dependencies and imports."""
        for item in items:
            # FastAPI dependencies
            for dep in (item.dependencies or []):
                if dep != item.qualname:  # Avoid self-references
                    relationship = UMLRelationship(
                        source=item.qualname,
                        target=dep,
                        relationship_type=RelationshipType.DEPENDENCY,
                        stereotype="depends"
                    )
                    self.relationships.append(relationship)
    
    def _analyze_association_relationships(self, items: List[DocumentationItem]):
        """Analyze association relationships from method parameters and return types."""
        for item in items:
            if item.method in ["function", "async_function"]:
                # Check parameter types for associations
                for param_name, param_type in (item.param_types or {}).items():
                    if self._is_custom_type(param_type) and not self._is_composition(item, param_type):
                        relationship = UMLRelationship(
                            source=self._get_containing_class(item.qualname) or item.qualname,
                            target=param_type,
                            relationship_type=RelationshipType.ASSOCIATION,
                            label=f"uses({param_name})"
                        )
                        self.relationships.append(relationship)
                
                # Check return type for associations
                if item.return_type and self._is_custom_type(item.return_type):
                    relationship = UMLRelationship(
                        source=self._get_containing_class(item.qualname) or item.qualname,
                        target=item.return_type,
                        relationship_type=RelationshipType.ASSOCIATION,
                        label="returns"
                    )
                    self.relationships.append(relationship)
    
    def _analyze_fastapi_patterns(self, items: List[DocumentationItem]):
        """Analyze FastAPI-specific patterns for enhanced UML context."""
        # Group endpoints by router
        routers = {}
        for item in items:
            if hasattr(item, 'tags') and item.tags:
                for tag in item.tags:
                    if tag not in routers:
                        routers[tag] = []
                    routers[tag].append(item.qualname)
        
        # Add router relationships
        for router_name, endpoints in routers.items():
            for endpoint in endpoints:
                relationship = UMLRelationship(
                    source=router_name + "Router",
                    target=endpoint,
                    relationship_type=RelationshipType.COMPOSITION,
                    stereotype="router"
                )
                self.relationships.append(relationship)
    
    def _determine_class_stereotype(self, item: DocumentationItem) -> Optional[str]:
        """Determine appropriate stereotype for a class."""
        qualname = item.qualname.lower()
        
        if "service" in qualname:
            return "service"
        elif "model" in qualname or "schema" in qualname:
            return "model"
        elif "repository" in qualname or "dao" in qualname:
            return "repository" 
        elif "controller" in qualname or "router" in qualname:
            return "controller"
        elif "config" in qualname:
            return "configuration"
        elif any(base in (item.signature or "") for base in ["BaseModel", "Schema"]):
            return "model"
        elif "Protocol" in (item.signature or ""):
            return "interface"
        
        return None
    
    def _is_abstract_class(self, item: DocumentationItem) -> bool:
        """Check if class is abstract."""
        return "ABC" in (item.signature or "") or "abstract" in (item.docstring or "").lower()
    
    def _create_uml_method(self, item: DocumentationItem) -> UMLMethod:
        """Create UML method from documentation item."""
        method_name = item.qualname.split(".")[-1]
        
        # Determine visibility
        visibility = "private" if method_name.startswith("_") else "public"
        
        # Build parameter list
        parameters = []
        for param_name, param_type in (item.param_types or {}).items():
            if param_name != "self":  # Skip self parameter
                param_str = f"{param_name}: {param_type}" if param_type else param_name
                parameters.append(param_str)
        
        return UMLMethod(
            name=method_name,
            parameters=parameters,
            return_type=item.return_type,
            visibility=visibility,
            is_static="staticmethod" in (item.signature or ""),
            is_async=item.method == "async_function"
        )
    
    def _create_uml_attribute_from_property(self, item: DocumentationItem) -> UMLAttribute:
        """Create UML attribute from property documentation item."""
        attr_name = item.qualname.split(".")[-1]
        visibility = "private" if attr_name.startswith("_") else "public"
        
        return UMLAttribute(
            name=attr_name,
            type_annotation=item.return_type,
            visibility=visibility
        )
    
    def _extract_base_classes(self, signature: str) -> List[str]:
        """Extract base class names from class signature."""
        if "inherits=(" not in signature:
            return []
        
        start = signature.find("inherits=(") + 10
        end = signature.find(")", start)
        if end == -1:
            return []
        
        base_classes_str = signature[start:end]
        return [cls.strip() for cls in base_classes_str.split(",") if cls.strip()]
    
    def _is_custom_type(self, type_name: str) -> bool:
        """Check if type is a custom class (not built-in)."""
        if not type_name:
            return False
        
        # Remove generic type parameters
        base_type = type_name.split("[")[0]
        
        # Skip built-in types
        builtin_types = {"str", "int", "float", "bool", "list", "dict", "tuple", "set", 
                        "List", "Dict", "Tuple", "Set", "Optional", "Union", "Any"}
        
        return base_type not in builtin_types
    
    def _is_composition(self, item: DocumentationItem, param_type: str) -> bool:
        """Check if parameter represents composition (stored as instance variable)."""
        # This would require more sophisticated analysis of the method body
        # For now, assume constructor parameters are composition
        return item.qualname.endswith(".__init__")
    
    def _get_containing_class(self, qualname: str) -> Optional[str]:
        """Get the containing class name from a method qualname."""
        parts = qualname.split(".")
        if len(parts) > 1:
            return ".".join(parts[:-1])
        return None