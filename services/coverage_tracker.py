"""
Coverage tracking service for monitoring documentation progress over time.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.config import settings


class CoverageTracker:
    """Service for tracking documentation coverage over time."""
    
    def __init__(self):
        """Initialize coverage tracker."""
        self.history_dir = Path(settings.REPORTS_DIR) / "coverage_history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / "coverage_history.json"
    
    def record_coverage(
        self, 
        items: List[Dict[str, Any]], 
        project_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record coverage statistics for a project scan.
        
        Args:
            items: List of documentation items from scanner
            project_path: Path to the scanned project
            metadata: Optional metadata about the scan
            
        Returns:
            Coverage record with statistics
        """
        # Calculate statistics
        total_items = len(items)
        documented_items = sum(1 for item in items if item.get('docstring'))
        coverage_percent = (documented_items / total_items * 100) if total_items > 0 else 0
        
        # Group by type
        by_type = {}
        for item in items:
            item_type = item.get('method', 'UNKNOWN')
            if item_type not in by_type:
                by_type[item_type] = {'total': 0, 'documented': 0}
            by_type[item_type]['total'] += 1
            if item.get('docstring'):
                by_type[item_type]['documented'] += 1
        
        # Calculate coverage by type
        for item_type in by_type:
            stats = by_type[item_type]
            stats['coverage'] = (stats['documented'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        # Group by module
        by_module = {}
        for item in items:
            module = item.get('module', 'unknown')
            if module not in by_module:
                by_module[module] = {'total': 0, 'documented': 0}
            by_module[module]['total'] += 1
            if item.get('docstring'):
                by_module[module]['documented'] += 1
        
        # Calculate coverage by module
        for module in by_module:
            stats = by_module[module]
            stats['coverage'] = (stats['documented'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        # Create coverage record
        record = {
            'timestamp': datetime.now().isoformat(),
            'project_path': project_path,
            'total_items': total_items,
            'documented_items': documented_items,
            'coverage_percent': round(coverage_percent, 2),
            'coverage_by_type': by_type,
            'coverage_by_module': by_module,
            'metadata': metadata or {}
        }
        
        # Load existing history
        history = self._load_history()
        
        # Add new record
        history.append(record)
        
        # Keep only last 100 records
        if len(history) > 100:
            history = history[-100:]
        
        # Save updated history
        self._save_history(history)
        
        return record
    
    def get_coverage_history(
        self, 
        project_path: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get coverage history records.
        
        Args:
            project_path: Filter by project path (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of coverage records, most recent first
        """
        history = self._load_history()
        
        # Filter by project path if specified
        if project_path:
            history = [record for record in history if record.get('project_path') == project_path]
        
        # Sort by timestamp (most recent first)
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply limit
        if limit:
            history = history[:limit]
        
        return history
    
    def get_coverage_trends(
        self, 
        project_path: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get coverage trends over the specified period.
        
        Args:
            project_path: Filter by project path (optional)
            days: Number of days to analyze
            
        Returns:
            Trends analysis
        """
        from datetime import timedelta
        
        history = self.get_coverage_history(project_path)
        
        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [
            record for record in history 
            if datetime.fromisoformat(record['timestamp']) >= cutoff_date
        ]
        
        if not recent_history:
            return {
                'period_days': days,
                'records_found': 0,
                'trend': 'no_data'
            }
        
        # Sort by timestamp (oldest first for trend calculation)
        recent_history.sort(key=lambda x: x.get('timestamp', ''))
        
        # Calculate trends
        first_record = recent_history[0]
        last_record = recent_history[-1]
        
        coverage_change = last_record['coverage_percent'] - first_record['coverage_percent']
        items_change = last_record['total_items'] - first_record['total_items']
        documented_change = last_record['documented_items'] - first_record['documented_items']
        
        # Determine trend direction
        if coverage_change > 1:
            trend = 'improving'
        elif coverage_change < -1:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'period_days': days,
            'records_found': len(recent_history),
            'trend': trend,
            'coverage_change': round(coverage_change, 2),
            'items_change': items_change,
            'documented_change': documented_change,
            'first_record': first_record,
            'last_record': last_record,
            'coverage_history': [
                {
                    'timestamp': record['timestamp'],
                    'coverage_percent': record['coverage_percent'],
                    'total_items': record['total_items']
                }
                for record in recent_history
            ]
        }
    
    def generate_progress_report(
        self, 
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive progress report.
        
        Args:
            project_path: Filter by project path (optional)
            
        Returns:
            Progress report with statistics and trends
        """
        # Get latest record
        history = self.get_coverage_history(project_path, limit=1)
        if not history:
            return {'error': 'No coverage data found'}
        
        latest = history[0]
        
        # Get trends for different periods
        trends_7d = self.get_coverage_trends(project_path, 7)
        trends_30d = self.get_coverage_trends(project_path, 30)
        
        # Find top and bottom modules by coverage
        modules = latest.get('coverage_by_module', {})
        if modules:
            sorted_modules = sorted(
                modules.items(), 
                key=lambda x: x[1]['coverage'], 
                reverse=True
            )
            best_modules = sorted_modules[:5]
            worst_modules = sorted_modules[-5:]
        else:
            best_modules = []
            worst_modules = []
        
        # Find missing documentation by type
        missing_by_type = {}
        for item_type, stats in latest.get('coverage_by_type', {}).items():
            missing_count = stats['total'] - stats['documented']
            if missing_count > 0:
                missing_by_type[item_type] = missing_count
        
        return {
            'generated_at': datetime.now().isoformat(),
            'project_path': project_path,
            'latest_scan': latest,
            'trends': {
                '7_days': trends_7d,
                '30_days': trends_30d
            },
            'top_modules': best_modules,
            'modules_needing_work': worst_modules,
            'missing_docs_by_type': missing_by_type,
            'recommendations': self._generate_recommendations(latest, trends_30d)
        }
    
    def _generate_recommendations(
        self, 
        latest: Dict[str, Any], 
        trends: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on coverage data."""
        recommendations = []
        
        coverage = latest['coverage_percent']
        trend = trends.get('trend', 'unknown')
        
        # Coverage level recommendations
        if coverage < 30:
            recommendations.append("🚨 Critical: Documentation coverage is very low. Consider making documentation a priority.")
        elif coverage < 60:
            recommendations.append("⚠️  Warning: Documentation coverage is below recommended levels. Focus on documenting public APIs first.")
        elif coverage < 80:
            recommendations.append("📈 Good progress! Focus on documenting remaining endpoints and complex functions.")
        else:
            recommendations.append("✅ Excellent documentation coverage! Focus on quality and keeping docs up-to-date.")
        
        # Trend recommendations
        if trend == 'declining':
            recommendations.append("📉 Documentation coverage is declining. Review recent changes and ensure new code is documented.")
        elif trend == 'improving':
            recommendations.append("🎉 Great job! Documentation coverage is improving over time.")
        
        # Type-specific recommendations
        by_type = latest.get('coverage_by_type', {})
        for item_type, stats in by_type.items():
            if stats['coverage'] < 50 and item_type in ['GET', 'POST', 'PUT', 'DELETE']:
                recommendations.append(f"🔗 Focus on documenting {item_type} endpoints - only {stats['coverage']:.1f}% are documented.")
        
        # Module-specific recommendations
        by_module = latest.get('coverage_by_module', {})
        worst_modules = sorted(by_module.items(), key=lambda x: x[1]['coverage'])[:3]
        for module, stats in worst_modules:
            if stats['coverage'] < 40:
                recommendations.append(f"📁 Module '{module}' needs attention - only {stats['coverage']:.1f}% documented.")
        
        return recommendations
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load coverage history from file."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """Save coverage history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except IOError as e:
            print(f"Failed to save coverage history: {e}")


# Global coverage tracker instance
coverage_tracker = CoverageTracker()