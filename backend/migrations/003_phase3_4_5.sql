-- ============================================================================
-- Migration: 003_phase3_4_5.sql
-- Description: Add Phase 3, 4, and 5 columns for signature detection,
--              relationship scoring, candidate traversal, and reassembly.
-- ============================================================================

-- Idempotent helper creates tables or indexes if missing.
-- Column additions to existing tables are handled via database.py pragma check.

CREATE TABLE IF NOT EXISTS candidate_edges (
    id TEXT PRIMARY KEY,
    evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    source_fragment_id TEXT NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
    target_fragment_id TEXT NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
    composite_confidence REAL NOT NULL,
    signature_match REAL NOT NULL,
    offset_continuity REAL NOT NULL,
    structural_validity REAL NOT NULL,
    entropy_compatibility REAL NOT NULL,
    contradiction_count INTEGER NOT NULL DEFAULT 0,
    decision TEXT NOT NULL DEFAULT 'PENDING' CHECK (decision IN ('PENDING', 'ACCEPTED', 'REJECTED')),
    decision_rationale TEXT,
    evidence_strings_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON candidate_edges(source_fragment_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON candidate_edges(target_fragment_id);
CREATE INDEX IF NOT EXISTS idx_edges_evidence ON candidate_edges(evidence_id);
