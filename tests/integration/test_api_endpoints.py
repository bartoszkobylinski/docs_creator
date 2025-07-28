"""
Integration tests for API endpoints.
Tests the full API functionality with real services but controlled data.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.integration
class TestReportEndpoints:
    """Integration tests for report-related endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_get_report_status_no_report(self, setup_test_environment):
        """Test getting report status when no report exists."""
        response = self.client.get("/api/report/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
    
    def test_get_report_status_with_report(self, json_report_file, setup_test_environment):
        """Test getting report status when report exists."""
        # Copy report to expected location
        with patch('core.config.settings') as mock_settings:
            mock_settings.report_file_path = json_report_file
            
            response = self.client.get("/api/report/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
    
    def test_get_report_data_success(self, json_report_file, sample_documentation_items):
        """Test getting report data successfully."""
        with patch('core.config.settings') as mock_settings:
            mock_settings.report_file_path = json_report_file
            
            response = self.client.get("/api/report/data")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(sample_documentation_items)
        assert data[0]["qualname"] == "root"
    
    def test_get_report_data_not_found(self, setup_test_environment):
        """Test getting report data when file doesn't exist."""
        response = self.client.get("/api/report/data")
        
        # Should handle missing file gracefully
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestScanEndpoints:
    """Integration tests for scanning endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    @pytest.mark.asyncio
    async def test_scan_uploaded_files_success(self, sample_project_files):
        """Test scanning uploaded Python files."""
        # Prepare file uploads
        files = []
        for file_path in sample_project_files:
            with open(file_path, 'rb') as f:
                content = f.read()
            files.append(
                ("files", (Path(file_path).name, BytesIO(content), "text/x-python"))
            )
        
        # Mock coverage tracker to avoid file operations
        with patch('services.scanner_service.coverage_tracker') as mock_tracker:
            mock_tracker.record_coverage.return_value = {"coverage_percent": 65.0}
            
            response = self.client.post(
                "/api/scan",
                data={"project_path": "test_project"},
                files=files
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "Successfully scanned" in data["message"]
        assert len(data["items"]) > 0
        assert data["total_files"] == len(sample_project_files)
        assert data["scan_time"] > 0
        
        # Verify some expected items are found
        item_names = [item["qualname"] for item in data["items"]]
        assert any("root" in name for name in item_names)
    
    def test_scan_uploaded_files_no_files(self):
        """Test scanning with no files uploaded."""
        response = self.client.post(
            "/api/scan",
            data={"project_path": "test_project"},
            files=[]
        )
        
        assert response.status_code == 400
        assert "No Python files found" in response.json()["detail"]
    
    def test_scan_uploaded_files_non_python(self):
        """Test scanning with non-Python files."""
        files = [
            ("files", ("readme.txt", BytesIO(b"This is not Python"), "text/plain"))
        ]
        
        response = self.client.post(
            "/api/scan",
            data={"project_path": "test_project"},
            files=files
        )
        
        assert response.status_code == 400
        assert "No Python files found" in response.json()["detail"]
    
    def test_scan_local_project_success(self, sample_project_files, temp_dir):
        """Test scanning a local project directory."""
        with patch('services.scanner_service.coverage_tracker') as mock_tracker:
            mock_tracker.record_coverage.return_value = {"coverage_percent": 70.0}
            
            response = self.client.post(
                "/api/scan-local",
                json={"project_path": temp_dir}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["items"]) > 0
        assert data["total_files"] == len(sample_project_files)
    
    def test_scan_local_project_missing_path(self):
        """Test scanning local project without path."""
        response = self.client.post(
            "/api/scan-local",
            json={}
        )
        
        assert response.status_code == 400
        assert "project_path is required" in response.json()["detail"]
    
    def test_scan_local_project_nonexistent_path(self):
        """Test scanning nonexistent local path."""
        response = self.client.post(
            "/api/scan-local",
            json={"project_path": "/nonexistent/path"}
        )
        
        assert response.status_code == 400
        assert "Path does not exist" in response.json()["detail"]


@pytest.mark.integration
class TestDocstringEndpoints:
    """Integration tests for docstring management endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_save_docstring_success(self, temp_dir):
        """Test saving a docstring to file."""
        # Create a test file
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text('''
def test_function():
    pass
''')
        
        item = {
            "qualname": "test_function",
            "file_path": str(test_file),
            "lineno": 2,
            "method": "function"
        }
        
        request_data = {
            "item": item,
            "docstring": "Test docstring for the function."
        }
        
        with patch('services.docstring_service.docstring_service') as mock_service:
            mock_service.save_docstring.return_value = {
                "success": True,
                "message": "Docstring saved successfully"
            }
            
            response = self.client.post(
                "/api/docstring/save",
                json=request_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_generate_docstring_success(self):
        """Test generating AI docstring."""
        item = {
            "qualname": "test_function",
            "file_path": "/test/file.py",
            "method": "function"
        }
        
        request_data = {"item": item}
        
        with patch('services.docstring_service.docstring_service') as mock_service:
            mock_service.generate_ai_docstring.return_value = "Generated AI docstring."
            
            response = self.client.post(
                "/api/docstring/generate",
                json=request_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["docstring"] == "Generated AI docstring."
    
    def test_get_project_files_success(self, temp_dir, sample_project_files):
        """Test getting project files list."""
        with patch('services.scanner_service.scanner_service') as mock_service:
            mock_service.get_project_files.return_value = [
                {"name": "main.py", "path": "main.py", "full_path": "/test/main.py"},
                {"name": "models.py", "path": "models.py", "full_path": "/test/models.py"}
            ]
            
            response = self.client.get("/api/project/files")
        
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert len(data["files"]) == 2
    
    def test_get_project_files_no_project(self):
        """Test getting project files when no project loaded."""
        with patch('services.scanner_service.scanner_service') as mock_service:
            from fastapi import HTTPException
            mock_service.get_project_files.side_effect = HTTPException(
                status_code=404, detail="No project loaded"
            )
            
            response = self.client.get("/api/project/files")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestConfluenceEndpoints:
    """Integration tests for Confluence integration endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_get_confluence_status_enabled(self, mock_settings):
        """Test getting Confluence status when enabled."""
        with patch('services.confluence_service.confluence_service') as mock_service:
            mock_service.is_enabled.return_value = True
            
            response = self.client.get("/api/confluence/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert "url" in data
        assert "space_key" in data
    
    def test_get_confluence_status_disabled(self):
        """Test getting Confluence status when disabled."""
        with patch('services.confluence_service.confluence_service') as mock_service:
            mock_service.is_enabled.return_value = False
            
            response = self.client.get("/api/confluence/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
    
    def test_publish_endpoint_to_confluence_success(self, mock_settings):
        """Test publishing endpoint to Confluence successfully."""
        endpoint_data = {
            "method": "GET",
            "path": "/test",
            "qualname": "test_endpoint",
            "docstring": "Test endpoint documentation"
        }
        
        with patch('services.confluence_service.confluence_service') as mock_service:
            mock_service.is_enabled.return_value = True
            mock_service.publish_endpoint_doc.return_value = {"id": "123456"}
            
            response = self.client.post(
                "/api/confluence/publish-endpoint",
                json=endpoint_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["page_id"] == "123456"
        assert "page_url" in data
    
    def test_publish_endpoint_confluence_disabled(self):
        """Test publishing endpoint when Confluence is disabled."""
        endpoint_data = {"method": "GET", "path": "/test"}
        
        with patch('services.confluence_service.confluence_service') as mock_service:
            mock_service.is_enabled.return_value = False
            
            response = self.client.post(
                "/api/confluence/publish-endpoint",
                json=endpoint_data
            )
        
        assert response.status_code == 400
        assert "not configured" in response.json()["detail"]
    
    def test_publish_coverage_to_confluence_success(self, mock_settings, sample_documentation_items):
        """Test publishing coverage report to Confluence."""
        request_data = {
            "items": sample_documentation_items,
            "title_suffix": "2024-01-15"
        }
        
        with patch('services.confluence_service.confluence_service') as mock_service:
            mock_service.is_enabled.return_value = True
            mock_service.publish_coverage_report.return_value = {"id": "789012"}
            
            response = self.client.post(
                "/api/confluence/publish-coverage",
                json=request_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["page_id"] == "789012"
    
    def test_publish_coverage_confluence_disabled(self, sample_documentation_items):
        """Test publishing coverage when Confluence is disabled."""
        request_data = {"items": sample_documentation_items}
        
        with patch('services.confluence_service.confluence_service') as mock_service:
            mock_service.is_enabled.return_value = False
            
            response = self.client.post(
                "/api/confluence/publish-coverage",
                json=request_data
            )
        
        assert response.status_code == 400
        assert "not configured" in response.json()["detail"]


@pytest.mark.integration
class TestCoverageEndpoints:
    """Integration tests for coverage tracking endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_get_coverage_history_success(self):
        """Test getting coverage history."""
        mock_history = [
            {
                "timestamp": "2024-01-15T10:30:00",
                "project_path": "/test/project",
                "coverage_percent": 65.0,
                "total_items": 10
            }
        ]
        
        with patch('services.coverage_tracker.coverage_tracker') as mock_tracker:
            mock_tracker.get_coverage_history.return_value = mock_history
            
            response = self.client.get("/api/coverage/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "total_records" in data
        assert len(data["history"]) == 1
    
    def test_get_coverage_history_with_filters(self):
        """Test getting coverage history with filters."""
        response = self.client.get(
            "/api/coverage/history",
            params={"project_path": "/test/project", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
    
    def test_get_coverage_trends_success(self):
        """Test getting coverage trends."""
        mock_trends = {
            "trend": "improving",
            "coverage_change": 15.0,
            "period_days": 30,
            "records_found": 5
        }
        
        with patch('services.coverage_tracker.coverage_tracker') as mock_tracker:
            mock_tracker.get_coverage_trends.return_value = mock_trends
            
            response = self.client.get("/api/coverage/trends")
        
        assert response.status_code == 200
        data = response.json()
        assert data["trend"] == "improving"
        assert data["coverage_change"] == 15.0
    
    def test_get_coverage_trends_with_params(self):
        """Test getting coverage trends with parameters."""
        response = self.client.get(
            "/api/coverage/trends",
            params={"project_path": "/test/project", "days": 7}
        )
        
        assert response.status_code == 200
    
    def test_get_progress_report_success(self):
        """Test getting progress report."""
        mock_report = {
            "generated_at": "2024-01-15T10:30:00",
            "project_path": "/test/project",
            "latest_scan": {"coverage_percent": 70.0},
            "trends": {"7_days": {"trend": "stable"}},
            "recommendations": ["Focus on documenting GET endpoints"]
        }
        
        with patch('services.coverage_tracker.coverage_tracker') as mock_tracker:
            mock_tracker.generate_progress_report.return_value = mock_report
            
            response = self.client.get("/api/coverage/progress-report")
        
        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "latest_scan" in data
        assert "trends" in data
        assert "recommendations" in data


@pytest.mark.integration
class TestAPIErrorHandling:
    """Integration tests for API error handling."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request."""
        response = self.client.post(
            "/api/scan-local",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        response = self.client.post(
            "/api/docstring/save",
            json={"docstring": "test"}  # Missing 'item' field
        )
        
        assert response.status_code == 422
    
    def test_service_exception_handling(self):
        """Test handling of service exceptions."""
        with patch('services.scanner_service.scanner_service') as mock_service:
            mock_service.scan_local_project.side_effect = Exception("Service error")
            
            response = self.client.post(
                "/api/scan-local",
                json={"project_path": "/test/path"}
            )
        
        assert response.status_code == 500
        assert "Service error" in response.json()["detail"]
    
    def test_confluence_service_error(self):
        """Test handling of Confluence service errors."""
        with patch('services.confluence_service.confluence_service') as mock_service:
            mock_service.is_enabled.return_value = True
            mock_service.publish_endpoint_doc.side_effect = Exception("Confluence API error")
            
            response = self.client.post(
                "/api/confluence/publish-endpoint",
                json={"method": "GET", "path": "/test"}
            )
        
        assert response.status_code == 500
        assert "Confluence API error" in response.json()["detail"]


@pytest.mark.integration 
@pytest.mark.slow
class TestEndToEndWorkflows:
    """End-to-end integration tests for complete workflows."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_complete_scan_and_edit_workflow(self, sample_project_files, temp_dir):
        """Test complete workflow: scan -> view results -> edit docstring."""
        # Step 1: Scan local project
        with patch('services.scanner_service.coverage_tracker') as mock_tracker:
            mock_tracker.record_coverage.return_value = {"coverage_percent": 50.0}
            
            scan_response = self.client.post(
                "/api/scan-local",
                json={"project_path": temp_dir}
            )
        
        assert scan_response.status_code == 200
        scan_data = scan_response.json()
        items = scan_data["items"]
        
        # Step 2: Get report status
        status_response = self.client.get("/api/report/status")
        assert status_response.status_code == 200
        
        # Step 3: Edit a docstring
        item_to_edit = next(item for item in items if not item.get("docstring"))
        
        with patch('services.docstring_service.docstring_service') as mock_service:
            mock_service.save_docstring.return_value = {
                "success": True,
                "message": "Saved successfully"
            }
            
            edit_response = self.client.post(
                "/api/docstring/save",
                json={
                    "item": item_to_edit,
                    "docstring": "New documentation for this function."
                }
            )
        
        assert edit_response.status_code == 200
        edit_data = edit_response.json()
        assert edit_data["success"] is True
    
    def test_scan_and_confluence_publish_workflow(self, sample_project_files, temp_dir, mock_settings):
        """Test workflow: scan -> publish to Confluence."""
        # Step 1: Scan project
        with patch('services.scanner_service.coverage_tracker') as mock_tracker:
            mock_tracker.record_coverage.return_value = {"coverage_percent": 60.0}
            
            scan_response = self.client.post(
                "/api/scan-local",
                json={"project_path": temp_dir}
            )
        
        assert scan_response.status_code == 200
        items = scan_response.json()["items"]
        
        # Step 2: Check Confluence status
        with patch('services.confluence_service.confluence_service') as mock_service:
            mock_service.is_enabled.return_value = True
            
            status_response = self.client.get("/api/confluence/status")
            assert status_response.status_code == 200
            
            # Step 3: Publish coverage report
            mock_service.publish_coverage_report.return_value = {"id": "report123"}
            
            publish_response = self.client.post(
                "/api/confluence/publish-coverage",
                json={"items": items, "title_suffix": "Integration Test"}
            )
        
        assert publish_response.status_code == 200
        publish_data = publish_response.json()
        assert publish_data["success"] is True