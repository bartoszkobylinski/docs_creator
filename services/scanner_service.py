"""
Scanner service for processing uploaded files and generating documentation reports.
"""

import os
import json
import tempfile
import time
from typing import List, Tuple, Dict, Any
from pathlib import Path

from werkzeug.datastructures import FileStorage

from fastdoc.scanner import scan_file
from core.config import settings
from services.coverage_tracker import coverage_tracker


class ScannerService:
    """Service for scanning uploaded Python files."""
    
    def __init__(self):
        self.current_project_path: str = None
    
    def scan_uploaded_files(
        self, 
        project_path: str, 
        files: List[FileStorage]
    ) -> Tuple[List[Dict[str, Any]], int, float]:
        """
        Scan uploaded files and return documentation items.
        
        Args:
            project_path: Name/path of the project
            files: List of uploaded files
            
        Returns:
            Tuple of (items_data, total_files, scan_time)
            
        Raises:
            Exception: If scanning fails or no Python files found
        """
        start_time = time.time()
        
        try:
            # Create temporary directory for uploaded files
            temp_dir = tempfile.mkdtemp()
            self.current_project_path = temp_dir
            
            print(f"Created temp directory: {temp_dir}")
            print(f"Received {len(files)} files")
            
            # Save uploaded files
            file_paths = self._save_uploaded_files(files, temp_dir)
            
            if not file_paths:
                raise Exception("No Python files found")
            
            # Scan all Python files
            all_items = []
            for file_path in file_paths:
                try:
                    items = scan_file(file_path)
                    all_items.extend(items)
                except Exception as e:
                    print(f"Error scanning {file_path}: {e}")
                    continue
            
            # Convert to dictionaries for JSON serialization
            items_data = [item.__dict__ for item in all_items]
            
            # Save report
            self._save_report(items_data)
            
            # Record coverage statistics
            coverage_tracker.record_coverage(
                items_data, 
                project_path,
                metadata={
                    'scan_type': 'uploaded_files',
                    'total_files': len(file_paths),
                    'scan_time': round(time.time() - start_time, 2)
                }
            )
            
            scan_time = time.time() - start_time
            
            return items_data, len(file_paths), round(scan_time, 2)
            
        except Exception as e:
            raise Exception(f"Scanning failed: {str(e)}")
    
    def _save_uploaded_files(
        self, 
        files: List[FileStorage], 
        temp_dir: str
    ) -> List[str]:
        """Save uploaded files to temporary directory."""
        file_paths = []
        
        for file in files:
            print(f"Processing file: {file.filename}")
            
            if not file.filename.endswith('.py'):
                print(f"Skipping non-Python file: {file.filename}")
                continue
            
            # Create subdirectories if needed (preserve structure)
            file_path = os.path.join(temp_dir, file.filename)
            file_dir = os.path.dirname(file_path)
            
            print(f"File path: {file_path}")
            print(f"File dir: {file_dir}")
            
            # Ensure directory exists
            if file_dir and file_dir != temp_dir:
                os.makedirs(file_dir, exist_ok=True)
                print(f"Created directory: {file_dir}")
            
            # Write file content
            with open(file_path, 'wb') as f:
                file.save(f)
            
            file_paths.append(file_path)
            print(f"Saved file: {file_path}")
        
        print(f"Total Python files saved: {len(file_paths)}")
        return file_paths
    
    def _save_report(self, items_data: List[Dict[str, Any]]) -> None:
        """Save scan results to report file."""
        with open(settings.report_file_path, 'w') as f:
            json.dump(items_data, f, indent=2)
    
    def scan_local_project(self, project_path: str) -> Tuple[List[Dict[str, Any]], int, float]:
        """
        Scan a local project directory using the CLI scanner.
        
        Args:
            project_path: Path to the local project directory
            
        Returns:
            Tuple of (items_data, total_files, scan_time)
            
        Raises:
            Exception: If scanning fails
        """
        start_time = time.time()
        
        try:
            self.current_project_path = project_path
            
            # Get all Python files in the project
            python_files = []
            for root, _, filenames in os.walk(project_path):
                for filename in filenames:
                    if filename.endswith('.py'):
                        python_files.append(os.path.join(root, filename))
            
            if not python_files:
                raise Exception(f"No Python files found in {project_path}")
            
            # Scan all Python files
            all_items = []
            for file_path in python_files:
                try:
                    items = scan_file(file_path)
                    all_items.extend(items)
                except Exception as e:
                    print(f"Error scanning {file_path}: {e}")
                    continue
            
            # Convert to dictionaries for JSON serialization
            items_data = [item.__dict__ for item in all_items]
            
            # Save report
            self._save_report(items_data)
            
            # Record coverage statistics
            coverage_tracker.record_coverage(
                items_data, 
                project_path,
                metadata={
                    'scan_type': 'local_project',
                    'total_files': len(python_files),
                    'scan_time': round(time.time() - start_time, 2)
                }
            )
            
            scan_time = time.time() - start_time
            
            return items_data, len(python_files), round(scan_time, 2)
            
        except Exception as e:
            raise Exception(f"Local scan failed: {str(e)}")
    
    def get_project_files(self) -> List[Dict[str, str]]:
        """Get list of Python files in the current project."""
        if not self.current_project_path or not os.path.exists(self.current_project_path):
            raise Exception("No project loaded")
        
        files = []
        for root, _, filenames in os.walk(self.current_project_path):
            for filename in filenames:
                if filename.endswith('.py'):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, self.current_project_path)
                    files.append({
                        "name": filename,
                        "path": rel_path,
                        "full_path": full_path
                    })
        
        return files


# Global scanner service instance
scanner_service = ScannerService()