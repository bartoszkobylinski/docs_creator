from dataclasses import dataclass, field
from typing import Optional, Dict

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

