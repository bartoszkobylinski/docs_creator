"""
OpenAI cost tracking service for monitoring API usage and expenses.
"""

import os
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
from pathlib import Path

from core.config import settings
from core.openai_pricing import calculate_cost, format_cost


class CostTrackingService:
    """Service for tracking OpenAI API costs and usage."""
    
    def __init__(self):
        self.cost_file_path = os.path.join(os.path.dirname(settings.report_file_path), "openai_costs.json")
        self._ensure_cost_file_exists()
    
    def _ensure_cost_file_exists(self):
        """Ensure the cost tracking file exists."""
        if not os.path.exists(self.cost_file_path):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.cost_file_path), exist_ok=True)
            
            # Initialize with empty data
            initial_data = {
                "total_cost": 0.0,
                "total_requests": 0,
                "daily_costs": {},
                "monthly_costs": {},
                "requests": []
            }
            
            with open(self.cost_file_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2)
    
    def track_usage(
        self, 
        model: str, 
        prompt_tokens: int, 
        completion_tokens: int, 
        context: str = "docstring_generation"
    ) -> Dict[str, Any]:
        """
        Track a single API usage and calculate costs.
        
        Args:
            model: OpenAI model used
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            context: Context of the request (e.g., "docstring_generation")
            
        Returns:
            Dictionary with cost information
        """
        try:
            # Calculate cost
            cost = calculate_cost(model, prompt_tokens, completion_tokens)
            if cost is None:
                cost = 0.0
            
            # Load existing data
            with open(self.cost_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Current date and time
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            month_str = now.strftime("%Y-%m")
            timestamp = now.isoformat()
            
            # Update totals
            data["total_cost"] = data.get("total_cost", 0.0) + cost
            data["total_requests"] = data.get("total_requests", 0) + 1
            
            # Update daily costs
            if "daily_costs" not in data:
                data["daily_costs"] = {}
            data["daily_costs"][today_str] = data["daily_costs"].get(today_str, 0.0) + cost
            
            # Update monthly costs
            if "monthly_costs" not in data:
                data["monthly_costs"] = {}
            data["monthly_costs"][month_str] = data["monthly_costs"].get(month_str, 0.0) + cost
            
            # Add request record
            request_record = {
                "timestamp": timestamp,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost": cost,
                "context": context
            }
            
            if "requests" not in data:
                data["requests"] = []
            data["requests"].append(request_record)
            
            # Keep only last 1000 requests to prevent file from growing too large
            if len(data["requests"]) > 1000:
                data["requests"] = data["requests"][-1000:]
            
            # Save updated data
            with open(self.cost_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return {
                "success": True,
                "cost": cost,
                "formatted_cost": format_cost(cost),
                "total_cost": data["total_cost"],
                "total_requests": data["total_requests"],
                "tokens_used": prompt_tokens + completion_tokens
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cost": 0.0
            }
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """
        Get current cost statistics.
        
        Returns:
            Dictionary with cost statistics
        """
        try:
            if not os.path.exists(self.cost_file_path):
                return {
                    "today": "0.00",
                    "month": "0.00",
                    "total": "0.00",
                    "total_requests": 0,
                    "today_requests": 0,
                    "month_requests": 0
                }
            
            with open(self.cost_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            today_str = date.today().strftime("%Y-%m-%d")
            month_str = date.today().strftime("%Y-%m")
            
            # Get costs
            today_cost = data.get("daily_costs", {}).get(today_str, 0.0)
            month_cost = data.get("monthly_costs", {}).get(month_str, 0.0)
            total_cost = data.get("total_cost", 0.0)
            total_requests = data.get("total_requests", 0)
            
            # Count today's and this month's requests
            today_requests = 0
            month_requests = 0
            
            for request in data.get("requests", []):
                request_date = datetime.fromisoformat(request["timestamp"]).date()
                if request_date == date.today():
                    today_requests += 1
                if request_date.strftime("%Y-%m") == month_str:
                    month_requests += 1
            
            return {
                "today": format_cost(today_cost),
                "month": format_cost(month_cost),
                "total": format_cost(total_cost),
                "total_requests": total_requests,
                "today_requests": today_requests,
                "month_requests": month_requests
            }
            
        except Exception as e:
            print(f"Error getting cost stats: {e}")
            return {
                "today": "0.00",
                "month": "0.00",
                "total": "0.00",
                "total_requests": 0,
                "today_requests": 0,
                "month_requests": 0
            }
    
    def get_recent_requests(self, limit: int = 50) -> list:
        """
        Get recent API requests with cost information.
        
        Args:
            limit: Maximum number of requests to return
            
        Returns:
            List of recent request records
        """
        try:
            with open(self.cost_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            requests = data.get("requests", [])
            # Return most recent first
            return list(reversed(requests[-limit:]))
            
        except Exception as e:
            print(f"Error getting recent requests: {e}")
            return []
    
    def get_monthly_breakdown(self, year: int, month: int) -> Dict[str, Any]:
        """
        Get detailed breakdown for a specific month.
        
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            
        Returns:
            Dictionary with monthly breakdown
        """
        try:
            with open(self.cost_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            month_str = f"{year:04d}-{month:02d}"
            requests = data.get("requests", [])
            
            # Filter requests for the specific month
            month_requests = []
            total_cost = 0.0
            model_usage = {}
            daily_breakdown = {}
            
            for request in requests:
                request_date = datetime.fromisoformat(request["timestamp"])
                if request_date.strftime("%Y-%m") == month_str:
                    month_requests.append(request)
                    total_cost += request["cost"]
                    
                    # Track model usage
                    model = request["model"]
                    if model not in model_usage:
                        model_usage[model] = {"requests": 0, "cost": 0.0, "tokens": 0}
                    model_usage[model]["requests"] += 1
                    model_usage[model]["cost"] += request["cost"]
                    model_usage[model]["tokens"] += request["total_tokens"]
                    
                    # Track daily breakdown
                    day_str = request_date.strftime("%Y-%m-%d")
                    if day_str not in daily_breakdown:
                        daily_breakdown[day_str] = {"requests": 0, "cost": 0.0}
                    daily_breakdown[day_str]["requests"] += 1
                    daily_breakdown[day_str]["cost"] += request["cost"]
            
            return {
                "month": month_str,
                "total_requests": len(month_requests),
                "total_cost": format_cost(total_cost),
                "model_usage": model_usage,
                "daily_breakdown": daily_breakdown,
                "requests": month_requests
            }
            
        except Exception as e:
            print(f"Error getting monthly breakdown: {e}")
            return {
                "month": f"{year:04d}-{month:02d}",
                "total_requests": 0,
                "total_cost": "0.00",
                "model_usage": {},
                "daily_breakdown": {},
                "requests": []
            }


# Global cost tracking service instance
cost_tracking_service = CostTrackingService()