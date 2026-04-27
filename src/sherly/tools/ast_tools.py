"""
AST PATCHER — ast_tools.py
Upgrades:
  FS-#26  Full AST-aware code patching beyond function body replacement.
           New capabilities:
             - patch_function()    — replace function body (existing)
             - patch_class()       — replace a class method body
             - add_import()        — inject a missing import at the top
             - rename_symbol()     — rename a function or class throughout the file
             - extract_function()  — extract a block of statements into a named function
             - get_function_names()— list all top-level function/method names
             - get_imports()       — list all current imports
           All operations unparse back to source code, eliminating
           whitespace-sensitive diff errors.
"""

from __future__ import annotations

import ast
import textwrap
from typing import Optional

from sherly.utils.runtime_utils import log


class ASTPatcher:
    """
    AST-aware source code transformation engine.

    FS-#26: Every operation parses the file into an AST, applies
    transformations at the node level, and unparses back to clean Python source.
    No string/regex manipulation — eliminates whitespace-sensitive diff errors.
    """

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_function_names(self, source_code: str) -> list[str]:
        """Return all top-level function and async-function names in the source."""
        try:
            tree = ast.parse(source_code)
            return [
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and isinstance(node.col_offset, int)
                and node.col_offset == 0
            ]
        except SyntaxError as exc:
            log(f"[AST] Syntax error parsing source: {exc}", level="error")
            return []

    def get_imports(self, source_code: str) -> list[str]:
        """Return all import statements as source strings."""
        try:
            tree = ast.parse(source_code)
            return [
                ast.unparse(node)
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
            ]
        except SyntaxError:
            return []

    # ------------------------------------------------------------------
    # Patch / Replace operations
    # ------------------------------------------------------------------

    def patch_function(self, source_code: str, target_func: str, new_body: str) -> str:
        """
        Replace the body of a named function (top-level or method).
        new_body is a Python source string for the function's statements.
        """
        try:
            tree          = ast.parse(source_code)
            new_body_ast  = ast.parse(textwrap.dedent(new_body)).body

            class _FunctionBodyReplacer(ast.NodeTransformer):
                def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
                    if node.name == target_func:
                        log(f"[AST] Patching function body: {target_func}")
                        node.body = new_body_ast
                    return node

                def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
                    if node.name == target_func:
                        log(f"[AST] Patching async function body: {target_func}")
                        node.body = new_body_ast
                    return node

            modified = _FunctionBodyReplacer().visit(tree)
            ast.fix_missing_locations(modified)
            return ast.unparse(modified)
        except Exception as exc:
            log(f"[AST] patch_function failed: {exc}", level="error")
            return source_code

    # Backward-compatible alias
    transform_function = patch_function

    def patch_class_method(
        self,
        source_code: str,
        class_name: str,
        method_name: str,
        new_body: str,
    ) -> str:
        """
        FS-#26: Replace the body of a specific method inside a named class.
        """
        try:
            tree         = ast.parse(source_code)
            new_body_ast = ast.parse(textwrap.dedent(new_body)).body

            class _ClassMethodReplacer(ast.NodeTransformer):
                def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
                    if node.name == class_name:
                        for item in node.body:
                            if (
                                isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                                and item.name == method_name
                            ):
                                log(f"[AST] Patching {class_name}.{method_name}")
                                item.body = new_body_ast
                    return node

            modified = _ClassMethodReplacer().visit(tree)
            ast.fix_missing_locations(modified)
            return ast.unparse(modified)
        except Exception as exc:
            log(f"[AST] patch_class_method failed: {exc}", level="error")
            return source_code

    def add_import(self, source_code: str, import_statement: str) -> str:
        """
        FS-#26: Inject a new import at the top of the file (after any existing
        imports) if it is not already present.
        """
        if import_statement.strip() in source_code:
            return source_code  # Already imported

        try:
            tree          = ast.parse(source_code)
            new_import    = ast.parse(import_statement.strip()).body[0]

            # Find the index after the last existing import statement
            last_import_idx = 0
            for i, node in enumerate(tree.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last_import_idx = i + 1

            tree.body.insert(last_import_idx, new_import)
            ast.fix_missing_locations(tree)
            log(f"[AST] Injected import: {import_statement.strip()}")
            return ast.unparse(tree)
        except Exception as exc:
            log(f"[AST] add_import failed: {exc}", level="error")
            return source_code

    def rename_symbol(self, source_code: str, old_name: str, new_name: str) -> str:
        """
        FS-#26: Rename every occurrence of a function or class name throughout
        the file (definitions + call sites).
        """
        try:
            tree = ast.parse(source_code)

            class _Renamer(ast.NodeTransformer):
                def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
                    if node.name == old_name:
                        node.name = new_name
                    return self.generic_visit(node)

                def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
                    if node.name == old_name:
                        node.name = new_name
                    return self.generic_visit(node)

                def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
                    if node.name == old_name:
                        node.name = new_name
                    return self.generic_visit(node)

                def visit_Name(self, node: ast.Name) -> ast.Name:
                    if node.id == old_name:
                        node.id = new_name
                    return node

            modified = _Renamer().visit(tree)
            ast.fix_missing_locations(modified)
            log(f"[AST] Renamed '{old_name}' → '{new_name}'")
            return ast.unparse(modified)
        except Exception as exc:
            log(f"[AST] rename_symbol failed: {exc}", level="error")
            return source_code

    def extract_function(
        self,
        source_code: str,
        start_line: int,
        end_line: int,
        new_func_name: str,
        parent_func: Optional[str] = None,
    ) -> str:
        """
        FS-#26: Extract lines [start_line, end_line] from parent_func (or
        module level) into a new named function, and replace the original
        block with a call to the new function.

        Lines are 1-indexed (matching editor conventions).
        """
        try:
            lines = source_code.splitlines()
            extracted = lines[start_line - 1 : end_line]
            dedented  = textwrap.dedent("\n".join(extracted))

            # Build the new function source
            new_func_src = f"def {new_func_name}():\n" + textwrap.indent(dedented, "    ")

            # Replace the original block with a call
            call_line = f"    {new_func_name}()  # extracted by ASTPatcher"
            new_lines = (
                lines[: start_line - 1]
                + [call_line]
                + lines[end_line:]
            )
            modified_src = "\n".join(new_lines)

            # Prepend the new function before the parent function
            tree = ast.parse(modified_src + "\n\n" + new_func_src)
            ast.fix_missing_locations(tree)
            log(f"[AST] Extracted lines {start_line}–{end_line} into {new_func_name}()")
            return ast.unparse(tree)
        except Exception as exc:
            log(f"[AST] extract_function failed: {exc}", level="error")
            return source_code
