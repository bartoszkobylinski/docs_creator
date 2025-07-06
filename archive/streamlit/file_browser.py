"""
File browser component for Streamlit dashboard.
Provides folder navigation and file selection without emojis.
"""

import os
import streamlit as st
from pathlib import Path
from typing import List, Optional


class FileBrowser:
    """Clean file browser component for directory navigation."""
    
    def __init__(self, start_path: str = "."):
        self.current_path = Path(start_path).resolve()
        if 'browser_path' not in st.session_state:
            st.session_state.browser_path = str(self.current_path)
    
    def render(self) -> Optional[str]:
        """Render the file browser and return selected path."""
        
        # Current path display
        st.text(f"Current location: {st.session_state.browser_path}")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("Go Up", key="go_up"):
                parent = Path(st.session_state.browser_path).parent
                st.session_state.browser_path = str(parent)
                st.rerun()
        
        with col2:
            if st.button("Home", key="go_home"):
                st.session_state.browser_path = str(Path.home())
                st.rerun()
        
        # Manual path input
        manual_path = st.text_input(
            "Or enter path manually:",
            value="",
            placeholder="/path/to/your/project"
        )
        
        if manual_path and os.path.exists(manual_path):
            st.session_state.browser_path = str(Path(manual_path).resolve())
            st.rerun()
        elif manual_path:
            st.error(f"Path does not exist: {manual_path}")
        
        # Directory contents
        try:
            current_path = Path(st.session_state.browser_path)
            
            # Get directories and files
            directories = []
            files = []
            
            for item in current_path.iterdir():
                if item.name.startswith('.'):
                    continue  # Skip hidden files
                
                if item.is_dir():
                    directories.append(item)
                elif item.suffix == '.py':
                    files.append(item)
            
            # Sort directories and files
            directories.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
            
            # Display directories
            if directories:
                st.subheader("Folders")
                for directory in directories:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.text(f"[DIR] {directory.name}")
                    with col2:
                        if st.button("Open", key=f"dir_{directory.name}"):
                            st.session_state.browser_path = str(directory)
                            st.rerun()
            
            # Display Python files (if any)
            if files:
                st.subheader(f"Python Files ({len(files)} found)")
                for file in files[:10]:  # Show first 10
                    st.text(f"[FILE] {file.name}")
                if len(files) > 10:
                    st.text(f"... and {len(files) - 10} more Python files")
            
            # Project selection
            st.markdown("---")
            
            # Check if current directory has Python files
            python_files_count = len([f for f in current_path.rglob("*.py") if not f.name.startswith('.')])
            
            if python_files_count > 0:
                st.success(f"Found {python_files_count} Python files in this directory")
                
                # Check for FastAPI indicators
                fastapi_found = self._check_fastapi_project(current_path)
                if fastapi_found:
                    st.info("FastAPI project detected")
                else:
                    st.warning("No FastAPI code detected, but scanning will still work")
                
                # Select this directory button
                if st.button("Select This Directory", type="primary"):
                    return str(current_path)
            else:
                st.warning("No Python files found in this directory")
        
        except PermissionError:
            st.error("Permission denied - cannot access this directory")
        except Exception as e:
            st.error(f"Error browsing directory: {e}")
        
        return None
    
    def _check_fastapi_project(self, path: Path) -> bool:
        """Check if the directory contains FastAPI code."""
        try:
            for py_file in path.rglob("*.py"):
                if py_file.stat().st_size > 100000:  # Skip very large files
                    continue
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(5000)  # Read first 5KB
                        if any(keyword in content for keyword in ['FastAPI', '@app.', '@router.', 'APIRouter']):
                            return True
                except:
                    continue
        except:
            pass
        return False


def render_quick_access():
    """Render quick access shortcuts."""
    st.subheader("Quick Access")
    
    # Common project locations
    common_paths = []
    
    # Add current directory
    common_paths.append(("Current Directory", "."))
    
    # Add parent directory
    common_paths.append(("Parent Directory", ".."))
    
    # Add common development folders
    home = Path.home()
    potential_paths = [
        ("Home", str(home)),
        ("Desktop", str(home / "Desktop")),
        ("Documents", str(home / "Documents")),
        ("Downloads", str(home / "Downloads")),
    ]
    
    # Check if these paths exist
    for name, path in potential_paths:
        if os.path.exists(path):
            common_paths.append((name, path))
    
    # Add development-specific paths
    dev_paths = [
        ("Projects", str(home / "Projects")),
        ("Development", str(home / "Development")),
        ("Code", str(home / "Code")),
        ("workspace", str(home / "workspace")),
    ]
    
    for name, path in dev_paths:
        if os.path.exists(path):
            common_paths.append((name, path))
    
    # Render quick access buttons
    for name, path in common_paths:
        if st.button(f"Go to {name}", key=f"quick_{name.replace(' ', '_')}"):
            st.session_state.browser_path = str(Path(path).resolve())
            st.rerun()