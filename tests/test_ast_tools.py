"""
Tests for tools/ast_tools.py — AST-Aware Code Patching (FS-#26)
"""

from __future__ import annotations

import pytest

from sherly.tools.ast_tools import ASTPatcher

SAMPLE = """\
import os

def greet(name: str) -> str:
    return f"Hello, {name}"

def farewell(name: str) -> str:
    return f"Goodbye, {name}"

class MyClass:
    def method_a(self) -> None:
        pass

    def method_b(self) -> str:
        return "original"
"""


@pytest.fixture
def patcher() -> ASTPatcher:
    return ASTPatcher()


# ---------------------------------------------------------------------------
# get_function_names
# ---------------------------------------------------------------------------

def test_get_function_names_lists_top_level(patcher: ASTPatcher) -> None:
    names = patcher.get_function_names(SAMPLE)
    assert "greet"    in names
    assert "farewell" in names
    # Class methods should NOT appear as top-level functions
    # (they have col_offset > 0)


def test_get_function_names_empty_source(patcher: ASTPatcher) -> None:
    assert patcher.get_function_names("") == []


# ---------------------------------------------------------------------------
# get_imports
# ---------------------------------------------------------------------------

def test_get_imports(patcher: ASTPatcher) -> None:
    imports = patcher.get_imports(SAMPLE)
    assert any("os" in imp for imp in imports)


# ---------------------------------------------------------------------------
# patch_function / transform_function
# ---------------------------------------------------------------------------

def test_patch_function_replaces_body(patcher: ASTPatcher) -> None:
    new_body   = 'return "patched"'
    result     = patcher.patch_function(SAMPLE, "greet", new_body)
    assert "patched" in result
    # Original body gone
    assert "Hello" not in result


def test_transform_function_alias_works(patcher: ASTPatcher) -> None:
    """transform_function is the backward-compat alias for patch_function."""
    result = patcher.transform_function(SAMPLE, "farewell", 'return "bye"')
    assert "bye" in result


def test_patch_function_unknown_name_unchanged(patcher: ASTPatcher) -> None:
    """Patching a non-existent function returns the original source."""
    result = patcher.patch_function(SAMPLE, "nonexistent_func", "pass")
    assert "greet" in result  # source essentially unchanged


# ---------------------------------------------------------------------------
# patch_class_method
# ---------------------------------------------------------------------------

def test_patch_class_method(patcher: ASTPatcher) -> None:
    result = patcher.patch_class_method(SAMPLE, "MyClass", "method_b", 'return "new"')
    assert "new" in result
    assert "original" not in result


def test_patch_class_method_wrong_class_unchanged(patcher: ASTPatcher) -> None:
    result = patcher.patch_class_method(SAMPLE, "NoSuchClass", "method_b", "pass")
    assert "original" in result


# ---------------------------------------------------------------------------
# add_import
# ---------------------------------------------------------------------------

def test_add_import_inserts_new(patcher: ASTPatcher) -> None:
    result = patcher.add_import(SAMPLE, "import sys")
    assert "import sys" in result


def test_add_import_no_duplicate(patcher: ASTPatcher) -> None:
    """Adding an already-present import should not duplicate it."""
    result = patcher.add_import(SAMPLE, "import os")
    assert result.count("import os") == 1


# ---------------------------------------------------------------------------
# rename_symbol
# ---------------------------------------------------------------------------

def test_rename_symbol_renames_def(patcher: ASTPatcher) -> None:
    result = patcher.rename_symbol(SAMPLE, "greet", "welcome")
    assert "def welcome" in result
    assert "def greet" not in result


def test_rename_symbol_renames_call_sites(patcher: ASTPatcher) -> None:
    source = "def foo(): return 1\nresult = foo()\n"
    result = patcher.rename_symbol(source, "foo", "bar")
    assert "def bar" in result
    assert "bar()" in result
    assert "foo" not in result


# ---------------------------------------------------------------------------
# extract_function
# ---------------------------------------------------------------------------

def test_extract_function_creates_new_def(patcher: ASTPatcher) -> None:
    source = "def big_func():\n    x = 1\n    y = 2\n    z = x + y\n    return z\n"
    result = patcher.extract_function(source, 2, 3, "compute_xy")
    assert "def compute_xy" in result
    assert "compute_xy()" in result
