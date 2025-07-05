# fastdoc/scanner.py

import ast
import os
import re
from fastdoc.models import DocItem

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"}
WEBSOCKET_METHODS = {"WEBSOCKET"}

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
        self.class_stack = []  # Track nested class hierarchy
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
                    file_path=self.filename,
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
                        lineno=node.lineno,
                        file_path=self.filename
                    ))
        
        # Detect "router = APIRouter(...)" and record router configuration
        elif (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and (
                (isinstance(node.value.func, ast.Name) and node.value.func.id == "APIRouter")
                or (isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "APIRouter")
            )
        ):
            router_name = node.targets[0].id
            for kw in node.value.keywords:
                if isinstance(kw.value, ast.Constant):
                    self.items.append(DocItem(
                        module=self.module,
                        qualname=router_name,
                        path="",
                        method="ROUTER_METADATA",
                        signature=kw.arg,
                        docstring=str(kw.value.value),
                        description=None,
                        first_lines="",
                        lineno=node.lineno,
                        file_path=self.filename
                    ))
        
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Detect FastAPI method calls like app.add_middleware(), app.include_router()"""
        if isinstance(node.func, ast.Attribute):
            # Check for middleware additions
            if node.func.attr == "add_middleware":
                middleware_info = self._extract_middleware_info(node)
                if middleware_info:
                    self.items.append(DocItem(
                        module=self.module,
                        qualname=f"{middleware_info['app_name']}.middleware",
                        path="",
                        method="MIDDLEWARE",
                        signature=middleware_info['middleware_class'],
                        docstring=None,
                        description=f"Middleware: {middleware_info['middleware_class']}",
                        first_lines="",
                        lineno=node.lineno,
                        file_path=self.filename
                    ))
            
            # Check for router inclusions
            elif node.func.attr == "include_router":
                router_info = self._extract_router_inclusion_info(node)
                if router_info:
                    self.items.append(DocItem(
                        module=self.module,
                        qualname=f"{router_info['app_name']}.router_inclusion",
                        path=router_info.get('prefix', ''),
                        method="ROUTER_INCLUSION",
                        signature=router_info['router_name'],
                        docstring=None,
                        description=f"Router inclusion: {router_info['router_name']}",
                        first_lines="",
                        lineno=node.lineno,
                        file_path=self.filename,
                        tags=router_info.get('tags', [])
                    ))
        
        self.generic_visit(node)

    def _extract_middleware_info(self, node: ast.Call) -> dict:
        """Extract middleware configuration from add_middleware call"""
        info = {}
        
        # Get app name
        if isinstance(node.func.value, ast.Name):
            info['app_name'] = node.func.value.id
        
        # Get middleware class (first argument)
        if node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Name):
                info['middleware_class'] = first_arg.id
            elif isinstance(first_arg, ast.Attribute):
                info['middleware_class'] = f"{ast.unparse(first_arg.value)}.{first_arg.attr}"
            else:
                try:
                    info['middleware_class'] = ast.unparse(first_arg)
                except:
                    info['middleware_class'] = "<complex_middleware>"
        
        return info if 'middleware_class' in info else None

    def _extract_router_inclusion_info(self, node: ast.Call) -> dict:
        """Extract router inclusion configuration"""
        info = {}
        
        # Get app name
        if isinstance(node.func.value, ast.Name):
            info['app_name'] = node.func.value.id
        
        # Get router name (first argument)
        if node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Attribute):
                info['router_name'] = f"{ast.unparse(first_arg.value)}.{first_arg.attr}"
            elif isinstance(first_arg, ast.Name):
                info['router_name'] = first_arg.id
            else:
                try:
                    info['router_name'] = ast.unparse(first_arg)
                except:
                    info['router_name'] = "<complex_router>"
        
        # Extract keywords like prefix, tags
        for kw in node.keywords:
            if kw.arg == 'prefix' and isinstance(kw.value, ast.Constant):
                info['prefix'] = kw.value.value
            elif kw.arg == 'tags' and isinstance(kw.value, ast.List):
                tags = []
                for tag in kw.value.elts:
                    if isinstance(tag, ast.Constant):
                        tags.append(tag.value)
                info['tags'] = tags
        
        return info if 'router_name' in info else None

    def visit_ClassDef(self, node: ast.ClassDef):
        # Build qualified name for nested classes
        if self.class_stack:
            qualified_name = ".".join(self.class_stack) + "." + node.name
        else:
            qualified_name = node.name
        
        # Add current class to stack for nested processing
        self.class_stack.append(node.name)
        
        # Record class-level docstring
        class_doc = ast.get_docstring(node)
        
        # Check if this is a Pydantic BaseModel
        is_pydantic_model = self._is_pydantic_model(node)
        method_type = "PYDANTIC_MODEL" if is_pydantic_model else "CLASS"
        
        # Determine nesting level and type
        nesting_info = self._analyze_class_nesting(node)
        
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
            qualname=qualified_name,
            path="",
            method=method_type,
            signature=nesting_info,  # Store nesting info in signature field
            docstring=class_doc,
            description=None,
            first_lines="",
            lineno=node.lineno,
            file_path=self.filename,
            param_types=pydantic_fields,  # Reuse param_types for Pydantic field types
            coverage_score=coverage_score,
            quality_score=quality_score,
            completeness_issues=issues
        ))
        
        # Process nested classes (like Config classes in Pydantic models)
        for nested_node in node.body:
            if isinstance(nested_node, ast.ClassDef):
                # Special handling for Config classes in Pydantic models
                if nested_node.name == "Config" and is_pydantic_model:
                    config_info = self._extract_pydantic_config(nested_node)
                    if config_info:
                        self.items.append(DocItem(
                            module=self.module,
                            qualname=qualified_name + ".Config",
                            path="",
                            method="PYDANTIC_CONFIG",
                            signature=", ".join(f"{k}={v}" for k, v in config_info.items()),
                            docstring=ast.get_docstring(nested_node),
                            description=None,
                            first_lines="",
                            lineno=nested_node.lineno,
                            file_path=self.filename
                        ))
        
        # Visit nested content
        self.generic_visit(node)
        
        # Remove current class from stack when done
        self.class_stack.pop()

    def _analyze_class_nesting(self, node: ast.ClassDef) -> str:
        """Analyze class nesting level and inheritance."""
        nesting_level = len(self.class_stack) - 1  # -1 because we already added current class
        
        # Build inheritance info
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(f"{ast.unparse(base.value)}.{base.attr}")
            else:
                try:
                    base_classes.append(ast.unparse(base))
                except:
                    base_classes.append("<complex_base>")
        
        # Create signature with nesting and inheritance info
        parts = []
        if nesting_level > 0:
            parts.append(f"nested_level={nesting_level}")
        if base_classes:
            parts.append(f"inherits=({', '.join(base_classes)})")
        
        return " | ".join(parts) if parts else ""

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

    def _extract_pydantic_config(self, node: ast.ClassDef) -> dict[str, str]:
        """Extract configuration from Pydantic Config class."""
        config_info = {}
        
        for stmt in node.body:
            # Handle simple assignments like orm_mode = True
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Constant):
                        config_info[target.id] = str(stmt.value.value)
                    elif isinstance(target, ast.Name):
                        try:
                            config_info[target.id] = ast.unparse(stmt.value)
                        except:
                            config_info[target.id] = "<complex_value>"
        
        return config_info

    def _extract_documented_exceptions(self, docstring: str) -> tuple[list[str], bool]:
        """
        Extract documented exceptions from docstring.
        Returns (exception_list, has_exception_documentation)
        """
        if not docstring:
            return [], False
        
        documented_exceptions = []
        
        # Google style: Raises: section
        google_match = re.search(
            r'(?:Raises?|Raise):\s*\n((?:\s+.*\n?)*?)(?=\n\s*\w+:|$)',
            docstring, 
            re.MULTILINE | re.IGNORECASE
        )
        if google_match:
            raises_section = google_match.group(1)
            # Extract exception names from lines like "ValueError: Description"
            exceptions = re.findall(r'^\s+(\w+(?:\.\w+)*(?:Error|Exception|\w+))(?:\s*:|\s+)', raises_section, re.MULTILINE)
            documented_exceptions.extend(exceptions)
        
        # NumPy style: Raises section with underline
        numpy_match = re.search(
            r'Raises?\s*\n\s*[-=]+\s*\n(.*?)(?=\n\s*\w+\s*\n\s*[-=]+|\Z)',
            docstring,
            re.MULTILINE | re.IGNORECASE | re.DOTALL
        )
        if numpy_match:
            raises_section = numpy_match.group(1)
            # Extract exception names from lines (first word on each line)
            exceptions = re.findall(r'^\s+(\w+(?:Error|Exception))', raises_section, re.MULTILINE)
            documented_exceptions.extend(exceptions)
        
        # Sphinx style: :raises ExceptionType:
        sphinx_exceptions = re.findall(r':raises?\s+(\w+(?:\.\w+)*(?:Error|Exception|\w+)):', docstring)
        documented_exceptions.extend(sphinx_exceptions)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_exceptions = []
        for exc in documented_exceptions:
            if exc not in seen:
                seen.add(exc)
                unique_exceptions.append(exc)
        
        has_exception_doc = len(unique_exceptions) > 0
        
        return unique_exceptions, has_exception_doc

    def _extract_raised_exceptions(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        """
        Extract exceptions that are actually raised in the function body.
        """
        raised_exceptions = []
        
        class ExceptionVisitor(ast.NodeVisitor):
            def visit_Raise(self, node):
                if node.exc:
                    if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                        # Direct exception like raise ValueError()
                        raised_exceptions.append(node.exc.func.id)
                    elif isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Attribute):
                        # Module exception like raise custom.MyError()
                        raised_exceptions.append(node.exc.func.attr)
                    elif isinstance(node.exc, ast.Name):
                        # Re-raising like raise existing_exception
                        raised_exceptions.append(node.exc.id)
                    elif isinstance(node.exc, ast.Attribute):
                        # Module exception like raise custom.MyError
                        raised_exceptions.append(node.exc.attr)
                self.generic_visit(node)
        
        visitor = ExceptionVisitor()
        visitor.visit(node)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_exceptions = []
        for exc in raised_exceptions:
            if exc not in seen:
                seen.add(exc)
                unique_exceptions.append(exc)
        
        return unique_exceptions

    def _extract_dependencies(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[list[str], dict[str, str]]:
        """
        Extract FastAPI dependencies from function parameters.
        Returns (dependency_list, dependency_docs)
        """
        dependencies = []
        dependency_docs = {}
        
        # Check function parameters for Depends() calls
        for arg in node.args.args:
            if arg.arg == 'self':
                continue
                
            # Look for default values that are Depends() calls
            defaults = node.args.defaults
            arg_count = len(node.args.args)
            default_count = len(defaults)
            
            # Calculate if this argument has a default value
            if default_count > 0:
                arg_index = node.args.args.index(arg)
                default_index = arg_index - (arg_count - default_count)
                
                if default_index >= 0 and default_index < len(defaults):
                    default_value = defaults[default_index]
                    
                    # Check if default is a Depends() call
                    if isinstance(default_value, ast.Call):
                        if (isinstance(default_value.func, ast.Name) and default_value.func.id == 'Depends') or \
                           (isinstance(default_value.func, ast.Attribute) and default_value.func.attr == 'Depends'):
                            
                            # Extract dependency function name
                            if default_value.args:
                                dep_arg = default_value.args[0]
                                if isinstance(dep_arg, ast.Name):
                                    dep_name = dep_arg.id
                                elif isinstance(dep_arg, ast.Attribute):
                                    dep_name = f"{ast.unparse(dep_arg.value)}.{dep_arg.attr}"
                                else:
                                    try:
                                        dep_name = ast.unparse(dep_arg)
                                    except:
                                        dep_name = "<complex_dependency>"
                                
                                dependencies.append(dep_name)
                                dependency_docs[arg.arg] = dep_name
        
        # Check keyword-only arguments for dependencies
        for i, kwarg in enumerate(node.args.kwonlyargs):
            if i < len(node.args.kw_defaults) and node.args.kw_defaults[i]:
                default_value = node.args.kw_defaults[i]
                
                if isinstance(default_value, ast.Call):
                    if (isinstance(default_value.func, ast.Name) and default_value.func.id == 'Depends') or \
                       (isinstance(default_value.func, ast.Attribute) and default_value.func.attr == 'Depends'):
                        
                        if default_value.args:
                            dep_arg = default_value.args[0]
                            if isinstance(dep_arg, ast.Name):
                                dep_name = dep_arg.id
                            elif isinstance(dep_arg, ast.Attribute):
                                dep_name = f"{ast.unparse(dep_arg.value)}.{dep_arg.attr}"
                            else:
                                try:
                                    dep_name = ast.unparse(dep_arg)
                                except:
                                    dep_name = "<complex_dependency>"
                            
                            dependencies.append(dep_name)
                            dependency_docs[kwarg.arg] = dep_name
        
        return dependencies, dependency_docs

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

    def _detect_docstring_style(self, docstring: str) -> tuple[str | None, list[str]]:
        """
        Detect docstring style and identify formatting issues.
        Returns (style_name, issues_list)
        """
        if not docstring:
            return None, []
        
        style_indicators = {
            'google': 0,
            'numpy': 0,
            'sphinx': 0
        }
        issues = []
        
        # Google style indicators
        google_patterns = [
            r'(?:Args?|Arguments?):\s*\n',
            r'(?:Returns?|Return):\s*\n',
            r'(?:Yields?|Yield):\s*\n',
            r'(?:Raises?|Raise):\s*\n',
            r'(?:Note|Notes?):\s*\n',
            r'(?:Example|Examples?):\s*\n'
        ]
        for pattern in google_patterns:
            if re.search(pattern, docstring, re.IGNORECASE | re.MULTILINE):
                style_indicators['google'] += 1
        
        # Numpy style indicators  
        numpy_patterns = [
            r'Parameters\s*\n\s*[-=]+',
            r'Returns?\s*\n\s*[-=]+',
            r'Yields?\s*\n\s*[-=]+',
            r'Raises?\s*\n\s*[-=]+',
            r'Notes?\s*\n\s*[-=]+',
            r'Examples?\s*\n\s*[-=]+'
        ]
        for pattern in numpy_patterns:
            if re.search(pattern, docstring, re.IGNORECASE | re.MULTILINE):
                style_indicators['numpy'] += 1
        
        # Sphinx style indicators
        sphinx_patterns = [
            r':param\s+\w+:',
            r':type\s+\w+:',
            r':returns?:',
            r':rtype:',
            r':raises?\s+\w+:',
            r':note:',
            r':example:'
        ]
        for pattern in sphinx_patterns:
            if re.search(pattern, docstring, re.IGNORECASE):
                style_indicators['sphinx'] += 1
        
        # Determine primary style
        max_score = max(style_indicators.values())
        if max_score == 0:
            return 'plain', []
        
        detected_styles = [style for style, score in style_indicators.items() if score == max_score]
        
        if len(detected_styles) > 1:
            issues.append(f"Mixed docstring styles detected: {detected_styles}")
            primary_style = detected_styles[0]  # Pick first one
        else:
            primary_style = detected_styles[0]
        
        # Style-specific validation
        if primary_style == 'google':
            issues.extend(self._validate_google_style(docstring))
        elif primary_style == 'numpy':
            issues.extend(self._validate_numpy_style(docstring))
        elif primary_style == 'sphinx':
            issues.extend(self._validate_sphinx_style(docstring))
        
        return primary_style, issues

    def _validate_google_style(self, docstring: str) -> list[str]:
        """Validate Google-style docstring formatting."""
        issues = []
        
        # Check for proper section formatting
        sections = re.findall(r'^\s*(Args?|Arguments?|Returns?|Return|Yields?|Yield|Raises?|Raise|Note|Notes?|Example|Examples?):\s*$', 
                            docstring, re.MULTILINE | re.IGNORECASE)
        
        for section in sections:
            # Check if section has content
            section_pattern = rf'{re.escape(section)}:\s*\n((?:\s+.*\n?)*?)(?=\n\s*\w+:|$)'
            match = re.search(section_pattern, docstring, re.MULTILINE | re.IGNORECASE)
            if match and not match.group(1).strip():
                issues.append(f"Empty {section} section")
        
        return issues

    def _validate_numpy_style(self, docstring: str) -> list[str]:
        """Validate Numpy-style docstring formatting."""
        issues = []
        
        # Check for proper section headers with underlines
        section_headers = re.findall(r'^\s*(\w+)\s*\n\s*([-=]+)', docstring, re.MULTILINE)
        
        for header, underline in section_headers:
            if len(underline) < len(header):
                issues.append(f"Underline too short for section '{header}'")
        
        return issues

    def _validate_sphinx_style(self, docstring: str) -> list[str]:
        """Validate Sphinx-style docstring formatting."""
        issues = []
        
        # Check for proper parameter/return documentation
        param_tags = re.findall(r':param\s+(\w+):', docstring)
        type_tags = re.findall(r':type\s+(\w+):', docstring)
        
        # Check if every param has a type (common Sphinx practice)
        missing_types = set(param_tags) - set(type_tags)
        if missing_types:
            issues.append(f"Missing type declarations for parameters: {list(missing_types)}")
        
        return issues

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
        
        if method in ['FUNCTION', 'ASYNC_FUNCTION', 'PROPERTY', 'STATICMETHOD', 'CLASSMETHOD', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE', 'WEBSOCKET']:
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
        
        elif method in ['MIDDLEWARE', 'ROUTER_INCLUSION', 'ROUTER_METADATA']:
            # Coverage scoring for FastAPI infrastructure
            max_coverage = 100
            max_quality = 100
            
            # These are structural elements, give them basic coverage
            coverage_points += 80  # Detected = good coverage
            quality_points += 70   # Structural quality
            
            if docstring:
                coverage_points += 20
                quality_points += 30
        
        elif method == 'PYDANTIC_CONFIG':
            # Coverage scoring for Pydantic config classes
            max_coverage = 100
            max_quality = 100
            
            # Config classes are usually simple
            coverage_points += 90
            quality_points += 80
            
            if docstring:
                coverage_points += 10
                quality_points += 20
        
        # Calculate final scores as percentages
        coverage_score = (coverage_points / max_coverage * 100) if max_coverage > 0 else 0
        quality_score = (quality_points / max_quality * 100) if max_quality > 0 else 0
        
        return min(coverage_score, 100), min(quality_score, 100), issues

    def _calculate_advanced_metrics(self, item_data: dict, coverage_score: float, quality_score: float) -> dict:
        """Calculate advanced quality metrics for documentation items."""
        docstring = item_data.get('docstring', '')
        method = item_data.get('method', '')
        actual_params = item_data.get('actual_params', [])
        missing_params = item_data.get('missing_params', [])
        has_type_hints = item_data.get('has_type_hints', False)
        has_return_doc = item_data.get('has_return_doc', False)
        return_type = item_data.get('return_type')
        
        # Docstring length metric
        docstring_length = len(docstring) if docstring else 0
        
        # Complexity score (based on multiple factors)
        complexity_factors = []
        
        # Parameter complexity
        if actual_params:
            param_complexity = len(actual_params) / 10.0  # Normalize to 0-1
            complexity_factors.append(min(param_complexity, 1.0))
        
        # Type hint complexity (good type hints reduce complexity score)
        if has_type_hints:
            complexity_factors.append(0.8)  # Type hints make code easier to understand
        else:
            complexity_factors.append(1.2)  # No type hints increase complexity
            
        complexity_score = sum(complexity_factors) / len(complexity_factors) if complexity_factors else 0.5
        complexity_score = min(complexity_score * 100, 100)
        
        # Maintainability score (based on documentation quality)
        maintainability_factors = []
        
        # Documentation completeness factor
        if docstring_length > 50:
            maintainability_factors.append(0.9)
        elif docstring_length > 20:
            maintainability_factors.append(0.7)
        else:
            maintainability_factors.append(0.3)
        
        # Parameter documentation factor
        if actual_params:
            param_doc_ratio = (len(actual_params) - len(missing_params)) / len(actual_params)
            maintainability_factors.append(param_doc_ratio)
        else:
            maintainability_factors.append(1.0)
        
        # Type hints factor
        maintainability_factors.append(0.9 if has_type_hints else 0.6)
        
        # Return documentation factor
        if return_type and return_type != "None":
            maintainability_factors.append(0.9 if has_return_doc else 0.5)
        else:
            maintainability_factors.append(0.8)
        
        maintainability_score = sum(maintainability_factors) / len(maintainability_factors) * 100
        
        # API completeness score (for API endpoints)
        api_completeness_score = 0.0
        if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE', 'WEBSOCKET']:
            api_factors = []
            
            # Response model factor
            response_model = item_data.get('response_model')
            api_factors.append(0.9 if response_model else 0.5)
            
            # Status codes factor
            status_codes = item_data.get('status_codes', [])
            api_factors.append(0.8 if status_codes and status_codes != ['Default'] else 0.6)
            
            # Tags factor
            tags = item_data.get('tags', [])
            api_factors.append(0.8 if tags else 0.4)
            
            # Operation ID factor
            operation_id = item_data.get('operation_id')
            api_factors.append(0.7 if operation_id else 0.5)
            
            # Dependencies documentation factor
            dependencies = item_data.get('dependencies', [])
            dependency_docs = item_data.get('dependency_docs', {})
            if dependencies:
                dep_doc_ratio = len([p for p in dependency_docs.keys() if p in item_data.get('documented_params', [])]) / len(dependencies)
                api_factors.append(dep_doc_ratio)
            else:
                api_factors.append(0.8)
            
            api_completeness_score = sum(api_factors) / len(api_factors) * 100
        
        return {
            'docstring_length': docstring_length,
            'complexity_score': round(complexity_score, 1),
            'maintainability_score': round(maintainability_score, 1),
            'api_completeness_score': round(api_completeness_score, 1)
        }

    def _classify_method_type(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Classify the type of method based on decorators."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == 'property':
                    return 'PROPERTY'
                elif decorator.id == 'staticmethod':
                    return 'STATICMETHOD'
                elif decorator.id == 'classmethod':
                    return 'CLASSMETHOD'
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr == 'property':
                    return 'PROPERTY'
                elif decorator.attr == 'staticmethod':
                    return 'STATICMETHOD'
                elif decorator.attr == 'classmethod':
                    return 'CLASSMETHOD'
        
        # Check if it's an async function
        if isinstance(node, ast.AsyncFunctionDef):
            return 'ASYNC_FUNCTION'
        
        return 'FUNCTION'

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
        
        # Classify method type
        method_type = self._classify_method_type(node)
        
        # Detect docstring style and issues
        docstring_style, style_issues = self._detect_docstring_style(func_doc)
        
        # Extract exception information
        documented_exceptions, has_exception_doc = self._extract_documented_exceptions(func_doc)
        raised_exceptions = self._extract_raised_exceptions(node)
        
        # Extract dependency information
        dependencies, dependency_docs = self._extract_dependencies(node)
        
        # Calculate missing and extra parameters
        missing_params = [p for p in actual_params if p not in documented_params and not p.startswith('*')]
        extra_params = [p for p in documented_params if p not in actual_params]

        # Calculate coverage and quality scores
        item_data = {
            'method': method_type,
            'docstring': func_doc,
            'actual_params': actual_params,
            'missing_params': missing_params,
            'has_return_doc': has_return_doc,
            'has_type_hints': has_type_hints,
            'return_type': return_type,
            'documented_params': documented_params,
            'dependencies': dependencies,
            'dependency_docs': dependency_docs
        }
        coverage_score, quality_score, issues = self._calculate_coverage_score(item_data)
        
        # Calculate advanced metrics
        advanced_metrics = self._calculate_advanced_metrics(item_data, coverage_score, quality_score)

        # Build qualified name including class context
        if self.class_stack:
            qualified_name = ".".join(self.class_stack) + "." + node.name
        else:
            qualified_name = node.name

        # 1) Record every function/method with enhanced validation info
        self.items.append(DocItem(
            module=self.module,
            qualname=qualified_name,
            path="",
            method=method_type,
            signature=sig,
            docstring=func_doc,
            description=None,
            first_lines=snippet,
            lineno=node.lineno,
            file_path=self.filename,
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
            completeness_issues=issues,
            docstring_style=docstring_style,
            style_issues=style_issues,
            documented_exceptions=documented_exceptions,
            raised_exceptions=raised_exceptions,
            has_exception_doc=has_exception_doc,
            dependencies=dependencies,
            dependency_docs=dependency_docs,
            docstring_length=advanced_metrics['docstring_length'],
            complexity_score=advanced_metrics['complexity_score'],
            maintainability_score=advanced_metrics['maintainability_score'],
            api_completeness_score=advanced_metrics['api_completeness_score']
        ))

        # 2) Now detect FastAPI HTTP decorators
        for deco in node.decorator_list:
            if isinstance(deco, ast.Call) and hasattr(deco.func, "attr"):
                http = deco.func.attr.upper()
                if http in HTTP_METHODS or http in WEBSOCKET_METHODS:
                    # extract path (first Constant arg)
                    path = ""
                    for arg in deco.args:
                        if isinstance(arg, ast.Constant):
                            path = arg.value
                            break

                    # extract FastAPI decorator parameters
                    summary = None
                    desc = None
                    response_model = None
                    status_codes = []
                    response_description = None
                    tags = []
                    operation_id = None
                    
                    for kw in deco.keywords:
                        if kw.arg == "summary" and isinstance(kw.value, ast.Constant):
                            summary = kw.value.value
                        elif kw.arg == "description" and isinstance(kw.value, ast.Constant):
                            desc = kw.value.value
                        elif kw.arg == "response_model":
                            try:
                                response_model = ast.unparse(kw.value)
                            except:
                                response_model = "<complex_model>"
                        elif kw.arg == "status_code" and isinstance(kw.value, ast.Constant):
                            status_codes.append(str(kw.value.value))
                        elif kw.arg == "responses" and isinstance(kw.value, ast.Dict):
                            # Extract status codes from responses dict
                            for key in kw.value.keys:
                                if isinstance(key, ast.Constant):
                                    status_codes.append(str(key.value))
                        elif kw.arg == "response_description" and isinstance(kw.value, ast.Constant):
                            response_description = kw.value.value
                        elif kw.arg == "tags":
                            # Extract tags from list
                            if isinstance(kw.value, ast.List):
                                for tag_item in kw.value.elts:
                                    if isinstance(tag_item, ast.Constant):
                                        tags.append(tag_item.value)
                            elif isinstance(kw.value, ast.Constant):
                                tags.append(kw.value.value)
                        elif kw.arg == "operation_id" and isinstance(kw.value, ast.Constant):
                            operation_id = kw.value.value

                    # Calculate coverage for endpoint
                    endpoint_data = {
                        'method': http,
                        'docstring': func_doc,
                        'actual_params': actual_params,
                        'missing_params': missing_params,
                        'has_return_doc': has_return_doc,
                        'has_type_hints': has_type_hints,
                        'return_type': return_type,
                        'documented_params': documented_params,
                        'dependencies': dependencies,
                        'dependency_docs': dependency_docs,
                        'response_model': response_model,
                        'status_codes': status_codes,
                        'tags': tags,
                        'operation_id': operation_id
                    }
                    endpoint_coverage, endpoint_quality, endpoint_issues = self._calculate_coverage_score(endpoint_data)
                    
                    # Calculate advanced metrics for endpoint
                    endpoint_advanced_metrics = self._calculate_advanced_metrics(endpoint_data, endpoint_coverage, endpoint_quality)

                    self.items.append(DocItem(
                        module=self.module,
                        qualname=qualified_name,
                        path=path,
                        method=http,
                        signature=sig,
                        docstring=func_doc,
                        description=desc if desc is not None else summary,
                        first_lines=snippet,
                        lineno=node.lineno,
                        file_path=self.filename,
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
                        completeness_issues=endpoint_issues,
                        docstring_style=docstring_style,
                        style_issues=style_issues,
                        documented_exceptions=documented_exceptions,
                        raised_exceptions=raised_exceptions,
                        has_exception_doc=has_exception_doc,
                        response_model=response_model,
                        status_codes=status_codes,
                        response_description=response_description,
                        dependencies=dependencies,
                        dependency_docs=dependency_docs,
                        tags=tags,
                        operation_id=operation_id,
                        summary_from_decorator=summary,
                        docstring_length=endpoint_advanced_metrics['docstring_length'],
                        complexity_score=endpoint_advanced_metrics['complexity_score'],
                        maintainability_score=endpoint_advanced_metrics['maintainability_score'],
                        api_completeness_score=endpoint_advanced_metrics['api_completeness_score']
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
