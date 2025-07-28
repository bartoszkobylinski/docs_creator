"""
Pytest configuration and shared fixtures.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from core.config import settings


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_project_files(temp_dir):
    """Create sample Python files for testing."""
    files = {
        "main.py": '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Hello World"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

class UserService:
    def create_user(self, name: str):
        """Create a new user."""
        pass
        
    def get_user(self, user_id: int):
        pass
''',
        "models.py": '''
from pydantic import BaseModel

class User(BaseModel):
    """User model."""
    id: int
    name: str
    email: str

class Product:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price
        
    def calculate_discount(self, percentage: float):
        """Calculate discount price."""
        return self.price * (1 - percentage / 100)
''',
        "utils.py": '''
def format_name(first: str, last: str):
    return f"{first} {last}"

def validate_email(email: str):
    """Validate email format."""
    return "@" in email and "." in email.split("@")[1]
'''
    }
    
    file_paths = []
    for filename, content in files.items():
        file_path = Path(temp_dir) / filename
        file_path.write_text(content)
        file_paths.append(str(file_path))
    
    return file_paths


@pytest.fixture
def sample_documentation_items():
    """Sample documentation items for testing."""
    return [
        {
            "module": "main",
            "qualname": "root",
            "method": "GET",
            "path": "/",
            "file_path": "/test/main.py",
            "lineno": 5,
            "docstring": "Root endpoint.",
            "coverage_score": 85.0,
            "quality_score": 78.0,
            "has_type_hints": True,
            "dependencies": [],
            "tags": []
        },
        {
            "module": "main",
            "qualname": "get_user",
            "method": "GET", 
            "path": "/users/{user_id}",
            "file_path": "/test/main.py",
            "lineno": 10,
            "docstring": None,
            "coverage_score": 45.0,
            "quality_score": 30.0,
            "has_type_hints": True,
            "dependencies": [],
            "tags": []
        },
        {
            "module": "main",
            "qualname": "UserService.create_user",
            "method": "function",
            "file_path": "/test/main.py",
            "lineno": 15,
            "docstring": "Create a new user.",
            "coverage_score": 75.0,
            "quality_score": 65.0,
            "has_type_hints": True,
            "dependencies": [],
            "tags": []
        },
        {
            "module": "main",
            "qualname": "UserService.get_user",
            "method": "function",
            "file_path": "/test/main.py",
            "lineno": 19,
            "docstring": None,
            "coverage_score": 20.0,
            "quality_score": 15.0,
            "has_type_hints": True,
            "dependencies": [],
            "tags": []
        }
    ]


@pytest.fixture
def mock_confluence_api():
    """Mock Confluence API responses."""
    mock_confluence = Mock()
    mock_confluence.get_space.return_value = {"key": "TESTSPACE"}
    mock_confluence.create_page.return_value = {
        "id": "123456",
        "title": "Test Page",
        "_links": {"webui": "/wiki/spaces/TESTSPACE/pages/123456"}
    }
    mock_confluence.update_page.return_value = {
        "id": "123456", 
        "title": "Updated Test Page"
    }
    return mock_confluence


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI API responses."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="Generated docstring for the function."))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_scan_result():
    """Sample scan result data."""
    return {
        "success": True,
        "message": "Successfully scanned 3 files",
        "items": [
            {
                "module": "main",
                "qualname": "root",
                "method": "GET",
                "docstring": "Root endpoint.",
                "coverage_score": 85.0
            }
        ],
        "total_files": 3,
        "scan_time": 1.23
    }


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch.object(settings, 'CONFLUENCE_URL', 'https://test.atlassian.net'), \
         patch.object(settings, 'CONFLUENCE_USERNAME', 'test@example.com'), \
         patch.object(settings, 'CONFLUENCE_API_TOKEN', 'test-token'), \
         patch.object(settings, 'CONFLUENCE_SPACE_KEY', 'TESTSPACE'), \
         patch.object(settings, 'REPORTS_DIR', '/tmp/test-reports'):
        yield settings


@pytest.fixture(autouse=True)
def setup_test_environment(temp_dir):
    """Setup test environment variables and directories."""
    # Set test-specific environment
    original_reports_dir = getattr(settings, 'REPORTS_DIR', None)
    original_default_report = getattr(settings, 'DEFAULT_REPORT_FILE', None)
    
    test_reports_dir = Path(temp_dir) / "reports"
    test_reports_dir.mkdir(exist_ok=True)
    
    settings.REPORTS_DIR = str(test_reports_dir)
    settings.DEFAULT_REPORT_FILE = "test_report.json"
    
    yield
    
    # Cleanup
    if original_reports_dir:
        settings.REPORTS_DIR = original_reports_dir
    if original_default_report:
        settings.DEFAULT_REPORT_FILE = original_default_report


@pytest.fixture
def json_report_file(temp_dir, sample_documentation_items):
    """Create a sample JSON report file."""
    report_path = Path(temp_dir) / "test_report.json"
    with open(report_path, 'w') as f:
        json.dump(sample_documentation_items, f, indent=2)
    return str(report_path)


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration  
pytest.mark.regression = pytest.mark.regression
pytest.mark.slow = pytest.mark.slow