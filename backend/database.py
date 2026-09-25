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


def _ensure_phase3_4_5_columns(conn: sqlite3.Connection) -> None:
    """Idempotently add Phase 3, 4, 5 columns to fragments and candidates tables."""
    # fragments table additions
    existing_frag = _existing_columns(conn, "fragments")
    frag_cols = {
        "role_guess":            "ALTER TABLE fragments ADD COLUMN role_guess TEXT DEFAULT 'UNKNOWN'",
        "signature_confidence":  "ALTER TABLE fragments ADD COLUMN signature_confidence REAL DEFAULT 0.0",
        "matched_magic_hex":     "ALTER TABLE fragments ADD COLUMN matched_magic_hex TEXT",
        "matched_magic_offset":  "ALTER TABLE fragments ADD COLUMN matched_magic_offset INTEGER DEFAULT 0",
        "matched_magic_length":  "ALTER TABLE fragments ADD COLUMN matched_magic_length INTEGER DEFAULT 0",
        "structural_notes":      "ALTER TABLE fragments ADD COLUMN structural_notes TEXT",
    }
    for col, ddl in frag_cols.items():
        if col not in existing_frag:
            conn.execute(ddl)

    # candidates table additions
    existing_cand = _existing_columns(conn, "candidates")
    cand_cols = {
        "evidence_id":            "ALTER TABLE candidates ADD COLUMN evidence_id TEXT",
        "recovered_fragments":    "ALTER TABLE candidates ADD COLUMN recovered_fragments INTEGER DEFAULT 0",
        "missing_fragments":      "ALTER TABLE candidates ADD COLUMN missing_fragments INTEGER DEFAULT 0",
        "duplicate_fragments":    "ALTER TABLE candidates ADD COLUMN duplicate_fragments INTEGER DEFAULT 0",
        "corrupted_fragments":    "ALTER TABLE candidates ADD COLUMN corrupted_fragments INTEGER DEFAULT 0",
        "reconstructed_bytes":    "ALTER TABLE candidates ADD COLUMN reconstructed_bytes INTEGER DEFAULT 0",
        "missing_bytes":          "ALTER TABLE candidates ADD COLUMN missing_bytes INTEGER DEFAULT 0",
        "coverage_pct":           "ALTER TABLE candidates ADD COLUMN coverage_pct REAL DEFAULT 0.0",
        "gaps_json":              "ALTER TABLE candidates ADD COLUMN gaps_json TEXT NOT NULL DEFAULT '[]'",
        "evidence_strings_json":  "ALTER TABLE candidates ADD COLUMN evidence_strings_json TEXT NOT NULL DEFAULT '[]'",
        "artifact_path":          "ALTER TABLE candidates ADD COLUMN artifact_path TEXT",
        "recovery_status":        "ALTER TABLE candidates ADD COLUMN recovery_status TEXT DEFAULT 'UNCERTAIN'",
    }
    for col, ddl in cand_cols.items():
        if col not in existing_cand:
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

        # Idempotent column additions
        _ensure_phase2_columns(conn)
        _ensure_phase3_4_5_columns(conn)

    finally:
        conn.close()
    return applied


if __name__ == "__main__":
    migrations = apply_migrations()
    print(f"Applied migrations: {migrations}")
