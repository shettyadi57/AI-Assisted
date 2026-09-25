"""
SQLite Database Connection & Migration Runner
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


def apply_migrations() -> list[str]:
    """Apply all SQL migration files in sequence."""
    applied = []
    conn = get_db_connection()
    try:
        migration_files = sorted(Path(MIGRATIONS_DIR).glob("*.sql"))
        for migration_file in migration_files:
            with open(migration_file, "r", encoding="utf-8") as f:
                sql_content = f.read()
            conn.executescript(sql_content)
            applied.append(migration_file.name)
        conn.commit()
    finally:
        conn.close()
    return applied


if __name__ == "__main__":
    migrations = apply_migrations()
    print(f"Applied migrations: {migrations}")
