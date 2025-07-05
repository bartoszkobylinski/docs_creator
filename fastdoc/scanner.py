# fastdoc/scanner.py

import ast
import os
import re
from fastdoc.models import DocItem

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}

class FastAPIScanner(ast.NodeVisitor):
    """
    Walks Python modules and gathers documentation items for FastAPI:
      - Module-level docstrings (in visit_Module)
      - Module-level FastAPI() metadata (in visit_Assign)
      - Class docstrings (visit_ClassDef)
      - Both sync & async function docstrings (visit_FunctionDef / visit_AsyncFunctionDef)
      - FastAPI endpoint decorators (@*.get/post/…) extracting path, summary, description
    """

    def __init__(self, filename: str):
        self.filename = filename
        self.module = os.path.splitext(os.path.basename(filename))[0]
        self.items: list[DocItem] = []
        self.module_docstring_processed = False  # Track if we've captured module docstring
        # Read file once for snippets
        with open(filename, "r") as f:
            self.source = f.read()

    def visit_Module(self, node: ast.Module):
        """Capture module-level docstring if present."""
        if not self.module_docstring_processed:
            module_doc = ast.get_docstring(node)
            if module_doc:
                # Calculate coverage score for module
                module_data = {
                    'method': 'MODULE',
                    'docstring': module_doc
                }
                coverage_score, quality_score, issues = self._calculate_coverage_score(module_data)
                
                self.items.append(DocItem(
                    module=self.module,
                    qualname="<module>",
                    path="",
                    method="MODULE",
                    signature="",
                    docstring=module_doc,
                    description=None,
                    first_lines="",
                    lineno=1,
                    coverage_score=coverage_score,
                    quality_score=quality_score,
                    completeness_issues=issues
                ))
            self.module_docstring_processed = True
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # Detect "app = FastAPI(...)" and record each keyword as METADATA
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "app"
            and isinstance(node.value, ast.Call)
            and (
                (isinstance(node.value.func, ast.Name) and node.value.func.id == "FastAPI")
                or (isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "FastAPI")
            )
        ):
            for kw in node.value.keywords:
                # Only record simple constant values here
                if isinstance(kw.value, ast.Constant):
                    self.items.append(DocItem(
                        module=self.module,
                        qualname="app",
                        path="",
                        method="METADATA",
                        signature=kw.arg,                   # e.g. "title", "description", "openapi_tags"
                        docstring=str(kw.value.value),     # the literal value
                        description=None,
                        first_lines="",
                        lineno=node.lineno
                    ))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Record class-level docstring
        class_doc = ast.get_docstring(node)
        
        # Check if this is a Pydantic BaseModel
        is_pydantic_model = self._is_pydantic_model(node)
        method_type = "PYDANTIC_MODEL" if is_pydantic_model else "CLASS"
        
        # For Pydantic models, also extract field information
        pydantic_fields = {}
        if is_pydantic_model:
            pydantic_fields = self._extract_pydantic_fields(node)
        
        # Calculate coverage score
        class_data = {
            'method': method_type,
            'docstring': class_doc
        }
        coverage_score, quality_score, issues = self._calculate_coverage_score(class_data)
        
        self.items.append(DocItem(
            module=self.module,
            qualname=node.name,
            path="",
            method=method_type,
            signature="",
            docstring=class_doc,
            description=None,
            first_lines="",
            lineno=node.lineno,
            param_types=pydantic_fields,  # Reuse param_types for Pydantic field types
            coverage_score=coverage_score,
            quality_score=quality_score,
            completeness_issues=issues
        ))
        self.generic_visit(node)

    def _is_pydantic_model(self, node: ast.ClassDef) -> bool:
        """Check if a class inherits from Pydantic BaseModel."""
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in ('BaseModel', 'Model'):
                    return True
            elif isinstance(base, ast.Attribute):
                if base.attr in ('BaseModel', 'Model'):
                    return True
        return False

    def _extract_pydantic_fields(self, node: ast.ClassDef) -> dict[str, str]:
        """Extract field names and types from a Pydantic model."""
        fields = {}
        
        for stmt in node.body:
            # Handle annotated assignments: field_name: Type = default_value
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                try:
                    field_type = ast.unparse(stmt.annotation)
                    fields[field_name] = field_type
                except Exception:
                    fields[field_name] = "<complex_type>"
            
            # Handle regular assignments with Field() calls
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id
                        # Try to infer type from Field() call or default value
                        if isinstance(stmt.value, ast.Call):
                            # Could be Field(default=...) or similar
                            fields[field_name] = "Any"
                        else:
                            fields[field_name] = "Any"
        
        return fields

    def _parse_docstring_params(self, docstring: str) -> tuple[list[str], bool]:
        """
        Parse docstring to extract parameter names and check for return documentation.
        Supports Google, Numpy, and basic Sphinx styles.
        """
        if not docstring:
            return [], False
        
        documented_params = []
        
        # Try Google/Numpy style with args section parsing
        args_section_match = re.search(
            r'(?:Args?|Arguments?|Parameters?):\s*\n(.*?)(?=\n\s*(?:Returns?|Return|Yields?|Yield|Raises?|Note|Example)s?:|$)',
            docstring, 
            re.MULTILINE | re.IGNORECASE | re.DOTALL
        )
        
        if args_section_match:
            param_block = args_section_match.group(1)
            # Look for lines that start with parameter names followed by colon
            # Only capture lines that are indented (parameter descriptions)
            param_lines = re.findall(r'^\s+(\w+)(?:\s*\([^)]*\))?\s*:', param_block, re.MULTILINE)
            documented_params.extend(param_lines)
        
        # Try Sphinx style if no Google/Numpy style found
        if not documented_params:
            documented_params = re.findall(r':param\s+(\w+):', docstring)
        
        # Check for return documentation
        has_return_doc = bool(re.search(
            r'(?:Returns?|Return|Yields?|Yield):', 
            docstring, 
            re.IGNORECASE
        )) or bool(re.search(r':returns?:', docstring, re.IGNORECASE))
        
        return documented_params, has_return_doc

    def _extract_function_params(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        """Extract actual parameter names from function definition."""
        params = []
        
        # Regular arguments
        for arg in node.args.args:
            if arg.arg != 'self':  # Skip 'self' parameter
                params.append(arg.arg)
        
        # *args
        if node.args.vararg:
            params.append(f"*{node.args.vararg.arg}")
        
        # **kwargs  
        if node.args.kwarg:
            params.append(f"**{node.args.kwarg.arg}")
        
        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            params.append(arg.arg)
            
        return params

    def _extract_type_hints(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[dict[str, str], str | None, bool]:
        """Extract type hints from function definition."""
        param_types = {}
        return_type = None
        has_any_hints = False
        
        # Extract parameter type hints
        for arg in node.args.args:
            if arg.annotation:
                has_any_hints = True
                try:
                    type_str = ast.unparse(arg.annotation)
                    param_types[arg.arg] = type_str
                except Exception:
                    param_types[arg.arg] = "<complex_type>"
        
        # Extract keyword-only parameter type hints
        for arg in node.args.kwonlyargs:
            if arg.annotation:
                has_any_hints = True
                try:
                    type_str = ast.unparse(arg.annotation)
                    param_types[arg.arg] = type_str
                except Exception:
                    param_types[arg.arg] = "<complex_type>"
        
        # Extract *args type hint
        if node.args.vararg and node.args.vararg.annotation:
            has_any_hints = True
            try:
                type_str = ast.unparse(node.args.vararg.annotation)
                param_types[f"*{node.args.vararg.arg}"] = type_str
            except Exception:
                param_types[f"*{node.args.vararg.arg}"] = "<complex_type>"
        
        # Extract **kwargs type hint
        if node.args.kwarg and node.args.kwarg.annotation:
            has_any_hints = True
            try:
                type_str = ast.unparse(node.args.kwarg.annotation)
                param_types[f"**{node.args.kwarg.arg}"] = type_str
            except Exception:
                param_types[f"**{node.args.kwarg.arg}"] = "<complex_type>"
        
        # Extract return type hint
        if node.returns:
            has_any_hints = True
            try:
                return_type = ast.unparse(node.returns)
            except Exception:
                return_type = "<complex_type>"
        
        return param_types, return_type, has_any_hints

    def _calculate_coverage_score(self, item_data: dict) -> tuple[float, float, list[str]]:
        """
        Calculate coverage and quality scores for a documentation item.
        Returns (coverage_score, quality_score, issues_list)
        """
        issues = []
        coverage_points = 0
        quality_points = 0
        max_coverage = 0
        max_quality = 0
        
        method = item_data.get('method', '')
        docstring = item_data.get('docstring')
        actual_params = item_data.get('actual_params', [])
        missing_params = item_data.get('missing_params', [])
        has_return_doc = item_data.get('has_return_doc', False)
        has_type_hints = item_data.get('has_type_hints', False)
        return_type = item_data.get('return_type')
        
        if method in ['FUNCTION', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            # Coverage scoring for functions and endpoints
            max_coverage = 100
            max_quality = 100
            
            # Basic docstring presence (30 points)
            if docstring:
                coverage_points += 30
            else:
                issues.append("Missing docstring")
            
            # Parameter documentation (40 points)
            if actual_params:
                param_coverage = (len(actual_params) - len(missing_params)) / len(actual_params)
                coverage_points += int(40 * param_coverage)
                if missing_params:
                    issues.append(f"Missing parameter docs: {missing_params}")
            else:
                coverage_points += 40  # No params to document
            
            # Return documentation (20 points)
            if return_type and return_type != "None":
                if has_return_doc:
                    coverage_points += 20
                else:
                    issues.append("Missing return documentation")
            else:
                coverage_points += 20  # No return to document
            
            # Type hints presence (10 points)
            if has_type_hints:
                coverage_points += 10
            else:
                issues.append("Missing type hints")
            
            # Quality scoring
            if docstring:
                # Docstring length and detail (50 points)
                if len(docstring) > 100:
                    quality_points += 50
                elif len(docstring) > 50:
                    quality_points += 30
                elif len(docstring) > 20:
                    quality_points += 15
                
                # Well-formatted parameters (30 points)
                if not missing_params and actual_params:
                    quality_points += 30
                elif len(missing_params) < len(actual_params) / 2:
                    quality_points += 15
                
                # Return documentation quality (20 points)
                if has_return_doc:
                    quality_points += 20
        
        elif method == 'PYDANTIC_MODEL':
            # Coverage scoring for Pydantic models
            max_coverage = 100
            max_quality = 100
            
            # Basic docstring presence (60 points)
            if docstring:
                coverage_points += 60
            else:
                issues.append("Missing model docstring")
            
            # Field documentation would go here (40 points)
            # For now, give full points if model has docstring
            if docstring:
                coverage_points += 40
            
            # Quality scoring
            if docstring:
                if len(docstring) > 50:
                    quality_points += 70
                elif len(docstring) > 20:
                    quality_points += 40
                quality_points += 30  # Base quality for having docstring
        
        elif method == 'CLASS':
            # Coverage scoring for regular classes
            max_coverage = 100
            max_quality = 100
            
            # Basic docstring presence (100 points)
            if docstring:
                coverage_points += 100
            else:
                issues.append("Missing class docstring")
            
            # Quality scoring
            if docstring:
                if len(docstring) > 50:
                    quality_points += 100
                elif len(docstring) > 20:
                    quality_points += 60
                else:
                    quality_points += 30
        
        elif method == 'MODULE':
            # Coverage scoring for modules
            max_coverage = 100
            max_quality = 100
            
            if docstring:
                coverage_points += 100
                quality_points += 100
            else:
                issues.append("Missing module docstring")
        
        # Calculate final scores as percentages
        coverage_score = (coverage_points / max_coverage * 100) if max_coverage > 0 else 0
        quality_score = (quality_points / max_quality * 100) if max_quality > 0 else 0
        
        return min(coverage_score, 100), min(quality_score, 100), issues

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        """Common logic for both sync & async functions."""
        func_doc = ast.get_docstring(node)
        sig = ast.unparse(node.args)

        # Source snippet: lines 2–6 of the function
        segment = ast.get_source_segment(self.source, node) or ""
        snippet = "\n".join(segment.splitlines()[1:6])

        # Parse docstring for parameter validation
        documented_params, has_return_doc = self._parse_docstring_params(func_doc)
        actual_params = self._extract_function_params(node)
        
        # Extract type hints
        param_types, return_type, has_type_hints = self._extract_type_hints(node)
        
        # Calculate missing and extra parameters
        missing_params = [p for p in actual_params if p not in documented_params and not p.startswith('*')]
        extra_params = [p for p in documented_params if p not in actual_params]

        # Calculate coverage and quality scores
        item_data = {
            'method': 'FUNCTION',
            'docstring': func_doc,
            'actual_params': actual_params,
            'missing_params': missing_params,
            'has_return_doc': has_return_doc,
            'has_type_hints': has_type_hints,
            'return_type': return_type
        }
        coverage_score, quality_score, issues = self._calculate_coverage_score(item_data)

        # 1) Record every function/method with enhanced validation info
        self.items.append(DocItem(
            module=self.module,
            qualname=node.name,
            path="",
            method="FUNCTION",
            signature=sig,
            docstring=func_doc,
            description=None,
            first_lines=snippet,
            lineno=node.lineno,
            documented_params=documented_params,
            actual_params=actual_params,
            missing_params=missing_params,
            extra_params=extra_params,
            has_return_doc=has_return_doc,
            param_types=param_types,
            return_type=return_type,
            has_type_hints=has_type_hints,
            coverage_score=coverage_score,
            quality_score=quality_score,
            completeness_issues=issues
        ))

        # 2) Now detect FastAPI HTTP decorators
        for deco in node.decorator_list:
            if isinstance(deco, ast.Call) and hasattr(deco.func, "attr"):
                http = deco.func.attr.upper()
                if http in HTTP_METHODS:
                    # extract path (first Constant arg)
                    path = ""
                    for arg in deco.args:
                        if isinstance(arg, ast.Constant):
                            path = arg.value
                            break

                    # extract summary & description, preferring description
                    summary = None
                    desc = None
                    for kw in deco.keywords:
                        if kw.arg == "summary" and isinstance(kw.value, ast.Constant):
                            summary = kw.value.value
                        if kw.arg == "description" and isinstance(kw.value, ast.Constant):
                            desc = kw.value.value

                    # Calculate coverage for endpoint
                    endpoint_data = {
                        'method': http,
                        'docstring': func_doc,
                        'actual_params': actual_params,
                        'missing_params': missing_params,
                        'has_return_doc': has_return_doc,
                        'has_type_hints': has_type_hints,
                        'return_type': return_type
                    }
                    endpoint_coverage, endpoint_quality, endpoint_issues = self._calculate_coverage_score(endpoint_data)

                    self.items.append(DocItem(
                        module=self.module,
                        qualname=node.name,
                        path=path,
                        method=http,
                        signature=sig,
                        docstring=func_doc,
                        description=desc if desc is not None else summary,
                        first_lines=snippet,
                        lineno=node.lineno,
                        documented_params=documented_params,
                        actual_params=actual_params,
                        missing_params=missing_params,
                        extra_params=extra_params,
                        has_return_doc=has_return_doc,
                        param_types=param_types,
                        return_type=return_type,
                        has_type_hints=has_type_hints,
                        coverage_score=endpoint_coverage,
                        quality_score=endpoint_quality,
                        completeness_issues=endpoint_issues
                    ))

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_function(node)
        self.generic_visit(node)


def scan_file(path: str):
    """
    Parse `path`, walk its AST with FastAPIScanner, and return List[DocItem].
    """
    source = open(path, "r").read()
    tree = ast.parse(source)
    scanner = FastAPIScanner(path)
    scanner.visit(tree)
    return scanner.items
