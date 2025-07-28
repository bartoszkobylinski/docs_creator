"""
Unit tests for Confluence service.
Tests Confluence integration with mocked Atlassian API calls.
"""

from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import pytest

from services.confluence_service import ConfluenceService, confluence_service


@pytest.mark.unit
class TestConfluenceService:
    """Test cases for ConfluenceService."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = ConfluenceService()
    
    @patch('services.confluence_service.settings')
    def test_init_with_valid_credentials(self, mock_settings):
        """Test initialization with valid Confluence credentials."""
        mock_settings.CONFLUENCE_URL = "https://test.atlassian.net"
        mock_settings.CONFLUENCE_USERNAME = "test@example.com"
        mock_settings.CONFLUENCE_API_TOKEN = "test-token"
        mock_settings.CONFLUENCE_SPACE_KEY = "TESTSPACE"
        
        with patch('services.confluence_service.Confluence') as mock_confluence_class:
            mock_confluence_instance = Mock()
            mock_confluence_class.return_value = mock_confluence_instance
            
            service = ConfluenceService()
            
            assert service.enabled is True
            assert service.confluence == mock_confluence_instance
            assert service.space_key == "TESTSPACE"
            
            mock_confluence_class.assert_called_once_with(
                url="https://test.atlassian.net",
                username="test@example.com", 
                password="test-token"
            )
    
    @patch('services.confluence_service.settings')
    def test_init_with_missing_credentials(self, mock_settings):
        """Test initialization with missing credentials disables service."""
        mock_settings.CONFLUENCE_URL = None
        mock_settings.CONFLUENCE_USERNAME = "test@example.com"
        mock_settings.CONFLUENCE_API_TOKEN = "test-token"
        mock_settings.CONFLUENCE_SPACE_KEY = "TESTSPACE"
        
        service = ConfluenceService()
        
        assert service.enabled is False
        assert service.confluence is None
    
    @patch('services.confluence_service.settings')
    def test_init_with_confluence_exception(self, mock_settings):
        """Test initialization handles Confluence connection errors gracefully."""
        mock_settings.CONFLUENCE_URL = "https://test.atlassian.net"
        mock_settings.CONFLUENCE_USERNAME = "test@example.com"
        mock_settings.CONFLUENCE_API_TOKEN = "invalid-token"
        mock_settings.CONFLUENCE_SPACE_KEY = "TESTSPACE"
        
        with patch('services.confluence_service.Confluence') as mock_confluence_class:
            mock_confluence_class.side_effect = Exception("Connection failed")
            
            service = ConfluenceService()
            
            assert service.enabled is False
            assert service.confluence is None
    
    def test_is_enabled_true(self):
        """Test is_enabled returns True when service is enabled."""
        self.service.enabled = True
        assert self.service.is_enabled() is True
    
    def test_is_enabled_false(self):
        """Test is_enabled returns False when service is disabled."""
        self.service.enabled = False
        assert self.service.is_enabled() is False
    
    def test_publish_endpoint_doc_disabled_service(self):
        """Test publishing endpoint when service is disabled raises exception."""
        self.service.enabled = False
        
        with pytest.raises(Exception) as exc_info:
            self.service.publish_endpoint_doc({"method": "GET", "path": "/test"})
        
        assert "not enabled" in str(exc_info.value)
    
    def test_publish_endpoint_doc_success(self, mock_confluence_api):
        """Test successful endpoint documentation publishing."""
        self.service.enabled = True
        self.service.confluence = mock_confluence_api
        self.service.space_key = "TESTSPACE"
        
        endpoint_data = {
            "method": "GET",
            "path": "/users/{user_id}",
            "qualname": "get_user",
            "docstring": "Get user by ID.",
            "module": "api",
            "lineno": 10
        }
        
        result = self.service.publish_endpoint_doc(endpoint_data)
        
        # Verify page creation was called
        mock_confluence_api.create_page.assert_called_once()
        call_args = mock_confluence_api.create_page.call_args
        
        assert call_args[1]["space"] == "TESTSPACE"
        assert "get_user" in call_args[1]["title"]
        assert "GET /users/{user_id}" in call_args[1]["body"]
        
        assert result["id"] == "123456"
    
    def test_publish_endpoint_doc_update_existing(self, mock_confluence_api):
        """Test updating existing endpoint documentation."""
        self.service.enabled = True
        self.service.confluence = mock_confluence_api
        self.service.space_key = "TESTSPACE"
        
        # Mock existing page found
        mock_confluence_api.get_page_by_title.return_value = {
            "id": "existing-123",
            "version": {"number": 1}
        }
        
        endpoint_data = {
            "method": "POST",
            "path": "/users",
            "qualname": "create_user",
            "docstring": "Create a new user.",
            "module": "api",
            "lineno": 20
        }
        
        result = self.service.publish_endpoint_doc(endpoint_data)
        
        # Should update instead of create
        mock_confluence_api.update_page.assert_called_once()
        mock_confluence_api.create_page.assert_not_called()
    
    def test_publish_coverage_report_success(self, mock_confluence_api, sample_documentation_items):
        """Test successful coverage report publishing."""
        self.service.enabled = True
        self.service.confluence = mock_confluence_api
        self.service.space_key = "TESTSPACE"
        
        result = self.service.publish_coverage_report(sample_documentation_items, "2024-01-15")
        
        # Verify page creation
        mock_confluence_api.create_page.assert_called_once()
        call_args = mock_confluence_api.create_page.call_args
        
        assert call_args[1]["space"] == "TESTSPACE"
        assert "Coverage Report" in call_args[1]["title"]
        assert "2024-01-15" in call_args[1]["title"]
        
        # Verify report content contains expected elements
        body = call_args[1]["body"]
        assert "Coverage Statistics" in body
        assert "75%" in body  # Overall coverage from sample data
        assert "GET" in body
        assert "function" in body
    
    def test_publish_coverage_report_disabled_service(self, sample_documentation_items):
        """Test publishing coverage report when service is disabled."""
        self.service.enabled = False
        
        with pytest.raises(Exception) as exc_info:
            self.service.publish_coverage_report(sample_documentation_items)
        
        assert "not enabled" in str(exc_info.value)
    
    def test_generate_endpoint_html_content(self):
        """Test HTML generation for endpoint documentation."""
        endpoint_data = {
            "method": "PUT",
            "path": "/users/{user_id}",
            "qualname": "update_user",
            "docstring": "Update user information.\n\nArgs:\n    user_id: The user ID\n    data: User data\n\nReturns:\n    Updated user object",
            "module": "users",
            "lineno": 45,
            "has_type_hints": True,
            "dependencies": ["authenticate", "validate_user"],
            "tags": ["users", "crud"]
        }
        
        html = self.service._generate_endpoint_html(endpoint_data)
        
        # Verify HTML structure
        assert "<h1>PUT /users/{user_id}</h1>" in html
        assert "update_user" in html
        assert "Update user information" in html
        assert "users.py:45" in html
        assert "authenticate" in html
        assert "validate_user" in html
        assert "users" in html and "crud" in html
    
    def test_generate_coverage_report_html(self, sample_documentation_items):
        """Test HTML generation for coverage report."""
        html = self.service._generate_coverage_report_html(sample_documentation_items, "Test Report")
        
        # Verify report structure
        assert "<h1>Documentation Coverage Report: Test Report</h1>" in html
        assert "Coverage Statistics" in html
        assert "75%" in html  # Overall coverage
        assert "GET" in html
        assert "root" in html
        assert "get_user" in html
        
        # Verify table structure
        assert "<table" in html
        assert "<th>Module</th>" in html
        assert "<th>Function/Endpoint</th>" in html
        assert "<th>Type</th>" in html
        assert "<th>Documentation Status</th>" in html
    
    def test_calculate_coverage_statistics(self, sample_documentation_items):
        """Test coverage statistics calculation."""
        stats = self.service._calculate_coverage_stats(sample_documentation_items)
        
        assert stats["total_items"] == 4
        assert stats["documented_items"] == 2  # root and create_user have docstrings
        assert stats["coverage_percent"] == 50.0
        
        # Verify by-type breakdown
        assert "GET" in stats["by_type"]
        assert "function" in stats["by_type"]
        assert stats["by_type"]["GET"]["total"] == 2
        assert stats["by_type"]["GET"]["documented"] == 1
        assert stats["by_type"]["function"]["total"] == 2
        assert stats["by_type"]["function"]["documented"] == 1
    
    def test_build_page_title_endpoint(self):
        """Test page title building for endpoints."""
        endpoint_data = {
            "method": "DELETE",
            "path": "/users/{user_id}",
            "qualname": "delete_user"
        }
        
        title = self.service._build_page_title(endpoint_data)
        assert title == "API: DELETE /users/{user_id} (delete_user)"
    
    def test_build_page_title_function(self):
        """Test page title building for functions."""
        function_data = {
            "qualname": "UserService.validate_email",
            "module": "services"
        }
        
        title = self.service._build_page_title(function_data)
        assert title == "Function: UserService.validate_email"
    
    def test_confluence_api_error_handling(self, mock_confluence_api):
        """Test error handling for Confluence API failures."""
        self.service.enabled = True
        self.service.confluence = mock_confluence_api
        self.service.space_key = "TESTSPACE"
        
        # Mock API error
        mock_confluence_api.create_page.side_effect = Exception("API Error")
        
        endpoint_data = {"method": "GET", "path": "/test", "qualname": "test"}
        
        with pytest.raises(Exception) as exc_info:
            self.service.publish_endpoint_doc(endpoint_data)
        
        assert "API Error" in str(exc_info.value)
    
    @patch('services.confluence_service.datetime')
    def test_timestamp_in_reports(self, mock_datetime, mock_confluence_api, sample_documentation_items):
        """Test that reports include proper timestamps."""
        fixed_time = datetime(2024, 1, 15, 10, 30, 0)
        mock_datetime.now.return_value = fixed_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        self.service.enabled = True
        self.service.confluence = mock_confluence_api
        self.service.space_key = "TESTSPACE"
        
        self.service.publish_coverage_report(sample_documentation_items)
        
        call_args = mock_confluence_api.create_page.call_args
        body = call_args[1]["body"]
        
        assert "Generated: 2024-01-15 10:30:00" in body
    
    def test_global_confluence_service_instance(self):
        """Test that the global confluence service instance is properly configured."""
        assert confluence_service is not None
        assert isinstance(confluence_service, ConfluenceService)


@pytest.mark.unit
class TestConfluenceServiceHTML:
    """Test HTML generation methods in detail."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = ConfluenceService()
    
    def test_html_escaping_in_docstrings(self):
        """Test that HTML characters in docstrings are properly escaped."""
        endpoint_data = {
            "method": "POST",
            "path": "/test",
            "qualname": "test_function",
            "docstring": "Test with <script>alert('xss')</script> and & symbols",
            "module": "test"
        }
        
        html = self.service._generate_endpoint_html(endpoint_data)
        
        # Verify HTML escaping
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "&amp;" in html
    
    def test_markdown_style_docstring_formatting(self):
        """Test formatting of markdown-style docstrings."""
        endpoint_data = {
            "method": "GET",
            "path": "/api/test",
            "qualname": "test_endpoint",
            "docstring": """Get test data.

Args:
    param1 (str): First parameter
    param2 (int): Second parameter

Returns:
    dict: Test response data

Raises:
    ValueError: If parameters are invalid""",
            "module": "api"
        }
        
        html = self.service._generate_endpoint_html(endpoint_data)
        
        # Verify structured formatting
        assert "Get test data." in html
        assert "Args:" in html
        assert "Returns:" in html
        assert "Raises:" in html
        assert "param1 (str)" in html
        assert "ValueError" in html
    
    def test_coverage_report_color_coding(self, sample_documentation_items):
        """Test that coverage report includes proper color coding."""
        html = self.service._generate_coverage_report_html(sample_documentation_items, "Color Test")
        
        # Should have different styling for documented vs undocumented
        assert 'style="color: green"' in html or 'class="documented"' in html
        assert 'style="color: red"' in html or 'class="undocumented"' in html
    
    def test_large_dataset_handling(self):
        """Test handling of large documentation datasets."""
        # Create large dataset
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                "module": f"module_{i}",
                "qualname": f"function_{i}",
                "method": "GET" if i % 2 == 0 else "function",
                "docstring": f"Function {i} documentation" if i % 3 == 0 else None,
                "lineno": i * 10
            })
        
        # Should handle large datasets without errors
        html = self.service._generate_coverage_report_html(large_dataset, "Large Dataset")
        
        assert len(html) > 1000  # Should generate substantial HTML
        assert "function_50" in html
        assert "function_99" in html