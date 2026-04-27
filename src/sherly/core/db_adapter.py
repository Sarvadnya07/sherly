"""
DATABASE ADAPTER — db_adapter.py
Implements:
  FS-#16  PostgreSQL + ChromaDB Server Mode.
           Provides a unified DB interface that transparently switches between
           SQLite (local dev) and PostgreSQL (production) based on config.json.

  Configuration (config.json):
    {
      "db_backend": "sqlite" | "postgresql",
      "postgresql": {
        "host": "localhost",
        "port": 5432,
        "database": "sherly",
        "user": "sherly",
        "password": "..."
      }
    }

  SQLAlchemy is used as the ORM layer so queries are identical across backends.
  Falls back gracefully to SQLite when SQLAlchemy / psycopg2 are not installed.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path
from typing import Any

from sherly.utils.runtime_utils import log


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _get_db_config() -> dict[str, Any]:
    try:
        from sherly.config.config_manager import load_config
        return load_config()
    except Exception:
        return {}


def _get_backend() -> str:
    """Return 'sqlite' or 'postgresql' based on config."""
    return _get_db_config().get("db_backend", "sqlite").lower()


def _get_pg_url() -> str:
    cfg  = _get_db_config().get("postgresql", {})
    host = cfg.get("host", os.environ.get("PGHOST", "localhost"))
    port = cfg.get("port", int(os.environ.get("PGPORT", "5432")))
    name = cfg.get("database", os.environ.get("PGDATABASE", "sherly"))
    user = cfg.get("user", os.environ.get("PGUSER", "sherly"))
    pwd  = cfg.get("password", os.environ.get("PGPASSWORD", ""))
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"


# ---------------------------------------------------------------------------
# SQLite adapter (no extra deps)
# ---------------------------------------------------------------------------

_SQLITE_PATH = Path(__file__).parent.parent / "data" / "sherly.db"
_sqlite_lock = threading.Lock()


class SQLiteAdapter:
    """Thin wrapper around sqlite3 for local development."""

    def __init__(self, db_path: str | Path = _SQLITE_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._conn_lock = threading.Lock()

    def _get_conn(self) -> sqlite3.Connection:
        with self._conn_lock:
            if self._conn is None:
                self._conn = sqlite3.connect(
                    str(self.db_path), check_same_thread=False
                )
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA foreign_keys=ON")
                self._conn.commit()
        return self._conn

    def execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        conn = self._get_conn()
        with _sqlite_lock:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.fetchall()

    def executemany(self, sql: str, params_seq: list[tuple]) -> None:
        conn = self._get_conn()
        with _sqlite_lock:
            conn.executemany(sql, params_seq)
            conn.commit()

    def create_table(self, ddl: str) -> None:
        self.execute(ddl)

    def close(self) -> None:
        with self._conn_lock:
            if self._conn:
                self._conn.close()
                self._conn = None


# ---------------------------------------------------------------------------
# PostgreSQL adapter (SQLAlchemy + psycopg2)
# ---------------------------------------------------------------------------

class PostgreSQLAdapter:
    """
    FS-#16: PostgreSQL adapter via SQLAlchemy Core.
    Requires: pip install sqlalchemy psycopg2-binary
    """

    def __init__(self) -> None:
        self._engine = None
        self._pool_lock = threading.Lock()

    def _get_engine(self):
        with self._pool_lock:
            if self._engine is None:
                try:
                    from sqlalchemy import create_engine
                    url = _get_pg_url()
                    self._engine = create_engine(
                        url,
                        pool_size=5,
                        max_overflow=10,
                        pool_pre_ping=True,
                        echo=False,
                    )
                    log(f"[DBAdapter] PostgreSQL engine created: {url.split('@')[-1]}")
                except ImportError:
                    raise RuntimeError(
                        "SQLAlchemy + psycopg2 required for PostgreSQL. "
                        "Install: pip install sqlalchemy psycopg2-binary"
                    )
        return self._engine

    def execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(sql), dict(enumerate(params)))
            conn.commit()
            return list(result.fetchall())

    def executemany(self, sql: str, params_seq: list[tuple]) -> None:
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            for params in params_seq:
                conn.execute(text(sql), dict(enumerate(params)))
            conn.commit()

    def create_table(self, ddl: str) -> None:
        self.execute(ddl)

    def close(self) -> None:
        with self._pool_lock:
            if self._engine:
                self._engine.dispose()
                self._engine = None


# ---------------------------------------------------------------------------
# Factory — unified interface (FS-#16)
# ---------------------------------------------------------------------------

_adapter_instance: SQLiteAdapter | PostgreSQLAdapter | None = None
_adapter_lock = threading.Lock()


def get_db_adapter() -> SQLiteAdapter | PostgreSQLAdapter:
    """
    FS-#16: Return the appropriate DB adapter based on config.json → db_backend.

    Call this instead of connecting to SQLite directly — when the config is
    switched to 'postgresql', all existing code automatically uses Postgres.
    """
    global _adapter_instance
    with _adapter_lock:
        if _adapter_instance is None:
            backend = _get_backend()
            if backend == "postgresql":
                try:
                    _adapter_instance = PostgreSQLAdapter()
                    log("[DBAdapter] Using PostgreSQL backend.")
                except Exception as exc:
                    log(
                        f"[DBAdapter] PostgreSQL unavailable ({exc}), falling back to SQLite.",
                        level="warning",
                    )
                    _adapter_instance = SQLiteAdapter()
            else:
                _adapter_instance = SQLiteAdapter()
                log("[DBAdapter] Using SQLite backend.")
    return _adapter_instance


def reset_db_adapter() -> None:
    """Force re-creation of the adapter (useful after config changes or in tests)."""
    global _adapter_instance
    with _adapter_lock:
        if _adapter_instance:
            _adapter_instance.close()
        _adapter_instance = None


# ---------------------------------------------------------------------------
# ChromaDB server mode helper (FS-#16)
# ---------------------------------------------------------------------------

def get_chroma_client():
    """
    FS-#16: Return a ChromaDB client in either embedded or server mode.
    Controlled by config.json → chroma_config.mode = "embedded" | "server".

    Server mode requires a running ChromaDB HTTP server:
      docker run -p 8000:8000 chromadb/chroma
    Or: pip install chromadb && chroma run --path ./chroma_data
    """
    try:
        import chromadb
        cfg  = _get_db_config().get("chroma_config", {})
        mode = cfg.get("mode", "embedded")

        if mode == "server":
            host = cfg.get("host", os.environ.get("CHROMA_HOST", "localhost"))
            port = int(cfg.get("port", os.environ.get("CHROMA_PORT", "8000")))
            log(f"[ChromaDB] Using HTTP client → {host}:{port}")
            return chromadb.HttpClient(host=host, port=port)

        path = cfg.get("path", "memory_rag")
        log(f"[ChromaDB] Using embedded client → {path}")
        return chromadb.PersistentClient(path=path)

    except ImportError:
        log("[ChromaDB] chromadb not installed — vector search unavailable.", level="warning")
        return None
    except Exception as exc:
        log(f"[ChromaDB] Client error: {exc}", level="error")
        return None
