"""
SQLite Database Connection & Migration Runner

Runs raw SQL migration scripts from backend/migrations/*.sql in filename order.
Also handles SQLite-specific idempotent column additions for ALTER TABLE statements
(SQLite does not support ALTER TABLE ... ADD COLUMN IF NOT EXISTS).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from backend.config import DATABASE_PATH, MIGRATIONS_DIR


def get_db_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the set of column names currently in a table."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _ensure_phase2_columns(conn: sqlite3.Connection) -> None:
    """
    Idempotently add Phase 2 columns to the fragments table.

    SQLite does not support 'ALTER TABLE … ADD COLUMN IF NOT EXISTS',
    so we check pragma_table_info before each ALTER.
    """
    existing = _existing_columns(conn, "fragments")
    phase2_cols = {
        "hex_preview":   "ALTER TABLE fragments ADD COLUMN hex_preview TEXT",
        "entropy_class": "ALTER TABLE fragments ADD COLUMN entropy_class TEXT",
        "content_class": "ALTER TABLE fragments ADD COLUMN content_class TEXT",
        "flags_json":    "ALTER TABLE fragments ADD COLUMN flags_json TEXT NOT NULL DEFAULT '[]'",
    }
    for col, ddl in phase2_cols.items():
        if col not in existing:
            conn.execute(ddl)
    conn.commit()


def apply_migrations() -> list[str]:
    """Apply all SQL migration files in sequence, then run Python schema fixups."""
    applied: list[str] = []
    conn = get_db_connection()
    try:
        migration_files = sorted(Path(MIGRATIONS_DIR).glob("*.sql"))
        for migration_file in migration_files:
            with open(migration_file, "r", encoding="utf-8") as f:
                sql_content = f.read()
            conn.executescript(sql_content)
            applied.append(migration_file.name)
        conn.commit()

        # Phase 2 column additions (idempotent — safe to run on every startup)
        _ensure_phase2_columns(conn)

    finally:
        conn.close()
    return applied


if __name__ == "__main__":
    migrations = apply_migrations()
    print(f"Applied migrations: {migrations}")
