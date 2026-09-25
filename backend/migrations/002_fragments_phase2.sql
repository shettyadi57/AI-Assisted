-- ============================================================================
-- Migration: 002_fragments_phase2.sql
-- Description: Add Phase 2 fragment analysis columns (idempotent)
-- ============================================================================

-- SQLite does not support IF NOT EXISTS on ALTER TABLE.
-- We add columns only if missing by checking pragma_table_info.

-- hex_preview: first 32 bytes of fragment as space-separated uppercase hex
-- entropy_class: preliminary classification (HIGH_ENTROPY / LOW_ENTROPY / MEDIUM_ENTROPY)
-- content_class: preliminary content type (PRINTABLE / BINARY / MIXED)
-- flags_json: JSON array of forensic flags (e.g. ["DUPLICATE_OF:…"])

-- The migration runner calls executescript() so we use a CREATE TABLE trick:
-- We insert a sentinel row into a migration-tracking table if this migration
-- has not been applied, then skip if it already has.

CREATE TABLE IF NOT EXISTS applied_migrations (
    name TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
