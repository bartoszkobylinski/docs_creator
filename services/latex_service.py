"""
LaTeX documentation generation service.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from fastdoc.models import DocItem


class LaTeXService:
    """Service for generating LaTeX documentation and PDFs."""
    
    def __init__(self):
        """Initialize LaTeX service with templates."""
        self.templates_dir = Path("templates/latex")
        self.output_dir = Path("reports/latex")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment for LaTeX templates
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            block_start_string='\\BLOCK{',
            block_end_string='}',
            variable_start_string='\\VAR{',
            variable_end_string='}',
            comment_start_string='\\#{',
            comment_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False,
        )
    
    def generate_complete_documentation(
        self, 
        doc_items: List[DocItem],
        project_name: str = "API Documentation",
        uml_diagrams: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete LaTeX documentation.
        
        Args:
            doc_items: List of documentation items
            project_name: Name of the project
            uml_diagrams: Optional UML diagram data
            
        Returns:
            Dict with paths to generated files
        """
        try:
            # Prepare template data
            template_data = self._prepare_template_data(doc_items, project_name, uml_diagrams)
            
            # Generate LaTeX source
            latex_source = self._generate_latex_source(template_data)
            
            # Save LaTeX source file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tex_filename = f"documentation_{timestamp}.tex"
            tex_path = self.output_dir / tex_filename
            
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(latex_source)
            
            # Try to compile PDF
            pdf_path = None
            try:
                pdf_path = self._compile_pdf(tex_path)
            except Exception as e:
                print(f"PDF compilation failed: {e}")
                # Still return LaTeX source even if PDF fails
            
            return {
                "success": True,
                "latex_file": str(tex_path),
                "pdf_file": str(pdf_path) if pdf_path else None,
                "timestamp": timestamp,
                "project_name": project_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_template_data(
        self, 
        doc_items: List[DocItem], 
        project_name: str,
        uml_diagrams: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare data for LaTeX templates."""
        
        # Organize items by type
        items_by_type = {}
        for item in doc_items:
            item_type = item.method or "UNKNOWN"
            if item_type not in items_by_type:
                items_by_type[item_type] = []
            items_by_type[item_type].append(item)
        
        # Calculate statistics
        total_items = len(doc_items)
        documented_items = len([item for item in doc_items if item.docstring and item.docstring.strip()])
        coverage_percent = (documented_items / total_items * 100) if total_items > 0 else 0
        
        # Get unique modules
        modules = list(set(item.module for item in doc_items if item.module))
        
        return {
            "project_name": project_name,
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_items": total_items,
            "documented_items": documented_items,
            "coverage_percent": coverage_percent,
            "modules": sorted(modules),
            "items_by_type": items_by_type,
            "uml_diagrams": uml_diagrams or {},
            "doc_items": doc_items
        }
    
    def _generate_latex_source(self, template_data: Dict[str, Any]) -> str:
        """Generate LaTeX source from template."""
        template = self.jinja_env.get_template("main.tex")
        return template.render(**template_data)
    
    def _compile_pdf(self, tex_path: Path) -> Optional[Path]:
        """
        Compile LaTeX to PDF using pdflatex.
        
        Args:
            tex_path: Path to .tex file
            
        Returns:
            Path to generated PDF or None if compilation fails
        """
        # Check if pdflatex is available
        try:
            subprocess.run(["pdflatex", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("pdflatex not found. Please install TeX Live or MiKTeX.")
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # Copy tex file to temp directory
            temp_tex_path = temp_dir_path / tex_path.name
            temp_tex_path.write_text(tex_path.read_text(encoding='utf-8'), encoding='utf-8')
            
            # Run pdflatex twice (for cross-references)
            for i in range(2):
                result = subprocess.run([
                    "pdflatex", 
                    "-interaction=nonstopmode",
                    "-output-directory", str(temp_dir_path),
                    str(temp_tex_path)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_msg = f"pdflatex failed (run {i+1}):\n{result.stdout}\n{result.stderr}"
                    raise Exception(error_msg)
            
            # Copy PDF back to output directory
            temp_pdf_path = temp_dir_path / tex_path.with_suffix('.pdf').name
            if temp_pdf_path.exists():
                final_pdf_path = self.output_dir / tex_path.with_suffix('.pdf').name
                final_pdf_path.write_bytes(temp_pdf_path.read_bytes())
                return final_pdf_path
            else:
                raise Exception("PDF file was not generated")
    
    def get_available_templates(self) -> List[str]:
        """Get list of available LaTeX templates."""
        if not self.templates_dir.exists():
            return []
        
        return [f.stem for f in self.templates_dir.glob("*.tex") 
                if f.name != "main.tex"]  # Exclude main template


# Global service instance
latex_service = LaTeXService()