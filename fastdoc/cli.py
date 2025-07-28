# fastdoc/cli.py

import json
import os
import sys
import typer
from typing import Optional

# Add the parent directory to the path to import scanner
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastdoc.scanner import scan_file
from services.confluence_service import confluence_service

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


@app.command()
def publish_coverage(
    report_file: str = typer.Argument(..., help="Path to JSON report file"),
    title_suffix: Optional[str] = typer.Option(None, help="Optional suffix for page title"),
    to_confluence: bool = typer.Option(False, "--to-confluence", help="Publish to Confluence")
):
    """Publish coverage report to Confluence."""
    if not to_confluence:
        typer.echo("Use --to-confluence flag to publish to Confluence")
        return
    
    if not confluence_service.is_enabled():
        typer.echo("Error: Confluence integration is not configured", err=True)
        typer.echo("Please set CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, and CONFLUENCE_SPACE_KEY environment variables")
        return
    
    # Load report data
    try:
        with open(report_file, 'r') as f:
            items = json.load(f)
    except FileNotFoundError:
        typer.echo(f"Error: Report file not found: {report_file}", err=True)
        return
    except json.JSONDecodeError:
        typer.echo(f"Error: Invalid JSON in report file: {report_file}", err=True)
        return
    
    # Publish to Confluence
    try:
        result = confluence_service.publish_coverage_report(items, title_suffix)
        page_id = result.get('id')
        typer.echo(f"✅ Coverage report published to Confluence!")
        typer.echo(f"Page ID: {page_id}")
        typer.echo(f"URL: {confluence_service.confluence.url}/wiki/spaces/{confluence_service.space_key}/pages/{page_id}")
    except Exception as e:
        typer.echo(f"Error publishing to Confluence: {e}", err=True)


@app.command()
def publish_endpoints(
    report_file: str = typer.Argument(..., help="Path to JSON report file"),
    to_confluence: bool = typer.Option(False, "--to-confluence", help="Publish to Confluence"),
    endpoint_filter: Optional[str] = typer.Option(None, help="Filter endpoints by path (contains)")
):
    """Publish endpoint documentation to Confluence."""
    if not to_confluence:
        typer.echo("Use --to-confluence flag to publish to Confluence")
        return
    
    if not confluence_service.is_enabled():
        typer.echo("Error: Confluence integration is not configured", err=True)
        typer.echo("Please set CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, and CONFLUENCE_SPACE_KEY environment variables")
        return
    
    # Load report data
    try:
        with open(report_file, 'r') as f:
            items = json.load(f)
    except FileNotFoundError:
        typer.echo(f"Error: Report file not found: {report_file}", err=True)
        return
    except json.JSONDecodeError:
        typer.echo(f"Error: Invalid JSON in report file: {report_file}", err=True)
        return
    
    # Filter for endpoints only
    endpoints = [item for item in items if item.get('method') in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']]
    
    if endpoint_filter:
        endpoints = [ep for ep in endpoints if endpoint_filter in ep.get('path', '')]
    
    if not endpoints:
        typer.echo("No endpoints found to publish")
        return
    
    typer.echo(f"Found {len(endpoints)} endpoints to publish")
    
    # Publish each endpoint
    published_count = 0
    failed_count = 0
    
    for endpoint in endpoints:
        try:
            result = confluence_service.publish_endpoint_doc(endpoint)
            published_count += 1
            typer.echo(f"✅ Published: {endpoint.get('method')} {endpoint.get('path')}")
        except Exception as e:
            failed_count += 1
            typer.echo(f"❌ Failed: {endpoint.get('method')} {endpoint.get('path')} - {e}")
    
    typer.echo(f"\n📊 Summary: {published_count} published, {failed_count} failed")


@app.command()
def confluence_status():
    """Check Confluence integration status."""
    if confluence_service.is_enabled():
        typer.echo("✅ Confluence integration is enabled")
        typer.echo(f"URL: {confluence_service.confluence.url}")
        typer.echo(f"Space: {confluence_service.space_key}")
    else:
        typer.echo("❌ Confluence integration is not configured")
        typer.echo("\nTo enable Confluence integration, set these environment variables:")
        typer.echo("  CONFLUENCE_URL=https://yourcompany.atlassian.net")
        typer.echo("  CONFLUENCE_USERNAME=your.email@company.com")
        typer.echo("  CONFLUENCE_API_TOKEN=your-api-token")
        typer.echo("  CONFLUENCE_SPACE_KEY=APIDEV")


if __name__ == "__main__":
    app()
