"""
Tests for core/db_adapter.py — Unified DB Adapter (FS-#16)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sherly.core.db_adapter import (
    SQLiteAdapter,
    get_db_adapter,
    reset_db_adapter,
)


# ---------------------------------------------------------------------------
# SQLiteAdapter — core operations
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path: Path) -> SQLiteAdapter:
    adapter = SQLiteAdapter(db_path=tmp_path / "test.db")
    adapter.create_table(
        "CREATE TABLE IF NOT EXISTS test_kv (key TEXT PRIMARY KEY, value TEXT)"
    )
    return adapter


def test_sqlite_execute_insert_and_select(db: SQLiteAdapter) -> None:
    db.execute("INSERT INTO test_kv (key, value) VALUES (?, ?)", ("hello", "world"))
    rows = db.execute("SELECT value FROM test_kv WHERE key=?", ("hello",))
    assert rows == [("world",)]


def test_sqlite_executemany(db: SQLiteAdapter) -> None:
    pairs = [("a", "1"), ("b", "2"), ("c", "3")]
    db.executemany("INSERT OR REPLACE INTO test_kv (key, value) VALUES (?, ?)", pairs)
    rows = db.execute("SELECT key FROM test_kv ORDER BY key")
    keys = [r[0] for r in rows]
    assert "a" in keys and "b" in keys and "c" in keys


def test_sqlite_create_table_idempotent(db: SQLiteAdapter) -> None:
    # Calling create_table twice should not raise
    db.create_table(
        "CREATE TABLE IF NOT EXISTS test_kv (key TEXT PRIMARY KEY, value TEXT)"
    )


def test_sqlite_close_and_reopen(tmp_path: Path) -> None:
    adapter = SQLiteAdapter(db_path=tmp_path / "reopen.db")
    adapter.create_table("CREATE TABLE IF NOT EXISTS t (x TEXT)")
    adapter.execute("INSERT INTO t VALUES (?)", ("hello",))
    adapter.close()

    # Re-open — data must persist
    adapter2 = SQLiteAdapter(db_path=tmp_path / "reopen.db")
    rows     = adapter2.execute("SELECT x FROM t")
    assert rows == [("hello",)]


def test_sqlite_wal_mode_enabled(tmp_path: Path) -> None:
    adapter = SQLiteAdapter(db_path=tmp_path / "wal.db")
    adapter.create_table("CREATE TABLE IF NOT EXISTS dummy (x INTEGER)")
    rows = adapter.execute("PRAGMA journal_mode")
    assert rows[0][0].lower() == "wal"


# ---------------------------------------------------------------------------
# Factory — get_db_adapter (SQLite path)
# ---------------------------------------------------------------------------

def test_get_db_adapter_returns_sqlite_by_default() -> None:
    reset_db_adapter()  # Clear any existing singleton
    adapter = get_db_adapter()
    assert isinstance(adapter, SQLiteAdapter)
    reset_db_adapter()  # Cleanup


def test_get_db_adapter_returns_singleton() -> None:
    reset_db_adapter()
    a = get_db_adapter()
    b = get_db_adapter()
    assert a is b
    reset_db_adapter()


def test_reset_db_adapter_forces_new_instance() -> None:
    reset_db_adapter()
    a = get_db_adapter()
    reset_db_adapter()
    b = get_db_adapter()
    assert a is not b
    reset_db_adapter()
