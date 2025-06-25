# fastdoc/cli.py

import json
import os
import typer
from fastdoc.scanner import scan_file

app = typer.Typer()

@app.command()
def scan(
    project_path: str = typer.Argument(
        ..., help="Root of your FastAPI project or a single .py file"
    ),
    out: str = typer.Option("fastapi_report.json", help="Output JSON path"),
):
    all_items = []

    if os.path.isfile(project_path):
        # single-file mode
        all_items = scan_file(project_path)
    else:
        # directory mode
        for root, _, files in os.walk(project_path):
            for fn in files:
                if fn.endswith(".py"):
                    all_items.extend(scan_file(os.path.join(root, fn)))

    with open(out, "w") as f:
        json.dump([item.__dict__ for item in all_items], f, indent=2)

    typer.echo(f"Scanned {len(all_items)} endpoints — report saved to {out}")

if __name__ == "__main__":
    app()
