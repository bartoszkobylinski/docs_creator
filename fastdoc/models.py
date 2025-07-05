from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class DocItem:
    module: str
    qualname: str
    path: str  # API path for endpoints (e.g., "/users/me")
    method: str
    signature: str
    docstring: Optional[str]
    description: Optional[str]
    first_lines: str
    lineno: int
    file_path: str = ""  # Actual file path
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
    # Docstring format validation
    docstring_style: Optional[str] = None
    style_issues: List[str] = field(default_factory=list)
    # Exception documentation tracking
    documented_exceptions: List[str] = field(default_factory=list)
    raised_exceptions: List[str] = field(default_factory=list)
    has_exception_doc: bool = False
    # FastAPI response model analysis
    response_model: Optional[str] = None
    status_codes: List[str] = field(default_factory=list)
    response_description: Optional[str] = None
    # FastAPI dependency tracking
    dependencies: List[str] = field(default_factory=list)
    dependency_docs: Dict[str, str] = field(default_factory=dict)
    # FastAPI tags and grouping
    tags: List[str] = field(default_factory=list)
    operation_id: Optional[str] = None
    summary_from_decorator: Optional[str] = None
    # Advanced quality metrics
    docstring_length: int = 0
    complexity_score: float = 0.0
    maintainability_score: float = 0.0
    api_completeness_score: float = 0.0

