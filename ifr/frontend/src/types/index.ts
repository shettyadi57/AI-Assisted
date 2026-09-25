/**
 * Shared TypeScript types for the IFR frontend.
 * These mirror the Pydantic schemas in backend/schemas.py exactly.
 * If you change one, change both.
 *
 * Phase 0: All types defined. Components consuming them are Phase 1+.
 */

// ── Status vocabulary ────────────────────────────────────────────────────
export type EvidenceStatus =
  | 'CONFIRMED'   // structurally validated
  | 'INFERRED'    // pattern/heuristic, not structurally proven
  | 'UNCERTAIN'   // conflicting or weak evidence
  | 'MISSING'     // expected fragment absent
  | 'CORRUPTED'   // present but damaged/unreadable
  | 'DUPLICATE';  // byte-identical to existing fragment

export type DecisionOutcome = 'ACCEPTED' | 'REJECTED' | 'DEFERRED';

// ── Phase info ───────────────────────────────────────────────────────────
export interface PhaseInfo {
  current_phase: number;
  phase_label: string;
  features_available: string[];
  features_coming: Record<string, number>; // feature_key → phase_number
}

// ── Health ───────────────────────────────────────────────────────────────
export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  db_connected: boolean;
  phase: PhaseInfo;
  timestamp: string; // ISO 8601
}

// ── Confidence evidence (Rule 2: never a bare percentage) ────────────────
export interface ConfidenceEvidence {
  sig_header_match:       number | null; // 0.0–1.0
  sig_offset_continuity:  number | null;
  sig_structural_validity:number | null;
  sig_entropy_profile:    number | null;
  sig_contradiction_count: number;
  composite_score:        number | null;
  evidence_status:        EvidenceStatus;
  not_computed_reason:    string | null;
}

// ── Evidence file ────────────────────────────────────────────────────────
export interface EvidenceFileRead {
  id: number;
  label: string;
  original_filename: string;
  size_bytes: number;
  sha256_hex: string;
  mime_type: string | null;
  is_sample_data: boolean;
  ingested_at: string;
  notes: string | null;
}

// ── Fragment ─────────────────────────────────────────────────────────────
export interface FragmentRead {
  id: number;
  evidence_file_id: number;
  sequence_index: number;
  byte_offset: number;
  size_bytes: number;
  sha256_hex: string;
  inferred_format: string | null;
  status: EvidenceStatus;
  header_bytes_hex: string | null;
  identified_at: string;
}

// ── Fragment edge (scored relationship) ──────────────────────────────────
export interface FragmentEdgeRead {
  id: number;
  source_fragment_id: number;
  target_fragment_id: number;
  evidence: ConfidenceEvidence;
  computed_at: string | null;
}

// ── Reconstruction candidate ──────────────────────────────────────────────
export interface ReconstructionCandidateRead {
  id: number;
  evidence_file_id: number;
  label: string;
  inferred_format: string | null;
  total_size_bytes: number | null;
  sha256_hex: string | null;
  outcome: DecisionOutcome | null;
  is_finalized: boolean;
  created_at: string;
  finalized_at: string | null;
}

// ── Investigator decision ─────────────────────────────────────────────────
export interface InvestigatorDecisionCreate {
  outcome: DecisionOutcome;
  rationale?: string; // required when REJECTED
}

export interface InvestigatorDecisionRead {
  id: number;
  candidate_id: number;
  outcome: DecisionOutcome;
  rationale: string | null;
  decided_at: string;
}

// ── Audit log ────────────────────────────────────────────────────────────
export interface AuditLogEntryRead {
  id: number;
  action: string;
  actor: string;
  entity_type: string | null;
  entity_id: number | null;
  detail: string | null;
  occurred_at: string;
}

// ── File format signature ─────────────────────────────────────────────────
export interface FormatSignature {
  format_id: string;
  display_name: string;
  header_magic_hex: string;
  footer_magic_hex: string | null;
  header_offset: number;
  mime_type: string;
  notes: string;
}

export interface SignatureRegistryResponse {
  count: number;
  signatures: FormatSignature[];
}

// ── Feature unavailable ───────────────────────────────────────────────────
export interface FeatureUnavailableResponse {
  available: false;
  feature: string;
  coming_in_phase: number;
  message: string;
}

// ── API utility types ─────────────────────────────────────────────────────
/** Discriminated union returned by all API calls */
export type ApiResult<T> =
  | { ok: true;  data: T }
  | { ok: false; error: string; status: number };
