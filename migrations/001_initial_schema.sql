-- ============================================================================
-- Migration: 001_initial_schema.sql
-- Description: Core forensic database schema for Reconstruct Workbench
-- Tech Stack: SQLite 3.x
-- Compliance: Section 20 Schema & Hashing Requirements
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. EVIDENCE TABLE
-- Tracks ingested raw disk images, raw memory dumps, and storage media files.
-- All raw evidence is strictly read-only.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL UNIQUE,
    file_size_bytes INTEGER NOT NULL,
    sha256_hash TEXT NOT NULL,           -- Cryptographic hash on ingest (Sec 20)
    md5_hash TEXT,
    mime_type TEXT,
    status TEXT NOT NULL DEFAULT 'INGESTED' CHECK (status IN ('INGESTED', 'ANALYZING', 'PROCESSED', 'ERROR')),
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_evidence_sha256 ON evidence(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_evidence_status ON evidence(status);

-- ----------------------------------------------------------------------------
-- 2. SIGNATURES TABLE
-- Magic byte signatures, trailer markers, and format definitions.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS signatures (
    id TEXT PRIMARY KEY,
    format_id TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK (category IN ('image', 'document', 'archive', 'database', 'executable', 'container')),
    magic_header_hex TEXT NOT NULL,
    header_offset INTEGER NOT NULL DEFAULT 0,
    magic_trailer_hex TEXT,
    sector_aligned INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_signatures_format ON signatures(format_id);
CREATE INDEX IF NOT EXISTS idx_signatures_category ON signatures(category);

-- ----------------------------------------------------------------------------
-- 3. FRAGMENTS TABLE
-- Carved contiguous byte blocks identified from evidence.
-- Status adheres to 6 forensic states (CONFIRMED/INFERRED/UNCERTAIN/MISSING/CORRUPTED/DUPLICATE).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fragments (
    id TEXT PRIMARY KEY,
    evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    offset_start INTEGER NOT NULL,
    offset_end INTEGER NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256_hash TEXT NOT NULL,           -- Fragment content SHA-256 hash (Sec 20)
    entropy REAL,                       -- Shannon entropy [0.0 - 8.0]
    signature_id TEXT REFERENCES signatures(id),
    status TEXT NOT NULL DEFAULT 'UNCERTAIN' CHECK (status IN ('CONFIRMED', 'INFERRED', 'UNCERTAIN', 'MISSING', 'CORRUPTED', 'DUPLICATE')),
    inferred_format TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    CONSTRAINT chk_fragment_offsets CHECK (offset_end > offset_start),
    CONSTRAINT chk_fragment_size CHECK (size_bytes = offset_end - offset_start)
);

CREATE INDEX IF NOT EXISTS idx_fragments_evidence ON fragments(evidence_id);
CREATE INDEX IF NOT EXISTS idx_fragments_sha256 ON fragments(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_fragments_status ON fragments(status);
CREATE INDEX IF NOT EXISTS idx_fragments_offset ON fragments(evidence_id, offset_start);

-- ----------------------------------------------------------------------------
-- 4. CANDIDATES TABLE
-- Reconstruction candidate files representing proposed assemblies of fragments.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target_format TEXT NOT NULL,
    total_size_bytes INTEGER NOT NULL DEFAULT 0,
    fragment_count INTEGER NOT NULL DEFAULT 0,
    composite_confidence REAL NOT NULL DEFAULT 0.0, -- [0.0 - 1.0]
    status TEXT NOT NULL DEFAULT 'UNCERTAIN' CHECK (status IN ('PENDING_REVIEW', 'ACCEPTED', 'REJECTED', 'UNCERTAIN')),
    reconstruction_sha256 TEXT,         -- Final assembled file hash (Sec 20)
    is_finalized INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_format ON candidates(target_format);
CREATE INDEX IF NOT EXISTS idx_candidates_hash ON candidates(reconstruction_sha256);

-- ----------------------------------------------------------------------------
-- 5. CANDIDATE_FRAGMENTS TABLE
-- Ordered sequence of fragments in an assembled candidate, with edge scores.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidate_fragments (
    candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    fragment_id TEXT NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL,
    edge_confidence REAL,               -- Composite edge score from previous fragment
    edge_signals_json TEXT,             -- JSON decomposed 5-signal evidence
    decision TEXT NOT NULL DEFAULT 'PENDING' CHECK (decision IN ('PENDING', 'ACCEPTED', 'REJECTED')),
    decision_rationale TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (candidate_id, sequence_order)
);

CREATE INDEX IF NOT EXISTS idx_cf_fragment ON candidate_fragments(fragment_id);
CREATE INDEX IF NOT EXISTS idx_cf_candidate ON candidate_fragments(candidate_id);

-- ----------------------------------------------------------------------------
-- 6. VALIDATION_RESULTS TABLE
-- Structural parser validation outputs for candidates and assemblies.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_results (
    id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    validator_name TEXT NOT NULL,       -- e.g. "PDFValidator", "JPEGValidator"
    is_valid INTEGER NOT NULL DEFAULT 0 CHECK (is_valid IN (0, 1)),
    status TEXT NOT NULL CHECK (status IN ('VALID', 'CORRUPTED', 'UNCERTAIN')),
    errors_json TEXT DEFAULT '[]',
    warnings_json TEXT DEFAULT '[]',
    structural_hash TEXT,               -- Structural checksum / AST signature (Sec 20)
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_val_candidate ON validation_results(candidate_id);
CREATE INDEX IF NOT EXISTS idx_val_status ON validation_results(status);

-- ----------------------------------------------------------------------------
-- 7. AUDIT_LOG TABLE
-- Immutable, tamper-evident forensic log for investigator actions and edge decisions.
-- Chain of custody verified via prev_state_hash -> entry_hash linkage.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,           -- e.g. EVIDENCE_INGESTED, EDGE_ACCEPTED, EDGE_REJECTED
    entity_type TEXT NOT NULL,          -- e.g. evidence, candidate_fragment, candidate
    entity_id TEXT NOT NULL,
    investigator_id TEXT NOT NULL DEFAULT 'investigator',
    action_detail TEXT NOT NULL,
    prev_state_hash TEXT,               -- Previous audit record hash (chain-of-custody)
    entry_hash TEXT NOT NULL,           -- SHA-256 hash of this entry's payload (Sec 20)
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);

-- ----------------------------------------------------------------------------
-- TRIGGERS FOR AUTO-UPDATING updated_at TIMESTAMP
-- ----------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_evidence_updated_at 
AFTER UPDATE ON evidence BEGIN 
    UPDATE evidence SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id; 
END;

CREATE TRIGGER IF NOT EXISTS trg_signatures_updated_at 
AFTER UPDATE ON signatures BEGIN 
    UPDATE signatures SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id; 
END;

CREATE TRIGGER IF NOT EXISTS trg_fragments_updated_at 
AFTER UPDATE ON fragments BEGIN 
    UPDATE fragments SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id; 
END;

CREATE TRIGGER IF NOT EXISTS trg_candidates_updated_at 
AFTER UPDATE ON candidates BEGIN 
    UPDATE candidates SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id; 
END;

CREATE TRIGGER IF NOT EXISTS trg_candidate_fragments_updated_at 
AFTER UPDATE ON candidate_fragments BEGIN 
    UPDATE candidate_fragments SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') 
    WHERE candidate_id = OLD.candidate_id AND sequence_order = OLD.sequence_order; 
END;

CREATE TRIGGER IF NOT EXISTS trg_validation_results_updated_at 
AFTER UPDATE ON validation_results BEGIN 
    UPDATE validation_results SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id; 
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_log_updated_at 
AFTER UPDATE ON audit_log BEGIN 
    UPDATE audit_log SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id; 
END;
