"""
Unit tests for scanner service.
Tests the scanning functionality with real file processing but mocked external dependencies.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import List

import pytest
from fastapi import HTTPException, UploadFile

from services.scanner_service import ScannerService, scanner_service
from fastdoc.scanner import scan_file


@pytest.mark.unit
class TestScannerService:
    """Test cases for ScannerService."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = ScannerService()
    
    @pytest.mark.asyncio
    async def test_scan_uploaded_files_success(self, sample_project_files, temp_dir):
        """Test successful scanning of uploaded files."""
        # Create mock upload files
        mock_files = []
        for file_path in sample_project_files:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = os.path.basename(file_path)
            
            # Read actual file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            mock_file.read = AsyncMock(return_value=content)
            mock_files.append(mock_file)
        
        # Mock coverage tracker
        with patch('services.scanner_service.coverage_tracker') as mock_tracker:
            mock_tracker.record_coverage.return_value = {"coverage_percent": 65.0}
            
            # Execute
            items_data, total_files, scan_time = await self.service.scan_uploaded_files(
                "test_project", mock_files
            )
        
        # Verify results
        assert isinstance(items_data, list)
        assert len(items_data) > 0
        assert total_files == len(sample_project_files)
        assert scan_time > 0
        
        # Verify coverage tracking was called
        mock_tracker.record_coverage.assert_called_once()
        
        # Verify some expected items are found
        item_names = [item.get('qualname', '') for item in items_data]
        assert any('root' in name for name in item_names)
        assert any('get_user' in name for name in item_names)
    
    @pytest.mark.asyncio
    async def test_scan_uploaded_files_no_python_files(self):
        """Test scanning with no Python files should raise exception."""
        # Create mock non-Python files
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "readme.txt"
        
        with pytest.raises(HTTPException) as exc_info:
            await self.service.scan_uploaded_files("test_project", [mock_file])
        
        assert exc_info.value.status_code == 400
        assert "No Python files found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_scan_uploaded_files_empty_list(self):
        """Test scanning with empty file list."""
        with pytest.raises(HTTPException) as exc_info:
            await self.service.scan_uploaded_files("test_project", [])
        
        assert exc_info.value.status_code == 400
        assert "No Python files found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_scan_local_project_success(self, sample_project_files, temp_dir):
        """Test successful scanning of local project."""
        with patch('services.scanner_service.coverage_tracker') as mock_tracker:
            mock_tracker.record_coverage.return_value = {"coverage_percent": 65.0}
            
            # Execute
            items_data, total_files, scan_time = await self.service.scan_local_project(temp_dir)
        
        # Verify results
        assert isinstance(items_data, list)
        assert len(items_data) > 0
        assert total_files == len(sample_project_files)
        assert scan_time > 0
        
        # Verify coverage tracking was called
        mock_tracker.record_coverage.assert_called_once()
        call_args = mock_tracker.record_coverage.call_args
        assert call_args[0][1] == temp_dir  # project_path
        assert call_args[1]['metadata']['scan_type'] == 'local_project'
    
    @pytest.mark.asyncio
    async def test_scan_local_project_nonexistent_path(self):
        """Test scanning nonexistent path should raise exception."""
        with pytest.raises(HTTPException) as exc_info:
            await self.service.scan_local_project("/nonexistent/path")
        
        assert exc_info.value.status_code == 400
        assert "Path does not exist" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_scan_local_project_no_python_files(self, temp_dir):
        """Test scanning directory with no Python files."""
        # Create a non-Python file
        (Path(temp_dir) / "readme.txt").write_text("This is not Python")
        
        with pytest.raises(HTTPException) as exc_info:
            await self.service.scan_local_project(temp_dir)
        
        assert exc_info.value.status_code == 400
        assert "No Python files found" in str(exc_info.value.detail)
    
    def test_get_project_files_success(self, sample_project_files, temp_dir):
        """Test getting project files list."""
        self.service.current_project_path = temp_dir
        
        files = self.service.get_project_files()
        
        assert isinstance(files, list)
        assert len(files) == len(sample_project_files)
        
        # Verify file structure
        for file_info in files:
            assert 'name' in file_info
            assert 'path' in file_info
            assert 'full_path' in file_info
            assert file_info['name'].endswith('.py')
    
    def test_get_project_files_no_project_loaded(self):
        """Test getting files when no project is loaded."""
        self.service.current_project_path = None
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.get_project_files()
        
        assert exc_info.value.status_code == 404
        assert "No project loaded" in str(exc_info.value.detail)
    
    def test_get_project_files_nonexistent_path(self):
        """Test getting files from nonexistent path."""
        self.service.current_project_path = "/nonexistent/path"
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.get_project_files()
        
        assert exc_info.value.status_code == 404
        assert "No project loaded" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_save_uploaded_files_preserves_structure(self, temp_dir):
        """Test that uploaded files preserve directory structure."""
        # Create mock file with subdirectory structure
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "subdir/module.py"
        mock_file.read = AsyncMock(return_value=b"# Python content")
        
        # Call the private method directly
        file_paths = await self.service._save_uploaded_files([mock_file], temp_dir)
        
        assert len(file_paths) == 1
        saved_path = file_paths[0]
        assert saved_path.endswith("subdir/module.py")
        assert os.path.exists(saved_path)
        
        # Verify directory was created
        expected_dir = os.path.join(temp_dir, "subdir")
        assert os.path.exists(expected_dir)
        assert os.path.isdir(expected_dir)
    
    @pytest.mark.asyncio
    async def test_save_uploaded_files_skips_non_python(self, temp_dir):
        """Test that non-Python files are skipped."""
        mock_files = [
            Mock(spec=UploadFile, filename="script.py"),
            Mock(spec=UploadFile, filename="readme.txt"),
            Mock(spec=UploadFile, filename="config.json")
        ]
        
        for mock_file in mock_files:
            mock_file.read = AsyncMock(return_value=b"content")
        
        file_paths = await self.service._save_uploaded_files(mock_files, temp_dir)
        
        # Only Python file should be saved
        assert len(file_paths) == 1
        assert file_paths[0].endswith("script.py")
    
    @patch('services.scanner_service.settings')
    def test_save_report_creates_file(self, mock_settings, temp_dir, sample_documentation_items):
        """Test that save report creates the expected file."""
        report_file = os.path.join(temp_dir, "test_report.json")
        mock_settings.report_file_path = report_file
        
        self.service._save_report(sample_documentation_items)
        
        # Verify file was created
        assert os.path.exists(report_file)
        
        # Verify content
        with open(report_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == sample_documentation_items
    
    @pytest.mark.asyncio
    async def test_scan_handles_file_errors_gracefully(self, temp_dir):
        """Test that scanning continues even if individual files have errors."""
        # Create files - one valid, one with syntax error
        valid_file = Path(temp_dir) / "valid.py"
        valid_file.write_text("def hello(): pass")
        
        invalid_file = Path(temp_dir) / "invalid.py"
        invalid_file.write_text("def broken(: pass")  # Syntax error
        
        with patch('services.scanner_service.coverage_tracker') as mock_tracker:
            mock_tracker.record_coverage.return_value = {"coverage_percent": 50.0}
            
            # Should not raise exception despite invalid file
            items_data, total_files, scan_time = await self.service.scan_local_project(temp_dir)
        
        # Should still process the valid file
        assert total_files == 2
        assert isinstance(items_data, list)
    
    @pytest.mark.asyncio
    async def test_metadata_recording(self, sample_project_files, temp_dir):
        """Test that metadata is properly recorded in coverage tracking."""
        with patch('services.scanner_service.coverage_tracker') as mock_tracker:
            # Execute local scan
            await self.service.scan_local_project(temp_dir)
            
            # Verify metadata structure
            call_args = mock_tracker.record_coverage.call_args
            metadata = call_args[1]['metadata']
            
            assert metadata['scan_type'] == 'local_project'
            assert metadata['total_files'] == len(sample_project_files)
            assert 'scan_time' in metadata
            assert isinstance(metadata['scan_time'], (int, float))
    
    def test_global_scanner_service_instance(self):
        """Test that the global scanner service instance is properly configured."""
        assert scanner_service is not None
        assert isinstance(scanner_service, ScannerService)
        assert scanner_service.current_project_path is None


@pytest.mark.unit  
class TestScannerServiceIntegrationWithCoreScanner:
    """Test integration between scanner service and core scanner module."""
    
    def test_scan_file_integration(self, sample_project_files):
        """Test that service properly integrates with core scan_file function."""
        # Use the actual scan_file function on our test files
        for file_path in sample_project_files:
            items = scan_file(file_path)
            
            # Verify items have expected structure
            for item in items:
                assert hasattr(item, 'module')
                assert hasattr(item, 'qualname') 
                assert hasattr(item, 'lineno')
                # Convert to dict as service does
                item_dict = item.__dict__
                assert isinstance(item_dict, dict)
    
    @pytest.mark.asyncio
    async def test_end_to_end_uploaded_files_workflow(self, sample_project_files):
        """Test complete workflow from file upload to report generation."""
        service = ScannerService()
        
        # Create realistic mock uploaded files
        mock_files = []
        for file_path in sample_project_files:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                content = f.read()
            mock_file.read = AsyncMock(return_value=content)
            mock_files.append(mock_file)
        
        with patch('services.scanner_service.coverage_tracker') as mock_tracker, \
             patch('services.scanner_service.settings') as mock_settings:
            
            mock_settings.report_file_path = "/tmp/test_report.json"
            mock_tracker.record_coverage.return_value = {"coverage_percent": 70.0}
            
            # Execute full workflow
            items_data, total_files, scan_time = await service.scan_uploaded_files(
                "integration_test", mock_files
            )
            
            # Verify comprehensive results
            assert len(items_data) > 0
            assert total_files == len(sample_project_files)
            assert scan_time > 0
            
            # Verify items contain expected FastAPI elements
            methods = [item.get('method') for item in items_data]
            assert 'GET' in methods
            
            qualnames = [item.get('qualname') for item in items_data]
            assert any('root' in name for name in qualnames)
            assert any('get_user' in name for name in qualnames)