"""
Core configuration settings for Flask Documentation Assistant.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings configuration."""
    
    # Application info
    APP_NAME: str = "Flask Documentation Assistant"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for scanning projects and managing docstrings"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8200"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:8200",
        "http://127.0.0.1:8200",
        "http://localhost:3000",  # For potential React frontend
    ]
    
    # File paths
    PROJECT_BASE_PATH: str = os.getenv("PROJECT_BASE_PATH", "./temp_projects")
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "./reports")
    BACKUPS_DIR: str = os.getenv("BACKUPS_DIR", "./backups")
    FRONTEND_DIR: str = os.getenv("FRONTEND_DIR", "./frontend")
    
    # Default report file
    DEFAULT_REPORT_FILE: str = "comprehensive_report.json"
    
    # OpenAI settings (optional)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Confluence settings (optional)
    CONFLUENCE_URL: Optional[str] = os.getenv("CONFLUENCE_URL")
    CONFLUENCE_USERNAME: Optional[str] = os.getenv("CONFLUENCE_USERNAME")
    CONFLUENCE_API_TOKEN: Optional[str] = os.getenv("CONFLUENCE_API_TOKEN")
    CONFLUENCE_SPACE_KEY: Optional[str] = os.getenv("CONFLUENCE_SPACE_KEY", "APIDEV")
    CONFLUENCE_PARENT_PAGE_ID: Optional[str] = os.getenv("CONFLUENCE_PARENT_PAGE_ID")
    
    # File scanning settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: list = [".py"]
    EXCLUDED_PATTERNS: list = [
        "**/migrations/**",
        "**/venv/**",
        "**/env/**",
        "**/__pycache__/**",
        "**/node_modules/**",
        "**/.git/**",
    ]
    
    def __init__(self):
        """Initialize settings and ensure directories exist."""
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.REPORTS_DIR,
            self.BACKUPS_DIR,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @property
    def report_file_path(self) -> str:
        """Get the full path to the default report file."""
        return os.path.join(self.REPORTS_DIR, self.DEFAULT_REPORT_FILE)

# Global settings instance
settings = Settings()