from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class DocItem:
    module: str
    qualname: str
    path: str
    method: str
    signature: str
    docstring: Optional[str]
    description: Optional[str]
    first_lines: str
    lineno: int
    # Enhanced fields for parameter validation
    documented_params: List[str] = field(default_factory=list)
    actual_params: List[str] = field(default_factory=list)
    missing_params: List[str] = field(default_factory=list)
    extra_params: List[str] = field(default_factory=list)
    has_return_doc: bool = False
    # Type hints analysis
    param_types: Dict[str, str] = field(default_factory=dict)
    return_type: Optional[str] = None
    has_type_hints: bool = False
    # Coverage scoring
    coverage_score: float = 0.0
    quality_score: float = 0.0
    completeness_issues: List[str] = field(default_factory=list)

