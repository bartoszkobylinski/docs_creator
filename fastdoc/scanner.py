# fastdoc/scanner.py

import ast
import os
from fastdoc.models import DocItem

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}

class FastAPIScanner(ast.NodeVisitor):
    """
    Walks Python modules and gathers documentation items for FastAPI:
      - Module-level FastAPI() metadata (in visit_Assign)
      - Class docstrings (visit_ClassDef)
      - Both sync & async function docstrings (visit_FunctionDef / visit_AsyncFunctionDef)
      - FastAPI endpoint decorators (@*.get/post/…) extracting path, summary, description
    """

    def __init__(self, filename: str):
        self.filename = filename
        self.module = os.path.splitext(os.path.basename(filename))[0]
        self.items: list[DocItem] = []
        # Read file once for snippets
        with open(filename, "r") as f:
            self.source = f.read()

    def visit_Assign(self, node: ast.Assign):
        # Detect "app = FastAPI(...)" and record each keyword as METADATA
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "app"
            and isinstance(node.value, ast.Call)
            and (
                (isinstance(node.value.func, ast.Name) and node.value.func.id == "FastAPI")
                or (isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "FastAPI")
            )
        ):
            for kw in node.value.keywords:
                # Only record simple constant values here
                if isinstance(kw.value, ast.Constant):
                    self.items.append(DocItem(
                        module=self.module,
                        qualname="app",
                        path="",
                        method="METADATA",
                        signature=kw.arg,                   # e.g. "title", "description", "openapi_tags"
                        docstring=str(kw.value.value),     # the literal value
                        description=None,
                        first_lines="",
                        lineno=node.lineno
                    ))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Record class-level docstring
        class_doc = ast.get_docstring(node)
        self.items.append(DocItem(
            module=self.module,
            qualname=node.name,
            path="",
            method="CLASS",
            signature="",
            docstring=class_doc,
            description=None,
            first_lines="",
            lineno=node.lineno
        ))
        self.generic_visit(node)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        """Common logic for both sync & async functions."""
        func_doc = ast.get_docstring(node)
        sig = ast.unparse(node.args)

        # Source snippet: lines 2–6 of the function
        segment = ast.get_source_segment(self.source, node) or ""
        snippet = "\n".join(segment.splitlines()[1:6])

        # 1) Record every function/method
        self.items.append(DocItem(
            module=self.module,
            qualname=node.name,
            path="",
            method="FUNCTION",
            signature=sig,
            docstring=func_doc,
            description=None,
            first_lines=snippet,
            lineno=node.lineno
        ))

        # 2) Now detect FastAPI HTTP decorators
        for deco in node.decorator_list:
            if isinstance(deco, ast.Call) and hasattr(deco.func, "attr"):
                http = deco.func.attr.upper()
                if http in HTTP_METHODS:
                    # extract path (first Constant arg)
                    path = ""
                    for arg in deco.args:
                        if isinstance(arg, ast.Constant):
                            path = arg.value
                            break

                    # extract summary & description, preferring description
                    summary = None
                    desc = None
                    for kw in deco.keywords:
                        if kw.arg == "summary" and isinstance(kw.value, ast.Constant):
                            summary = kw.value.value
                        if kw.arg == "description" and isinstance(kw.value, ast.Constant):
                            desc = kw.value.value

                    self.items.append(DocItem(
                        module=self.module,
                        qualname=node.name,
                        path=path,
                        method=http,
                        signature=sig,
                        docstring=func_doc,
                        description=desc if desc is not None else summary,
                        first_lines=snippet,
                        lineno=node.lineno
                    ))

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_function(node)
        self.generic_visit(node)


def scan_file(path: str):
    """
    Parse `path`, walk its AST with FastAPIScanner, and return List[DocItem].
    """
    source = open(path, "r").read()
    tree = ast.parse(source)
    scanner = FastAPIScanner(path)
    scanner.visit(tree)
    return scanner.items
