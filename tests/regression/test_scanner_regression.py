"""
Regression tests for scanner functionality.
Tests that ensure existing behavior doesn't change across versions.
"""

import json
import os
from pathlib import Path

import pytest

from fastdoc.scanner import scan_file


@pytest.mark.regression
class TestScannerRegression:
    """Regression tests for core scanner functionality."""
    
    def test_fastapi_example_regression(self, temp_dir):
        """Test that scanning FastAPI example produces expected results."""
        # Create a known FastAPI example
        fastapi_content = '''
from fastapi import FastAPI, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(title="User API", version="1.0.0")

class User(BaseModel):
    """User model for API."""
    id: int
    name: str
    email: str
    age: Optional[int] = None

class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None

@app.get("/")
def root():
    """Root endpoint returning API information."""
    return {"message": "User API", "version": "1.0.0"}

@app.get("/users/", response_model=List[User])
def get_users(skip: int = 0, limit: int = 100):
    """Get list of users with pagination."""
    return []

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    """Get a specific user by ID."""
    if user_id == 999:
        raise HTTPException(status_code=404, detail="User not found")
    return User(id=user_id, name="Test User", email="test@example.com")

@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    """Create a new user."""
    return User(id=1, **user.dict())

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate):
    return User(id=user_id, **user.dict())

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user by ID."""
    return {"message": f"User {user_id} deleted"}

class UserService:
    """Service for managing users."""
    
    def __init__(self, db_connection):
        """Initialize service with database connection."""
        self.db = db_connection
    
    def validate_user(self, user_data: dict) -> bool:
        """Validate user data before saving."""
        return "name" in user_data and "email" in user_data
    
    async def fetch_user_async(self, user_id: int):
        """Fetch user asynchronously from database."""
        return {"id": user_id}
    
    @staticmethod
    def format_user_name(first: str, last: str):
        return f"{first} {last}"
'''
        
        file_path = Path(temp_dir) / "fastapi_example.py"
        file_path.write_text(fastapi_content)
        
        # Scan the file
        items = scan_file(str(file_path))
        
        # Expected results based on current implementation
        expected_items = {
            # Classes
            "User": {"method": "class", "has_docstring": True},
            "UserCreate": {"method": "class", "has_docstring": False},
            "UserService": {"method": "class", "has_docstring": True},
            
            # FastAPI endpoints
            "root": {"method": "GET", "path": "/", "has_docstring": True},
            "get_users": {"method": "GET", "path": "/users/", "has_docstring": True},
            "get_user": {"method": "GET", "path": "/users/{user_id}", "has_docstring": True},
            "create_user": {"method": "POST", "path": "/users/", "has_docstring": True},
            "update_user": {"method": "PUT", "path": "/users/{user_id}", "has_docstring": False},
            "delete_user": {"method": "DELETE", "path": "/users/{user_id}", "has_docstring": True},
            
            # Service methods
            "UserService.__init__": {"method": "function", "has_docstring": True},
            "UserService.validate_user": {"method": "function", "has_docstring": True},
            "UserService.fetch_user_async": {"method": "async_function", "has_docstring": True},
            "UserService.format_user_name": {"method": "function", "has_docstring": False}
        }
        
        # Verify all expected items are found
        found_qualnames = {item.qualname for item in items}
        for expected_qualname in expected_items.keys():
            assert expected_qualname in found_qualnames, f"Missing expected item: {expected_qualname}"
        
        # Verify specific attributes for each item
        items_by_qualname = {item.qualname: item for item in items}
        
        for qualname, expected_attrs in expected_items.items():
            item = items_by_qualname[qualname]
            
            # Check method type
            assert item.method == expected_attrs["method"], \
                f"{qualname}: expected method {expected_attrs['method']}, got {item.method}"
            
            # Check docstring presence
            has_docstring = item.docstring is not None and item.docstring.strip() != ""
            assert has_docstring == expected_attrs["has_docstring"], \
                f"{qualname}: expected has_docstring {expected_attrs['has_docstring']}, got {has_docstring}"
            
            # Check path for endpoints
            if "path" in expected_attrs:
                assert hasattr(item, 'path'), f"{qualname}: missing path attribute"
                assert item.path == expected_attrs["path"], \
                    f"{qualname}: expected path {expected_attrs['path']}, got {item.path}"
        
        # Verify total count matches expectations
        assert len(items) >= len(expected_items), \
            f"Expected at least {len(expected_items)} items, got {len(items)}"
    
    def test_pydantic_models_regression(self, temp_dir):
        """Test that Pydantic model scanning produces consistent results."""
        pydantic_content = '''
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class Address(BaseModel):
    """Address model with validation."""
    street: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1)
    postal_code: str = Field(..., regex=r"^\\d{5}$")
    country: str = "USA"
    
    class Config:
        """Pydantic configuration for Address."""
        schema_extra = {
            "example": {
                "street": "123 Main St",
                "city": "Anytown", 
                "postal_code": "12345"
            }
        }

class Person(BaseModel):
    """Person model with complex validation."""
    id: Optional[int] = None
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: str = Field(..., regex=r"^[^@]+@[^@]+\\.[^@]+$")
    age: int = Field(..., ge=0, le=150)
    addresses: List[Address] = []
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('email')
    def validate_email_domain(cls, v):
        """Validate email domain is allowed."""
        allowed_domains = ['example.com', 'test.org']
        domain = v.split('@')[1]
        if domain not in allowed_domains:
            raise ValueError('Email domain not allowed')
        return v
    
    @validator('age')
    def validate_age_reasonable(cls, v):
        if v < 13:
            raise ValueError('Must be at least 13 years old')
        return v
    
    def full_name(self) -> str:
        """Get full name of person."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def primary_address(self) -> Optional[Address]:
        """Get primary address."""
        return self.addresses[0] if self.addresses else None

class Company(BaseModel):
    name: str
    employees: List[Person] = []
    headquarters: Optional[Address] = None
    
    def add_employee(self, person: Person):
        """Add employee to company."""
        self.employees.append(person)
    
    def employee_count(self) -> int:
        return len(self.employees)
'''
        
        file_path = Path(temp_dir) / "pydantic_models.py"
        file_path.write_text(pydantic_content)
        
        items = scan_file(str(file_path))
        
        # Expected structure
        expected_findings = {
            # Models
            "Address": {"method": "class", "docstring": "Address model with validation."},
            "Address.Config": {"method": "class", "docstring": "Pydantic configuration for Address."},
            "Person": {"method": "class", "docstring": "Person model with complex validation."},
            "Company": {"method": "class", "docstring": None},
            
            # Validators
            "Person.validate_email_domain": {"method": "function", "docstring": "Validate email domain is allowed."},
            "Person.validate_age_reasonable": {"method": "function", "docstring": None},
            
            # Methods and properties
            "Person.full_name": {"method": "function", "docstring": "Get full name of person."},
            "Person.primary_address": {"method": "property", "docstring": "Get primary address."},
            "Company.add_employee": {"method": "function", "docstring": "Add employee to company."},
            "Company.employee_count": {"method": "function", "docstring": None}
        }
        
        items_by_qualname = {item.qualname: item for item in items}
        
        for qualname, expected in expected_findings.items():
            assert qualname in items_by_qualname, f"Expected to find {qualname}"
            item = items_by_qualname[qualname]
            
            assert item.method == expected["method"], \
                f"{qualname}: expected {expected['method']}, got {item.method}"
            
            if expected["docstring"] is not None:
                assert item.docstring == expected["docstring"], \
                    f"{qualname}: docstring mismatch"
            else:
                assert item.docstring is None or item.docstring.strip() == "", \
                    f"{qualname}: expected no docstring, got '{item.docstring}'"
    
    def test_complex_inheritance_regression(self, temp_dir):
        """Test complex inheritance scenarios remain consistent."""
        inheritance_content = '''
from abc import ABC, abstractmethod
from typing import Protocol

class Drawable(Protocol):
    """Protocol for drawable objects."""
    def draw(self) -> None:
        ...

class Shape(ABC):
    """Abstract base shape class."""
    
    def __init__(self, name: str):
        """Initialize shape with name."""
        self.name = name
    
    @abstractmethod
    def area(self) -> float:
        """Calculate area of shape."""
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        """Calculate perimeter of shape."""
        pass
    
    def description(self) -> str:
        """Get shape description."""
        return f"A {self.name} with area {self.area()}"

class Rectangle(Shape):
    """Rectangle implementation of Shape."""
    
    def __init__(self, width: float, height: float):
        """Initialize rectangle with dimensions."""
        super().__init__("rectangle")
        self.width = width
        self.height = height
    
    def area(self) -> float:
        """Calculate rectangle area."""
        return self.width * self.height
    
    def perimeter(self) -> float:
        """Calculate rectangle perimeter."""
        return 2 * (self.width + self.height)

class Square(Rectangle):
    """Square as special case of Rectangle."""
    
    def __init__(self, side: float):
        """Initialize square with side length."""
        super().__init__(side, side)
        self.name = "square"

class DrawableRectangle(Rectangle, Drawable):
    """Rectangle that can be drawn."""
    
    def draw(self) -> None:
        """Draw the rectangle."""
        print(f"Drawing {self.description()}")

class ShapeFactory:
    """Factory for creating shapes."""
    
    @staticmethod
    def create_rectangle(width: float, height: float) -> Rectangle:
        """Create a rectangle."""
        return Rectangle(width, height)
    
    @staticmethod
    def create_square(side: float) -> Square:
        """Create a square."""
        return Square(side)
    
    @classmethod
    def supported_shapes(cls) -> list:
        return ["rectangle", "square"]
'''
        
        file_path = Path(temp_dir) / "inheritance.py"
        file_path.write_text(inheritance_content)
        
        items = scan_file(str(file_path))
        
        # Verify inheritance hierarchy is properly detected
        expected_classes = {
            "Drawable", "Shape", "Rectangle", "Square", 
            "DrawableRectangle", "ShapeFactory"
        }
        
        found_classes = {item.qualname for item in items if item.method == "class"}
        for expected_class in expected_classes:
            assert expected_class in found_classes, f"Missing class: {expected_class}"
        
        # Verify abstract methods are detected
        abstract_methods = {
            item.qualname for item in items 
            if "area" in item.qualname or "perimeter" in item.qualname
        }
        assert len(abstract_methods) >= 4  # Shape.area, Shape.perimeter, Rectangle.area, Rectangle.perimeter
        
        # Verify static and class methods
        factory_methods = [item for item in items if item.qualname.startswith("ShapeFactory.")]
        static_methods = [item for item in factory_methods if "create_" in item.qualname]
        class_methods = [item for item in factory_methods if "supported_shapes" in item.qualname]
        
        assert len(static_methods) == 2
        assert len(class_methods) == 1
    
    def test_coverage_calculation_regression(self, temp_dir):
        """Test that coverage calculations remain consistent."""
        mixed_content = '''
def documented_function():
    """This function has documentation."""
    return "documented"

def undocumented_function():
    return "undocumented"

class DocumentedClass:
    """This class has documentation."""
    
    def documented_method(self):
        """This method has documentation.""" 
        pass
    
    def undocumented_method(self):
        pass

class UndocumentedClass:
    def another_undocumented(self):
        pass
    
    def another_documented(self):
        """Another documented method."""
        pass
'''
        
        file_path = Path(temp_dir) / "mixed_docs.py"
        file_path.write_text(mixed_content)
        
        items = scan_file(str(file_path))
        
        # Calculate expected coverage
        documented_items = [
            item for item in items 
            if item.docstring is not None and item.docstring.strip() != ""
        ]
        
        total_items = len(items)
        documented_count = len(documented_items)
        
        # Expected: 4 documented items out of 8 total = 50% coverage
        assert total_items == 8, f"Expected 8 items, got {total_items}"
        assert documented_count == 4, f"Expected 4 documented items, got {documented_count}"
        
        # Verify specific items are documented
        documented_qualnames = {item.qualname for item in documented_items}
        expected_documented = {
            "documented_function",
            "DocumentedClass", 
            "DocumentedClass.documented_method",
            "UndocumentedClass.another_documented"
        }
        
        assert documented_qualnames == expected_documented, \
            f"Documented items mismatch: {documented_qualnames} != {expected_documented}"


@pytest.mark.regression
class TestServiceIntegrationRegression:
    """Regression tests for service integration behavior."""
    
    def test_scanner_service_output_format_regression(self, sample_project_files, temp_dir):
        """Test that scanner service output format remains consistent."""
        from services.scanner_service import ScannerService
        
        service = ScannerService()
        
        # Mock coverage tracker to isolate scanner behavior
        with pytest.mock.patch('services.scanner_service.coverage_tracker') as mock_tracker:
            mock_tracker.record_coverage.return_value = {"coverage_percent": 60.0}
            
            # Test local project scanning
            items_data, total_files, scan_time = pytest.asyncio.run(
                service.scan_local_project(temp_dir)
            )
        
        # Verify output format consistency
        assert isinstance(items_data, list)
        assert isinstance(total_files, int)
        assert isinstance(scan_time, (int, float))
        assert total_files == len(sample_project_files)
        assert scan_time > 0
        
        # Verify item structure
        for item in items_data:
            assert isinstance(item, dict)
            required_fields = ["module", "qualname", "method", "lineno"]
            for field in required_fields:
                assert field in item, f"Missing required field: {field}"
    
    def test_coverage_tracker_statistics_regression(self, sample_documentation_items):
        """Test that coverage statistics calculations remain consistent."""
        from services.coverage_tracker import CoverageTracker
        
        tracker = CoverageTracker()
        record = tracker.record_coverage(sample_documentation_items, "/test/project")
        
        # Verify expected statistics
        assert record["total_items"] == 4
        assert record["documented_items"] == 2
        assert record["coverage_percent"] == 50.0
        
        # Verify by-type breakdown
        assert "GET" in record["coverage_by_type"]
        assert record["coverage_by_type"]["GET"]["total"] == 2
        assert record["coverage_by_type"]["GET"]["documented"] == 1
        assert record["coverage_by_type"]["GET"]["coverage"] == 50.0
        
        # Verify by-module breakdown  
        assert "main" in record["coverage_by_module"]
        assert record["coverage_by_module"]["main"]["total"] == 4
        assert record["coverage_by_module"]["main"]["documented"] == 2
        assert record["coverage_by_module"]["main"]["coverage"] == 50.0


@pytest.mark.regression
class TestAPIResponseRegression:
    """Regression tests for API response formats."""
    
    def test_scan_endpoint_response_format(self, test_client, sample_project_files):
        """Test that scan endpoint response format is consistent."""
        from io import BytesIO
        from pathlib import Path
        
        # Prepare file uploads
        files = []
        for file_path in sample_project_files:
            with open(file_path, 'rb') as f:
                content = f.read()
            files.append(
                ("files", (Path(file_path).name, BytesIO(content), "text/x-python"))
            )
        
        with pytest.mock.patch('services.scanner_service.coverage_tracker'):
            response = test_client.post(
                "/api/scan",
                data={"project_path": "test_project"},
                files=files
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        required_fields = ["success", "message", "items", "total_files", "scan_time"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert data["success"] is True
        assert isinstance(data["message"], str)
        assert isinstance(data["items"], list)
        assert isinstance(data["total_files"], int)
        assert isinstance(data["scan_time"], (int, float))
    
    def test_confluence_status_response_format(self, test_client):
        """Test that Confluence status response format is consistent."""
        with pytest.mock.patch('services.confluence_service.confluence_service') as mock_service:
            mock_service.is_enabled.return_value = True
            
            response = test_client.get("/api/confluence/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "enabled" in data
        assert isinstance(data["enabled"], bool)
        
        if data["enabled"]:
            assert "url" in data
            assert "space_key" in data


@pytest.mark.regression 
class TestPerformanceRegression:
    """Regression tests to ensure performance doesn't degrade."""
    
    @pytest.mark.slow
    def test_large_file_scanning_performance(self, temp_dir):
        """Test that scanning large files doesn't become significantly slower."""
        import time
        
        # Create a large file with many functions
        lines = ["# Large test file"]
        for i in range(500):
            lines.extend([
                f"def function_{i}():",
                f'    """Function number {i}."""',
                f"    return {i}",
                ""
            ])
        
        large_file = Path(temp_dir) / "large_file.py"
        large_file.write_text("\n".join(lines))
        
        # Time the scanning
        start_time = time.time()
        items = scan_file(str(large_file))
        end_time = time.time()
        
        scan_duration = end_time - start_time
        
        # Performance regression check
        assert len(items) == 500, "Should find all 500 functions"
        assert scan_duration < 5.0, f"Scanning took too long: {scan_duration}s"
        
        # Verify quality of results
        documented_items = [item for item in items if item.docstring]
        assert len(documented_items) == 500, "All functions should be documented"
    
    @pytest.mark.slow 
    def test_many_files_scanning_performance(self, temp_dir):
        """Test scanning many small files doesn't become significantly slower."""
        import time
        from services.scanner_service import ScannerService
        
        # Create many small files
        file_paths = []
        for i in range(50):
            file_content = f'''
def function_in_file_{i}():
    """Function in file {i}."""
    return {i}

class ClassInFile{i}:
    """Class in file {i}.""" 
    pass
'''
            file_path = Path(temp_dir) / f"file_{i}.py"
            file_path.write_text(file_content)
            file_paths.append(str(file_path))
        
        service = ScannerService()
        
        with pytest.mock.patch('services.scanner_service.coverage_tracker'):
            start_time = time.time()
            items_data, total_files, scan_time = pytest.asyncio.run(
                service.scan_local_project(temp_dir)
            )
            end_time = time.time()
        
        total_duration = end_time - start_time
        
        # Performance checks
        assert total_files == 50, "Should scan all 50 files"
        assert len(items_data) == 100, "Should find 2 items per file"
        assert total_duration < 10.0, f"Total scanning took too long: {total_duration}s"