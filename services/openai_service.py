"""
OpenAI configuration and settings service.
"""

import os
import json
from typing import Dict, Any, Optional
from core.config import settings


class OpenAIService:
    """Service for managing OpenAI API configuration."""
    
    def __init__(self):
        self.settings_file_path = os.path.join(os.path.dirname(settings.report_file_path), "openai_settings.json")
        self._ensure_settings_file_exists()
    
    def _ensure_settings_file_exists(self):
        """Ensure the OpenAI settings file exists."""
        if not os.path.exists(self.settings_file_path):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.settings_file_path), exist_ok=True)
            
            # Initialize with default settings
            default_settings = {
                "api_key": "",
                "model": "gpt-4.1-nano",
                "max_tokens": 400,
                "temperature": 0.1,
                "last_updated": None
            }
            
            with open(self.settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=2)
    
    def save_settings(
        self, 
        api_key: str, 
        model: str = "gpt-4.1-nano", 
        max_tokens: int = 400,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Save OpenAI API settings.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for requests
            max_tokens: Maximum tokens for completions
            temperature: Temperature setting for API calls
            
        Returns:
            Dictionary with success status and message
        """
        try:
            # Validate inputs
            if not api_key or (not api_key.startswith("sk-") and api_key != settings.OPENAI_API_KEY):
                return {
                    "success": False,
                    "message": "Invalid API key. OpenAI API keys should start with 'sk-'"
                }
            
            if max_tokens < 50 or max_tokens > 1000:
                return {
                    "success": False,
                    "message": "Max tokens must be between 50 and 1000"
                }
            
            if temperature < 0 or temperature > 2:
                return {
                    "success": False,
                    "message": "Temperature must be between 0 and 2"
                }
            
            # Load existing settings
            with open(self.settings_file_path, 'r', encoding='utf-8') as f:
                current_settings = json.load(f)
            
            # Update settings
            current_settings.update({
                "api_key": api_key,
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "last_updated": self._get_current_timestamp()
            })
            
            # Save updated settings
            with open(self.settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=2)
            
            # Update the global settings object
            settings.OPENAI_API_KEY = api_key
            
            return {
                "success": True,
                "message": "OpenAI settings saved successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error saving OpenAI settings: {str(e)}"
            }
    
    def get_settings(self) -> Optional[Dict[str, Any]]:
        """
        Load OpenAI settings from saved file or environment variables.
        
        Returns:
            Dictionary with OpenAI settings or None if not found
        """
        try:
            # First check if there's a saved settings file
            saved_settings = None
            if os.path.exists(self.settings_file_path):
                with open(self.settings_file_path, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
            
            # Check environment variable first (priority)
            env_api_key = settings.OPENAI_API_KEY
            
            # Determine which API key to use
            api_key = None
            if env_api_key and env_api_key.startswith("sk-") and len(env_api_key) > 10:
                api_key = env_api_key
            elif saved_settings and saved_settings.get("api_key") and saved_settings["api_key"].startswith("sk-"):
                api_key = saved_settings["api_key"]
            
            if api_key:
                return {
                    "api_key": api_key,
                    "model": saved_settings.get("model", "gpt-4.1-nano") if saved_settings else "gpt-4.1-nano",
                    "max_tokens": saved_settings.get("max_tokens", 400) if saved_settings else 400,
                    "temperature": saved_settings.get("temperature", 0.1) if saved_settings else 0.1,
                    "last_updated": saved_settings.get("last_updated", "") if saved_settings else "",
                    "source": "env" if api_key == env_api_key else "saved"
                }
            
            return None
            
        except Exception as e:
            print(f"Error loading OpenAI settings: {e}")
            return None
    
    def has_valid_settings(self) -> bool:
        """Check if valid OpenAI settings exist."""
        settings_data = self.get_settings()
        return (
            settings_data is not None and 
            settings_data.get("api_key") and 
            settings_data["api_key"].startswith("sk-")
        )
    
    def test_api_connection(self) -> Dict[str, Any]:
        """
        Test the OpenAI API connection with current settings.
        
        Returns:
            Dictionary with test results
        """
        try:
            settings_data = self.get_settings()
            if not settings_data:
                return {
                    "success": False,
                    "message": "No OpenAI settings found"
                }
            
            # Try to import and use OpenAI
            try:
                import openai
            except ImportError:
                return {
                    "success": False,
                    "message": "OpenAI library not installed. Run: pip install openai"
                }
            
            # Make a simple test request
            client = openai.OpenAI(api_key=settings_data["api_key"])
            response = client.chat.completions.create(
                model=settings_data["model"],
                messages=[
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Say 'test successful' if you receive this message."}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            return {
                "success": True,
                "message": "OpenAI API connection successful",
                "model": response.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"OpenAI API test failed: {str(e)}"
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for tracking updates."""
        from datetime import datetime
        return datetime.now().isoformat()


# Global OpenAI service instance
openai_service = OpenAIService()