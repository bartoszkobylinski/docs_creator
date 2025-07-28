"""
Unit tests for core scanner module.
Tests AST analysis and documentation item extraction.
"""

import ast
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from fastdoc.scanner import scan_file, DocumentationItem
from fastdoc.models import DocumentationItem as ModelDocItem


@pytest.mark.unit
class TestScanFile:
    """Test cases for scan_file function."""
    
    def test_scan_simple_function(self, temp_dir):
        """Test scanning a simple function."""
        content = '''
def hello_world():
    """Say hello to the world."""
    return "Hello, World!"
'''
        file_path = Path(temp_dir) / "simple.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        assert len(items) == 1
        item = items[0]
        assert item.qualname == "hello_world"
        assert item.docstring == "Say hello to the world."
        assert item.lineno == 2
        assert item.method == "function"
    
    def test_scan_class_with_methods(self, temp_dir):
        """Test scanning a class with methods."""
        content = '''
class UserService:
    """Service for managing users."""
    
    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
    
    def get_user(self, user_id):
        """Get user by ID."""
        return self.db.get(user_id)
    
    def create_user(self, name, email):
        return self.db.create(name=name, email=email)
    
    @property 
    def user_count(self):
        """Get total user count."""
        return len(self.db.all())
'''
        file_path = Path(temp_dir) / "service.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        # Should find class and all methods
        qualnames = [item.qualname for item in items]
        assert "UserService" in qualnames
        assert "UserService.__init__" in qualnames
        assert "UserService.get_user" in qualnames
        assert "UserService.create_user" in qualnames
        assert "UserService.user_count" in qualnames
        
        # Check class documentation
        class_item = next(item for item in items if item.qualname == "UserService")
        assert class_item.docstring == "Service for managing users."
        assert class_item.method == "class"
        
        # Check method documentation
        get_user_item = next(item for item in items if item.qualname == "UserService.get_user")
        assert get_user_item.docstring == "Get user by ID."
        assert get_user_item.method == "function"
        
        # Check undocumented method
        create_user_item = next(item for item in items if item.qualname == "UserService.create_user")
        assert create_user_item.docstring is None
    
    def test_scan_fastapi_endpoints(self, temp_dir):
        """Test scanning FastAPI endpoints."""
        content = '''
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/")
def root():
    """Root endpoint returning welcome message."""
    return {"message": "Hello World"}

@app.post("/users/")
def create_user(user: dict):
    """Create a new user."""
    return {"user": user}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

@app.put("/users/{user_id}")
@app.patch("/users/{user_id}")
def update_user(user_id: int, user: dict):
    """Update user information."""
    return {"user_id": user_id, "user": user}

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user."""
    return {"deleted": user_id}
'''
        file_path = Path(temp_dir) / "api.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        # Filter for HTTP endpoints
        endpoints = [item for item in items if item.method in ["GET", "POST", "PUT", "PATCH", "DELETE"]]
        
        assert len(endpoints) >= 5  # At least 5 endpoints
        
        # Check specific endpoints
        root_endpoint = next((item for item in endpoints if item.qualname == "root"), None)
        assert root_endpoint is not None
        assert root_endpoint.method == "GET"
        assert root_endpoint.path == "/"
        assert root_endpoint.docstring == "Root endpoint returning welcome message."
        
        create_endpoint = next((item for item in endpoints if item.qualname == "create_user"), None)
        assert create_endpoint is not None
        assert create_endpoint.method == "POST"
        assert create_endpoint.path == "/users/"
        
        # Check endpoint with multiple decorators
        update_endpoints = [item for item in endpoints if item.qualname == "update_user"]
        assert len(update_endpoints) >= 2  # Should have both PUT and PATCH
        methods = [item.method for item in update_endpoints]
        assert "PUT" in methods
        assert "PATCH" in methods
    
    def test_scan_with_type_hints(self, temp_dir):
        """Test scanning functions with type hints."""
        content = '''
from typing import List, Optional

def process_data(items: List[str], max_count: Optional[int] = None) -> dict:
    """Process a list of items."""
    return {"processed": len(items)}

def calculate_score(base: float, multiplier: float = 1.0) -> float:
    return base * multiplier
'''
        file_path = Path(temp_dir) / "typed.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        process_item = next(item for item in items if item.qualname == "process_data")
        assert process_item.has_type_hints is True
        
        calculate_item = next(item for item in items if item.qualname == "calculate_score")
        assert calculate_item.has_type_hints is True
    
    def test_scan_pydantic_models(self, temp_dir):
        """Test scanning Pydantic models."""
        content = '''
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    """User model with validation."""
    id: int
    name: str
    email: str
    age: Optional[int] = None
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True
        
    def display_name(self) -> str:
        """Get display name for user."""
        return f"{self.name} ({self.email})"

class Product(BaseModel):
    name: str
    price: float
'''
        file_path = Path(temp_dir) / "models.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        # Should find both models and nested Config class
        qualnames = [item.qualname for item in items]
        assert "User" in qualnames
        assert "Product" in qualnames
        assert "User.Config" in qualnames
        assert "User.display_name" in qualnames
        
        # Check model documentation
        user_item = next(item for item in items if item.qualname == "User")
        assert user_item.docstring == "User model with validation."
        assert user_item.method == "class"
        
        # Check undocumented model
        product_item = next(item for item in items if item.qualname == "Product")
        assert product_item.docstring is None
    
    def test_scan_async_functions(self, temp_dir):
        """Test scanning async functions."""
        content = '''
import asyncio

async def fetch_data(url: str):
    """Fetch data from URL asynchronously."""
    # Simulate async operation
    await asyncio.sleep(0.1)
    return {"data": "fetched"}

async def process_batch(items):
    return [await fetch_data(item) for item in items]
'''
        file_path = Path(temp_dir) / "async_code.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        fetch_item = next(item for item in items if item.qualname == "fetch_data")
        assert fetch_item.docstring == "Fetch data from URL asynchronously."
        assert fetch_item.method == "async_function"
        
        process_item = next(item for item in items if item.qualname == "process_batch")
        assert process_item.method == "async_function"
        assert process_item.docstring is None
    
    def test_scan_nested_functions(self, temp_dir):
        """Test scanning nested functions."""
        content = '''
def outer_function(x):
    """Outer function with nested definition."""
    
    def inner_function(y):
        """Inner function."""
        return x + y
    
    def another_inner(z):
        return x * z
    
    return inner_function, another_inner
'''
        file_path = Path(temp_dir) / "nested.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        qualnames = [item.qualname for item in items]
        assert "outer_function" in qualnames
        assert "outer_function.inner_function" in qualnames
        assert "outer_function.another_inner" in qualnames
        
        # Check nested function documentation
        inner_item = next(item for item in items if item.qualname == "outer_function.inner_function")
        assert inner_item.docstring == "Inner function."
    
    def test_scan_decorators(self, temp_dir):
        """Test scanning functions with decorators."""
        content = '''
from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def decorated_function():
    """Function with decorator."""
    return "decorated"

@staticmethod
def static_method():
    """Static method."""
    return "static"

@classmethod 
def class_method(cls):
    """Class method.""" 
    return cls
'''
        file_path = Path(temp_dir) / "decorated.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        # Check that decorated functions are still found
        qualnames = [item.qualname for item in items]
        assert "decorated_function" in qualnames
        assert "static_method" in qualnames
        assert "class_method" in qualnames
        
        decorated_item = next(item for item in items if item.qualname == "decorated_function")
        assert decorated_item.docstring == "Function with decorator."
    
    def test_scan_syntax_error_file(self, temp_dir):
        """Test scanning file with syntax errors."""
        content = '''
def broken_function(
    """This function has syntax error."""
    return "broken"
'''
        file_path = Path(temp_dir) / "broken.py"
        file_path.write_text(content)
        
        # Should handle syntax errors gracefully
        items = scan_file(str(file_path))
        
        # Should return empty list for unparseable files
        assert items == []
    
    def test_scan_empty_file(self, temp_dir):
        """Test scanning empty file."""
        file_path = Path(temp_dir) / "empty.py"
        file_path.write_text("")
        
        items = scan_file(str(file_path))
        
        assert items == []
    
    def test_scan_nonexistent_file(self):
        """Test scanning nonexistent file."""
        with pytest.raises(FileNotFoundError):
            scan_file("/nonexistent/file.py")
    
    def test_scan_complex_inheritance(self, temp_dir):
        """Test scanning complex class inheritance."""
        content = '''
class BaseClass:
    """Base class for all entities."""
    
    def base_method(self):
        """Method in base class."""
        pass

class MiddleClass(BaseClass):
    """Middle class in hierarchy."""
    
    def middle_method(self):
        pass

class FinalClass(MiddleClass):
    """Final class inheriting from middle."""
    
    def base_method(self):
        """Override base method."""
        super().base_method()
    
    def final_method(self):
        """Method only in final class."""
        pass
'''
        file_path = Path(temp_dir) / "inheritance.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        # Should find all classes and methods
        qualnames = [item.qualname for item in items]
        assert "BaseClass" in qualnames
        assert "MiddleClass" in qualnames
        assert "FinalClass" in qualnames
        assert "BaseClass.base_method" in qualnames
        assert "FinalClass.base_method" in qualnames  # Overridden method
        assert "FinalClass.final_method" in qualnames
    
    def test_scan_multiple_inheritance(self, temp_dir):
        """Test scanning multiple inheritance scenarios."""
        content = '''
class Mixin1:
    """First mixin class."""
    def mixin1_method(self):
        pass

class Mixin2:
    """Second mixin class."""
    def mixin2_method(self):
        pass

class Combined(Mixin1, Mixin2):
    """Class with multiple inheritance."""
    def combined_method(self):
        """Method in combined class."""
        pass
'''
        file_path = Path(temp_dir) / "multiple.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        # Should handle multiple inheritance
        combined_item = next(item for item in items if item.qualname == "Combined")
        assert combined_item.docstring == "Class with multiple inheritance."


@pytest.mark.unit
class TestDocumentationItem:
    """Test cases for DocumentationItem class."""
    
    def test_documentation_item_creation(self):
        """Test creating a DocumentationItem instance."""
        item = DocumentationItem(
            module="test_module",
            qualname="TestClass.test_method",
            method="function",
            file_path="/test/file.py",
            lineno=42,
            docstring="Test docstring"
        )
        
        assert item.module == "test_module"
        assert item.qualname == "TestClass.test_method"
        assert item.method == "function"
        assert item.file_path == "/test/file.py"
        assert item.lineno == 42
        assert item.docstring == "Test docstring"
    
    def test_documentation_item_defaults(self):
        """Test DocumentationItem with default values."""
        item = DocumentationItem(
            module="test",
            qualname="test_func",
            method="function"
        )
        
        # Check default values
        assert item.file_path == ""
        assert item.lineno == 0
        assert item.docstring is None
        assert item.coverage_score == 0.0
        assert item.quality_score == 0.0
        assert item.has_type_hints is False
        assert item.dependencies == []
        assert item.tags == []
    
    def test_documentation_item_dict_conversion(self):
        """Test converting DocumentationItem to dictionary."""
        item = DocumentationItem(
            module="api",
            qualname="get_users", 
            method="GET",
            path="/users",
            docstring="Get all users",
            has_type_hints=True,
            dependencies=["auth"],
            tags=["users"]
        )
        
        item_dict = item.__dict__
        
        assert isinstance(item_dict, dict)
        assert item_dict["module"] == "api"
        assert item_dict["qualname"] == "get_users"
        assert item_dict["method"] == "GET"
        assert item_dict["path"] == "/users"
        assert item_dict["has_type_hints"] is True
        assert item_dict["dependencies"] == ["auth"]
        assert item_dict["tags"] == ["users"]


@pytest.mark.unit
class TestScannerEdgeCases:
    """Test edge cases and error conditions in scanner."""
    
    def test_scan_file_with_encoding_issues(self, temp_dir):
        """Test scanning file with encoding issues."""
        # Create file with non-UTF-8 content
        file_path = Path(temp_dir) / "encoding.py"
        with open(file_path, 'wb') as f:
            # Write some content with problematic encoding
            f.write(b'def test():\n    """Test with \xff\xfe chars"""\n    pass\n')
        
        # Should handle encoding issues gracefully
        items = scan_file(str(file_path))
        
        # May return empty list or parsed content depending on error handling
        assert isinstance(items, list)
    
    def test_scan_very_large_file(self, temp_dir):
        """Test scanning a very large file."""
        # Create a large file with many functions
        content_lines = ["# Large file test"]
        for i in range(1000):
            content_lines.extend([
                f"def function_{i}():",
                f'    """Function number {i}."""',
                f"    return {i}",
                ""
            ])
        
        content = "\n".join(content_lines)
        file_path = Path(temp_dir) / "large.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        # Should handle large files
        assert len(items) == 1000
        assert all(item.method == "function" for item in items)
    
    def test_scan_deeply_nested_code(self, temp_dir):
        """Test scanning deeply nested code structures."""
        # Create deeply nested structure
        content = "class A:\n"
        indent = "    "
        for i in range(10):
            content += f"{indent * (i + 1)}class Nested{i}:\n"
            content += f"{indent * (i + 2)}def method{i}(self):\n"
            content += f"{indent * (i + 3)}'''Nested method {i}.'''\n"
            content += f"{indent * (i + 3)}pass\n"
        
        file_path = Path(temp_dir) / "nested.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        # Should handle deep nesting
        assert len(items) > 10  # Classes and methods
        nested_items = [item for item in items if "Nested" in item.qualname]
        assert len(nested_items) > 0
    
    def test_scan_file_with_imports_only(self, temp_dir):
        """Test scanning file with only import statements."""
        content = '''
import os
import sys
from typing import List, Dict
from fastapi import FastAPI
'''
        file_path = Path(temp_dir) / "imports.py"
        file_path.write_text(content)
        
        items = scan_file(str(file_path))
        
        # Should return empty list for import-only files
        assert items == []
    
    @patch('fastdoc.scanner.open')
    def test_scan_file_io_error(self, mock_open):
        """Test handling IO errors during file scanning."""
        mock_open.side_effect = IOError("Permission denied")
        
        with pytest.raises(IOError):
            scan_file("/test/file.py")
    
    def test_scan_file_with_unicode_docstrings(self, temp_dir):
        """Test scanning file with Unicode characters in docstrings."""
        content = '''
def unicode_function():
    """Function with Unicode: café, naïve, 中文, 🚀, ∑."""
    return "unicode"

class UnicodeClass:
    """Class with émojis: 😀😃😄😁 and symbols: ∞≠≤≥."""
    pass
'''
        file_path = Path(temp_dir) / "unicode.py"
        file_path.write_text(content, encoding='utf-8')
        
        items = scan_file(str(file_path))
        
        assert len(items) == 2
        
        func_item = next(item for item in items if item.qualname == "unicode_function")
        assert "café" in func_item.docstring
        assert "🚀" in func_item.docstring
        
        class_item = next(item for item in items if item.qualname == "UnicodeClass")
        assert "😀" in class_item.docstring
        assert "∞" in class_item.docstring