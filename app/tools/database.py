"""Built-in tool: SQL database management.

Default: local SQLite (zero config, just works).
Override: set DATABASE_URL in .env for external Postgres/MySQL/etc.

Tools provided:
  - sql_query:    Read-only SELECT queries
  - sql_execute:  Write queries (CREATE, INSERT, UPDATE, DELETE)
  - sql_describe: List tables and their schemas
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.tools.registry import registry

log = get_logger("database")


def _get_db_path() -> str:
    """Get database path from config or default."""
    return os.getenv("DATABASE_PATH", "agent_harness.db")


def _get_connection() -> sqlite3.Connection:
    """Create a SQLite connection with sensible defaults."""
    db_path = _get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# --- Tool Input Models ---


class SqlQueryInput(BaseModel):
    query: str = Field(description="SQL SELECT query to execute (read-only)")
    params: list[str] = Field(default_factory=list, description="Query parameters for ? placeholders")
    limit: int = Field(default=100, ge=1, le=1000, description="Max rows to return")


class SqlExecuteInput(BaseModel):
    query: str = Field(description="SQL statement to execute (CREATE, INSERT, UPDATE, DELETE, ALTER)")
    params: list[str] = Field(default_factory=list, description="Query parameters for ? placeholders")


# --- Tool Implementations ---


def _run_query(query: str, params: list[str], limit: int) -> str:
    """Execute a read-only query and return formatted results."""
    query_stripped = query.strip().upper()
    if not query_stripped.startswith("SELECT") and not query_stripped.startswith("PRAGMA"):
        return "Error: sql_query only supports SELECT and PRAGMA statements. Use sql_execute for writes."

    conn = _get_connection()
    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchmany(limit)

        if not rows:
            return "Query returned 0 rows."

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Format as readable table
        lines = [f"Columns: {', '.join(columns)}", f"Rows returned: {len(rows)}", ""]

        for i, row in enumerate(rows):
            row_data = {col: row[j] for j, col in enumerate(columns)}
            lines.append(f"  Row {i + 1}: {row_data}")

        if len(rows) == limit:
            lines.append(f"\n  ... (limited to {limit} rows, use 'limit' param for more)")

        return "\n".join(lines)
    finally:
        conn.close()


def _run_execute(query: str, params: list[str]) -> str:
    """Execute a write statement."""
    query_stripped = query.strip().upper()

    # Safety: block dangerous operations unless explicitly enabled
    dangerous = ["DROP DATABASE", "DROP SCHEMA"]
    for d in dangerous:
        if d in query_stripped:
            return f"Error: '{d}' is blocked for safety. Remove this check in database.py if intended."

    conn = _get_connection()
    try:
        cursor = conn.execute(query, params)
        conn.commit()
        return (
            f"Success. Rows affected: {cursor.rowcount}. "
            f"Last row ID: {cursor.lastrowid if cursor.lastrowid else 'N/A'}"
        )
    except sqlite3.Error as e:
        return f"SQL Error: {e}"
    finally:
        conn.close()


def _describe_tables() -> str:
    """List all tables and their schemas."""
    conn = _get_connection()
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            return "No tables found. The database is empty."

        lines = [f"Database: {_get_db_path()}", f"Tables: {len(tables)}", ""]

        for table in tables:
            lines.append(f"── {table} ──")
            col_cursor = conn.execute(f"PRAGMA table_info('{table}')")
            for col in col_cursor.fetchall():
                # col: (cid, name, type, notnull, default_value, pk)
                pk = " [PK]" if col[5] else ""
                nullable = "" if col[3] else " NULL"
                lines.append(f"  {col[1]}: {col[2]}{pk}{nullable}")

            # Row count
            count = conn.execute(f"SELECT COUNT(*) FROM '{table}'").fetchone()[0]
            lines.append(f"  ({count} rows)")
            lines.append("")

        return "\n".join(lines)
    finally:
        conn.close()


# --- Register Tools ---


@registry.register(
    name="sql_query",
    description="Execute a read-only SQL SELECT query against the database. Returns formatted results. Use this to look up data, run analytics, or inspect table contents.",
    args_model=SqlQueryInput,
)
def sql_query(query: str, params: list[str] | None = None, limit: int = 100) -> str:
    """Run a SELECT query."""
    return _run_query(query, params or [], limit)


@registry.register(
    name="sql_execute",
    description="Execute a SQL write statement (CREATE TABLE, INSERT, UPDATE, DELETE, ALTER). Use this to create schemas, add data, or modify the database structure.",
    args_model=SqlExecuteInput,
)
def sql_execute(query: str, params: list[str] | None = None) -> str:
    """Run a write query."""
    return _run_execute(query, params or [])


class SqlDescribeInput(BaseModel):
    """No arguments needed — describes all tables."""


@registry.register(
    name="sql_describe",
    description="List all tables in the database with their column schemas and row counts. Use this to understand the database structure before writing queries.",
    args_model=SqlDescribeInput,
)
def sql_describe() -> str:
    """Describe all tables."""
    return _describe_tables()
