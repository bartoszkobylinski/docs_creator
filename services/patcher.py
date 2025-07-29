import re
import os
import ast
import shutil
from textwrap import indent
from typing import Optional, Dict, Any
from datetime import datetime

def resolve_file_path(file_path: str, base_path: str = ".") -> str:
    """Resolve file path relative to base path if not absolute."""
    if os.path.isabs(file_path):
        return file_path
    return os.path.join(base_path, file_path)

def create_backup(file_path: str) -> str:
    """Create a backup of the file before patching."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def apply_docstring_patch(file_path: str, lineno: int, new_doc: str, 
                         create_backup_file: bool = True, base_path: str = ".") -> Dict[str, Any]:
    """
    Replaces (or inserts) the triple-quoted docstring for the function/class
    whose def line is at `lineno` in file_path.
    
    Returns:
        Dict with status, message, and backup_path if successful
    """
    try:
        # Resolve file path
        resolved_path = resolve_file_path(file_path, base_path)
        
        if not os.path.exists(resolved_path):
            return {
                "success": False,
                "message": f"File not found: {resolved_path}",
                "backup_path": None
            }
        
        # Create backup if requested
        backup_path = None
        if create_backup_file:
            backup_path = create_backup(resolved_path)
        
        # Read file
        with open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.splitlines(True)
        
        if lineno < 1 or lineno > len(lines):
            return {
                "success": False,
                "message": f"Line number {lineno} out of range (1-{len(lines)})",
                "backup_path": backup_path
            }
        
        i = lineno - 1
        
        # Validate that this is a def/class line
        if not re.match(r"^\s*(def|class|async\s+def)\s+", lines[i]):
            actual_content = lines[i].strip() if lines[i] else "<empty line>"
            
            # Search for any function definition within a reasonable range (±10 lines)
            found_line = None
            for search_line in range(max(1, lineno - 10), min(len(lines) + 1, lineno + 11)):
                search_index = search_line - 1
                if search_index < len(lines):
                    line_content = lines[search_index]
                    if re.match(r"^\s*(def|class|async\s+def)\s+", line_content):
                        found_line = search_line
                        break
            
            if found_line:
                return {
                    "success": False,
                    "message": f"Line {lineno} is not the function definition (found: '{actual_content}'). A function definition was found at line {found_line}. Please re-scan the project to update line numbers.",
                    "backup_path": backup_path
                }
            else:
                return {
                    "success": False,
                    "message": f"Line {lineno} is not a function/class definition (found: '{actual_content}'). No function definition found nearby. Please re-scan the project.",
                    "backup_path": backup_path
                }
        
        # Get base indentation
        indent_match = re.match(r"^(\s*)", lines[i])
        base_indent = indent_match.group(1)
        
        # Find insertion point (skip existing docstring)
        j = i + 1
        
        # Skip the colon and find the first content line
        while j < len(lines) and lines[j].strip() in ["", ":"]:
            j += 1
        
        # Check if there's already a docstring
        if j < len(lines):
            stripped_line = lines[j].strip()
            if stripped_line.startswith(('"""', "'''", '"', "'")):
                # Find the end of the existing docstring
                if stripped_line.startswith(('"""', "'''")):
                    # Multi-line docstring
                    quote_type = stripped_line[:3]
                    if stripped_line.count(quote_type) >= 2:
                        # Single-line docstring
                        j += 1
                    else:
                        # Multi-line docstring, find closing quotes
                        j += 1
                        while j < len(lines) and quote_type not in lines[j]:
                            j += 1
                        if j < len(lines):
                            j += 1
                else:
                    # Single-line docstring with single quotes
                    j += 1
        
        # Build the new docstring block
        if not new_doc.strip():
            # Empty docstring - don't add anything
            new_lines = lines[:i+1] + lines[j:]
        else:
            # Add proper indentation for docstring content
            docstring_indent = base_indent + "    "  # Standard 4-space indent
            
            block = []
            
            # Handle multi-line docstrings properly
            doc_lines = new_doc.strip().splitlines()
            
            if len(doc_lines) == 1:
                # Single-line docstring: """Content on same line"""
                block.append(f'{docstring_indent}"""{doc_lines[0]}"""\n')
            else:
                # Multi-line docstring: """First line on same line as quotes
                block.append(f'{docstring_indent}"""{doc_lines[0]}\n')
                
                # Add remaining lines with proper indentation
                for line in doc_lines[1:]:
                    if line.strip():  # Skip completely empty lines
                        block.append(f'{docstring_indent}{line}\n')
                    else:
                        block.append('\n')  # Preserve empty lines
                
                # Closing quotes on separate line
                block.append(f'{docstring_indent}"""\n')
            
            # Insert the new docstring
            new_lines = lines[:i+1] + block + lines[j:]
        
        # Write back to file
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write("".join(new_lines))
        
        return {
            "success": True,
            "message": f"Successfully patched docstring at line {lineno}",
            "backup_path": backup_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error patching file: {str(e)}",
            "backup_path": backup_path if 'backup_path' in locals() else None
        }

def apply_module_docstring_patch(file_path: str, new_doc: str, 
                               create_backup_file: bool = True, base_path: str = ".") -> Dict[str, Any]:
    """
    Replaces (or inserts) the module-level docstring at the top of the file.
    """
    try:
        # Resolve file path
        resolved_path = resolve_file_path(file_path, base_path)
        
        if not os.path.exists(resolved_path):
            return {
                "success": False,
                "message": f"File not found: {resolved_path}",
                "backup_path": None
            }
        
        # Create backup if requested
        backup_path = None
        if create_backup_file:
            backup_path = create_backup(resolved_path)
        
        # Parse the file to find existing module docstring
        with open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            existing_docstring = ast.get_docstring(tree)
        except SyntaxError as e:
            return {
                "success": False,
                "message": f"Syntax error in file: {str(e)}",
                "backup_path": backup_path
            }
        
        lines = content.splitlines(True)
        
        # Find where to insert the module docstring
        insert_line = 0
        
        # Skip shebang and encoding declarations
        for i, line in enumerate(lines):
            if line.startswith('#!') or 'coding:' in line or 'encoding:' in line:
                insert_line = i + 1
            else:
                break
        
        # If there's an existing module docstring, remove it
        if existing_docstring:
            # Find the docstring in the AST
            for node in ast.walk(tree):
                if (isinstance(node, ast.Expr) and 
                    isinstance(node.value, ast.Constant) and 
                    isinstance(node.value.value, str) and
                    node.value.value == existing_docstring):
                    # Remove lines from docstring start to end
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    lines = lines[:start_line] + lines[end_line:]
                    break
        
        # Build new docstring
        if new_doc.strip():
            docstring_lines = []
            docstring_lines.append('"""\n')
            for line in new_doc.strip().splitlines():
                docstring_lines.append(f'{line}\n')
            docstring_lines.append('"""\n')
            
            # Insert at the appropriate position
            lines = lines[:insert_line] + docstring_lines + lines[insert_line:]
        
        # Write back to file
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        
        return {
            "success": True,
            "message": "Successfully patched module docstring",
            "backup_path": backup_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error patching module docstring: {str(e)}",
            "backup_path": backup_path if 'backup_path' in locals() else None
        }

def validate_docstring_syntax(docstring: str) -> Dict[str, Any]:
    """
    Validate that the docstring is properly formatted.
    """
    try:
        # Try to parse as part of a dummy function
        test_code = f'''
def test_function():
    """{docstring}"""
    pass
'''
        ast.parse(test_code)
        return {"valid": True, "message": "Docstring syntax is valid"}
    except SyntaxError as e:
        return {"valid": False, "message": f"Docstring syntax error: {str(e)}"}

def get_item_file_path(item_data: Dict[str, Any], base_path: str = ".") -> str:
    """
    Extract file path from DocItem data, handling different formats.
    """
    # First try the file_path field
    file_path = item_data.get('file_path', '')
    
    if not file_path:
        # Fall back to constructing from module name
        module = item_data.get('module', '')
        if module:
            file_path = f"{module.replace('.', '/')}.py"
    
    return resolve_file_path(file_path, base_path)

def apply_docitem_patch(item_data: Dict[str, Any], new_doc: str, 
                       create_backup_file: bool = True, base_path: str = ".") -> Dict[str, Any]:
    """
    Apply docstring patch based on DocItem type and data.
    """
    method_type = item_data.get('method', '').upper()
    qualname = item_data.get('qualname', '')
    
    # Scanner now properly skips non-documentable items, so this check is no longer needed
    
    if method_type == 'MODULE':
        file_path = get_item_file_path(item_data, base_path)
        return apply_module_docstring_patch(file_path, new_doc, create_backup_file, base_path)
    
    elif method_type in ['FUNCTION', 'ASYNC_FUNCTION', 'CLASS', 'PYDANTIC_MODEL', 
                         'PROPERTY', 'STATICMETHOD', 'CLASSMETHOD', 'MIDDLEWARE',
                         'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE', 'WEBSOCKET']:
        file_path = get_item_file_path(item_data, base_path)
        lineno = item_data.get('lineno', 1)
        return apply_docstring_patch(file_path, lineno, new_doc, create_backup_file, base_path)
    
    else:
        return {
            "success": False,
            "message": f"Unsupported method type for patching: {method_type}",
            "backup_path": None
        }
