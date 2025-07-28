"""
Unit tests for coverage tracker service.
Tests coverage statistics, historical tracking, and trend analysis.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
from freezegun import freeze_time

from services.coverage_tracker import CoverageTracker, coverage_tracker


@pytest.mark.unit
class TestCoverageTracker:
    """Test cases for CoverageTracker."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.tracker = CoverageTracker()
    
    def test_init_creates_directories(self, temp_dir):
        """Test that initialization creates necessary directories."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            assert tracker.history_dir.exists()
            assert tracker.history_dir.is_dir()
            assert tracker.history_file == tracker.history_dir / "coverage_history.json"
    
    def test_record_coverage_basic_stats(self, sample_documentation_items):
        """Test basic coverage statistics recording."""
        with freeze_time("2024-01-15 10:30:00"):
            record = self.tracker.record_coverage(
                sample_documentation_items,
                "/test/project",
                metadata={"scan_type": "test"}
            )
        
        # Verify basic statistics
        assert record["total_items"] == 4
        assert record["documented_items"] == 2  # root and create_user
        assert record["coverage_percent"] == 50.0
        assert record["project_path"] == "/test/project"
        assert record["timestamp"] == "2024-01-15T10:30:00"
        assert record["metadata"]["scan_type"] == "test"
    
    def test_record_coverage_by_type_breakdown(self, sample_documentation_items):
        """Test coverage breakdown by item type."""
        record = self.tracker.record_coverage(sample_documentation_items, "/test/project")
        
        by_type = record["coverage_by_type"]
        
        # Verify GET endpoints
        assert "GET" in by_type
        assert by_type["GET"]["total"] == 2
        assert by_type["GET"]["documented"] == 1  # only root has docstring
        assert by_type["GET"]["coverage"] == 50.0
        
        # Verify functions
        assert "function" in by_type
        assert by_type["function"]["total"] == 2
        assert by_type["function"]["documented"] == 1  # only create_user has docstring
        assert by_type["function"]["coverage"] == 50.0
    
    def test_record_coverage_by_module_breakdown(self, sample_documentation_items):
        """Test coverage breakdown by module."""
        record = self.tracker.record_coverage(sample_documentation_items, "/test/project")
        
        by_module = record["coverage_by_module"]
        
        # All items are in 'main' module
        assert "main" in by_module
        assert by_module["main"]["total"] == 4
        assert by_module["main"]["documented"] == 2
        assert by_module["main"]["coverage"] == 50.0
    
    def test_record_coverage_empty_items(self):
        """Test recording coverage with empty items list."""
        record = self.tracker.record_coverage([], "/empty/project")
        
        assert record["total_items"] == 0
        assert record["documented_items"] == 0
        assert record["coverage_percent"] == 0
        assert record["coverage_by_type"] == {}
        assert record["coverage_by_module"] == {}
    
    def test_record_coverage_all_documented(self):
        """Test recording coverage when all items are documented."""
        items = [
            {"qualname": "func1", "docstring": "Doc 1", "method": "GET", "module": "api"},
            {"qualname": "func2", "docstring": "Doc 2", "method": "POST", "module": "api"}
        ]
        
        record = self.tracker.record_coverage(items, "/full/project")
        
        assert record["coverage_percent"] == 100.0
        assert record["documented_items"] == 2
        assert record["coverage_by_type"]["GET"]["coverage"] == 100.0
        assert record["coverage_by_type"]["POST"]["coverage"] == 100.0
    
    def test_history_persistence(self, temp_dir, sample_documentation_items):
        """Test that coverage history is properly persisted."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Record first entry
            record1 = tracker.record_coverage(sample_documentation_items, "/test/project1")
            
            # Record second entry
            record2 = tracker.record_coverage(sample_documentation_items[:2], "/test/project2")
            
            # Verify history file exists and contains both records
            assert tracker.history_file.exists()
            
            with open(tracker.history_file, 'r') as f:
                history = json.load(f)
            
            assert len(history) == 2
            assert history[0] == record1
            assert history[1] == record2
    
    def test_history_limit_enforcement(self, temp_dir):
        """Test that history is limited to 100 records."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Create 102 records
            for i in range(102):
                items = [{"qualname": f"func_{i}", "docstring": "doc", "method": "GET", "module": "test"}]
                tracker.record_coverage(items, f"/project_{i}")
            
            # Load history and verify limit
            history = tracker._load_history()
            assert len(history) == 100
            
            # Verify it kept the latest records
            assert any("project_101" in record["project_path"] for record in history)
            assert not any("project_0" in record["project_path"] for record in history)
    
    def test_get_coverage_history_no_filter(self, temp_dir, sample_documentation_items):
        """Test getting coverage history without filters."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Add some records
            with freeze_time("2024-01-10"):
                tracker.record_coverage(sample_documentation_items, "/project1")
            with freeze_time("2024-01-15"):
                tracker.record_coverage(sample_documentation_items, "/project2")
            
            history = tracker.get_coverage_history()
            
            assert len(history) == 2
            # Should be sorted by timestamp, most recent first
            assert "2024-01-15" in history[0]["timestamp"]
            assert "2024-01-10" in history[1]["timestamp"]
    
    def test_get_coverage_history_with_project_filter(self, temp_dir, sample_documentation_items):
        """Test getting coverage history filtered by project path."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Add records for different projects
            tracker.record_coverage(sample_documentation_items, "/project1")
            tracker.record_coverage(sample_documentation_items, "/project2")
            tracker.record_coverage(sample_documentation_items, "/project1")
            
            # Filter by project1
            history = tracker.get_coverage_history(project_path="/project1")
            
            assert len(history) == 2
            assert all(record["project_path"] == "/project1" for record in history)
    
    def test_get_coverage_history_with_limit(self, temp_dir, sample_documentation_items):
        """Test getting coverage history with limit."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Add 5 records
            for i in range(5):
                tracker.record_coverage(sample_documentation_items, f"/project{i}")
            
            # Get only 3 most recent
            history = tracker.get_coverage_history(limit=3)
            
            assert len(history) == 3
    
    def test_get_coverage_trends_improving(self, temp_dir):
        """Test trend analysis for improving coverage."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Create trend: coverage improving over time
            base_time = datetime(2024, 1, 1)
            
            for i in range(5):
                timestamp = base_time + timedelta(days=i)
                documented_count = i + 1  # Increasing documentation
                items = [
                    {"qualname": f"func_{j}", "docstring": "doc" if j < documented_count else None, 
                     "method": "GET", "module": "test"}
                    for j in range(5)
                ]
                
                with freeze_time(timestamp):
                    tracker.record_coverage(items, "/improving/project")
            
            trends = tracker.get_coverage_trends("/improving/project", days=10)
            
            assert trends["trend"] == "improving"
            assert trends["coverage_change"] > 1
            assert trends["records_found"] == 5
    
    def test_get_coverage_trends_declining(self, temp_dir):
        """Test trend analysis for declining coverage."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Create trend: coverage declining over time
            base_time = datetime(2024, 1, 1)
            
            for i in range(5):
                timestamp = base_time + timedelta(days=i)
                documented_count = 5 - i  # Decreasing documentation
                items = [
                    {"qualname": f"func_{j}", "docstring": "doc" if j < documented_count else None,
                     "method": "GET", "module": "test"}
                    for j in range(5)
                ]
                
                with freeze_time(timestamp):
                    tracker.record_coverage(items, "/declining/project")
            
            trends = tracker.get_coverage_trends("/declining/project", days=10)
            
            assert trends["trend"] == "declining"
            assert trends["coverage_change"] < -1
    
    def test_get_coverage_trends_stable(self, temp_dir):
        """Test trend analysis for stable coverage."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Create stable trend
            base_time = datetime(2024, 1, 1)
            items = [
                {"qualname": "func_1", "docstring": "doc", "method": "GET", "module": "test"},
                {"qualname": "func_2", "docstring": None, "method": "GET", "module": "test"}
            ]
            
            for i in range(5):
                timestamp = base_time + timedelta(days=i)
                with freeze_time(timestamp):
                    tracker.record_coverage(items, "/stable/project")
            
            trends = tracker.get_coverage_trends("/stable/project", days=10)
            
            assert trends["trend"] == "stable"
            assert abs(trends["coverage_change"]) <= 1
    
    def test_get_coverage_trends_no_data(self, temp_dir):
        """Test trend analysis with no data."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            trends = tracker.get_coverage_trends("/nonexistent/project", days=30)
            
            assert trends["trend"] == "no_data"
            assert trends["records_found"] == 0
    
    def test_generate_progress_report_complete(self, temp_dir, sample_documentation_items):
        """Test comprehensive progress report generation."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Create history with trends
            base_time = datetime(2024, 1, 1)
            for i in range(10):
                timestamp = base_time + timedelta(days=i)
                with freeze_time(timestamp):
                    tracker.record_coverage(sample_documentation_items, "/test/project")
            
            with freeze_time("2024-01-15"):
                report = tracker.generate_progress_report("/test/project")
            
            # Verify report structure
            assert "generated_at" in report
            assert "project_path" in report
            assert "latest_scan" in report
            assert "trends" in report
            assert "7_days" in report["trends"]
            assert "30_days" in report["trends"]
            assert "top_modules" in report
            assert "modules_needing_work" in report
            assert "missing_docs_by_type" in report
            assert "recommendations" in report
            
            # Verify latest scan data
            assert report["latest_scan"]["total_items"] == 4
            assert report["latest_scan"]["coverage_percent"] == 50.0
    
    def test_generate_progress_report_no_data(self, temp_dir):
        """Test progress report generation with no data."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            report = tracker.generate_progress_report("/nonexistent/project")
            
            assert "error" in report
            assert "No coverage data found" in report["error"]
    
    def test_generate_recommendations_low_coverage(self):
        """Test recommendation generation for low coverage."""
        latest_record = {
            "coverage_percent": 25.0,
            "coverage_by_type": {
                "GET": {"coverage": 20.0, "total": 5, "documented": 1},
                "POST": {"coverage": 30.0, "total": 3, "documented": 1}
            },
            "coverage_by_module": {
                "api": {"coverage": 15.0, "total": 10, "documented": 1}
            }
        }
        
        trends = {"trend": "declining"}
        
        recommendations = self.tracker._generate_recommendations(latest_record, trends)
        
        # Should recommend focusing on documentation
        assert any("Critical" in rec for rec in recommendations)
        assert any("GET endpoints" in rec for rec in recommendations)
        assert any("declining" in rec for rec in recommendations)
        assert any("'api'" in rec for rec in recommendations)
    
    def test_generate_recommendations_high_coverage(self):
        """Test recommendation generation for high coverage."""
        latest_record = {
            "coverage_percent": 85.0,
            "coverage_by_type": {"GET": {"coverage": 90.0}},
            "coverage_by_module": {"api": {"coverage": 85.0}}
        }
        
        trends = {"trend": "improving"}
        
        recommendations = self.tracker._generate_recommendations(latest_record, trends)
        
        # Should recommend maintaining quality
        assert any("Excellent" in rec for rec in recommendations)
        assert any("improving" in rec for rec in recommendations)
    
    def test_load_history_nonexistent_file(self, temp_dir):
        """Test loading history when file doesn't exist."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # File doesn't exist yet
            history = tracker._load_history()
            
            assert history == []
    
    def test_load_history_corrupted_file(self, temp_dir):
        """Test loading history with corrupted JSON file."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Create corrupted JSON file
            with open(tracker.history_file, 'w') as f:
                f.write("invalid json content")
            
            # Should return empty list on error
            history = tracker._load_history()
            
            assert history == []
    
    def test_save_history_io_error(self, temp_dir):
        """Test handling of IO errors during history saving."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Mock file operations to raise IOError
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                # Should not raise exception
                tracker._save_history([{"test": "data"}])
    
    def test_global_coverage_tracker_instance(self):
        """Test that the global coverage tracker instance is properly configured."""
        assert coverage_tracker is not None
        assert isinstance(coverage_tracker, CoverageTracker)


@pytest.mark.unit
class TestCoverageTrackerEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.tracker = CoverageTracker()
    
    def test_record_coverage_with_missing_fields(self):
        """Test recording coverage with items missing optional fields."""
        items = [
            {"qualname": "test1"},  # Missing docstring, method, module
            {"qualname": "test2", "docstring": "doc"},  # Missing method, module
            {"qualname": "test3", "method": "GET"}  # Missing docstring, module
        ]
        
        record = self.tracker.record_coverage(items, "/test/project")
        
        # Should handle missing fields gracefully
        assert record["total_items"] == 3
        assert record["documented_items"] == 1  # Only test2 has docstring
        
        # Should use default values for missing fields
        assert "UNKNOWN" in record["coverage_by_type"]
        assert "unknown" in record["coverage_by_module"]
    
    def test_coverage_calculation_edge_cases(self):
        """Test coverage calculation edge cases."""
        # Test with empty docstring (should count as undocumented)
        items = [
            {"qualname": "test1", "docstring": "", "method": "GET", "module": "api"},
            {"qualname": "test2", "docstring": "   ", "method": "POST", "module": "api"},
            {"qualname": "test3", "docstring": None, "method": "PUT", "module": "api"}
        ]
        
        record = self.tracker.record_coverage(items, "/test/project")
        
        # All should be considered undocumented
        assert record["documented_items"] == 0
        assert record["coverage_percent"] == 0.0
    
    def test_trend_calculation_single_record(self, temp_dir):
        """Test trend calculation with only one record."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            items = [{"qualname": "test", "docstring": "doc", "method": "GET", "module": "api"}]
            tracker.record_coverage(items, "/single/project")
            
            trends = tracker.get_coverage_trends("/single/project", days=30)
            
            # With only one record, change should be 0
            assert trends["coverage_change"] == 0.0
            assert trends["trend"] == "stable"
    
    def test_large_time_range_filtering(self, temp_dir):
        """Test filtering with very large time ranges."""
        with patch('services.coverage_tracker.settings') as mock_settings:
            mock_settings.REPORTS_DIR = temp_dir
            
            tracker = CoverageTracker()
            
            # Add a record from long ago
            old_time = datetime.now() - timedelta(days=500)
            with freeze_time(old_time):
                items = [{"qualname": "old", "docstring": "doc", "method": "GET", "module": "api"}]
                tracker.record_coverage(items, "/old/project")
            
            # Request trends for only last 30 days
            trends = tracker.get_coverage_trends("/old/project", days=30)
            
            # Should find no records in recent period
            assert trends["records_found"] == 0
            assert trends["trend"] == "no_data"