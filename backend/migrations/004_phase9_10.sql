-- ============================================================================
-- Migration: 004_phase9_10.sql
-- Description: Phase 9 ML Extension Point configuration & Phase 10 Provenance,
--              Export Tracking, and Forensic Evidence Report artifacts.
-- ============================================================================

CREATE TABLE IF NOT EXISTS export_records (
    id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    export_type TEXT NOT NULL CHECK (export_type IN ('ARTIFACT', 'BUNDLE_ZIP', 'EVIDENCE_REPORT')),
    export_filename TEXT NOT NULL,
    export_path TEXT NOT NULL,
    export_sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    tool_version TEXT NOT NULL DEFAULT 'reconstruct-v0.5.0-alpha',
    config_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_exports_candidate ON export_records(candidate_id);
CREATE INDEX IF NOT EXISTS idx_exports_evidence ON export_records(evidence_id);
CREATE INDEX IF NOT EXISTS idx_exports_sha256 ON export_records(export_sha256);
