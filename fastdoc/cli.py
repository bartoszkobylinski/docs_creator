# fastdoc/cli.py

import json
import os
import sys
import typer

# Add the parent directory to the path to import scanner
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastdoc.scanner import scan_file

app = typer.Typer()

@app.command()
def scan(
    project_path: str = typer.Argument(
        ..., help="Root of your FastAPI project or a single .py file"
    ),
    out: str = typer.Option("comprehensive_report.json", help="Output JSON path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    all_items = []
    processed_files = 0

    if os.path.isfile(project_path):
        # single-file mode
        if verbose:
            typer.echo(f"Scanning single file: {project_path}")
        all_items = scan_file(project_path)
        processed_files = 1
    else:
        # directory mode
        if verbose:
            typer.echo(f"Scanning directory: {project_path}")
        
        for root, _, files in os.walk(project_path):
            for fn in files:
                if fn.endswith(".py"):
                    file_path = os.path.join(root, fn)
                    if verbose:
                        typer.echo(f"Processing: {file_path}")
                    
                    try:
                        items = scan_file(file_path)
                        all_items.extend(items)
                        processed_files += 1
                    except Exception as e:
                        if verbose:
                            typer.echo(f"Error processing {file_path}: {e}")

    if verbose:
        typer.echo(f"Processed {processed_files} Python files")
        typer.echo(f"Found {len(all_items)} documentation items")

    with open(out, "w") as f:
        json.dump([item.__dict__ for item in all_items], f, indent=2)

    # Calculate some stats
    documented_items = sum(1 for item in all_items if hasattr(item, 'docstring') and item.docstring and item.docstring.strip())
    coverage_percent = (documented_items / len(all_items) * 100) if all_items else 0

    typer.echo(f"Scan complete!")
    typer.echo(f"Files processed: {processed_files}")
    typer.echo(f"Items found: {len(all_items)}")
    typer.echo(f"Documented: {documented_items} ({coverage_percent:.1f}%)")
    typer.echo(f"Report saved to: {out}")

if __name__ == "__main__":
    app()
