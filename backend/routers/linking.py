"""
Linking Stage Router — Phase 4 LIVE: Relationship Scoring & Graph Linking

Provides real endpoints for evaluating multi-signal candidate relationships
between fragments, inspecting decomposed edge signals, and recording
investigator accept/reject decisions.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, status

from backend.config import PROJECT_ROOT
from backend.database import get_db_connection
from backend.schemas import (
    EdgeDecisionRequest,
    EdgeEvidenceFactorsSchema,
    RelationshipEdgeSchema,
    RelationshipScoreRequest,
)
from core.fragment_analyzer import FragmentMetadata, ForensicStatus
from core.relationship_engine import default_relationship_engine, EdgeEvidenceFactors

logger = logging.getLogger("reconstruct.linking")
router = APIRouter(prefix="/linking", tags=["Pipeline Stage: Linking"])


def _resolve_evidence_path(filepath: str) -> Path:
    p = Path(filepath)
    if p.is_absolute() and p.exists():
        return p
    rel = PROJECT_ROOT / filepath
    if rel.exists():
        return rel
    raise FileNotFoundError(f"Evidence file not found at '{filepath}'.")


def _row_to_meta(row) -> FragmentMetadata:
    keys = row.keys() if hasattr(row, "keys") else []
    return FragmentMetadata(
        fragment_id=row["id"],
        evidence_id=row["evidence_id"],
        offset_start=row["offset_start"],
        offset_end=row["offset_end"],
        size_bytes=row["size_bytes"],
        sha256_hash=row["sha256_hash"],
        entropy=row["entropy"] or 0.0,
        status=ForensicStatus(row["status"]) if row["status"] in ForensicStatus._value2member_map_ else ForensicStatus.UNCERTAIN,
        entropy_class=row["entropy_class"] or "UNKNOWN",
        content_class=row["content_class"] or "UNKNOWN",
        hex_preview=row["hex_preview"] or "",
        flags=json.loads(row["flags_json"] or "[]"),
        inferred_format=row["inferred_format"],
        role_guess=row["role_guess"] if "role_guess" in keys and row["role_guess"] else "UNKNOWN",
        signature_confidence=row["signature_confidence"] if "signature_confidence" in keys and row["signature_confidence"] else 0.0,
        matched_magic_hex=row["matched_magic_hex"] if "matched_magic_hex" in keys else None,
        matched_magic_offset=row["matched_magic_offset"] if "matched_magic_offset" in keys and row["matched_magic_offset"] is not None else 0,
        matched_magic_length=row["matched_magic_length"] if "matched_magic_length" in keys and row["matched_magic_length"] is not None else 0,
        structural_notes=row["structural_notes"] if "structural_notes" in keys and row["structural_notes"] else "",
    )


@router.post(
    "/score",
    response_model=RelationshipEdgeSchema,
    status_code=status.HTTP_200_OK,
    summary="Evaluate multi-signal candidate relationship between two fragments",
)
async def score_relationship(req: RelationshipScoreRequest = Body(...)) -> RelationshipEdgeSchema:
    """Evaluate directed relationship from source to target fragment on 5 evidence signals."""
    conn = get_db_connection()
    try:
        s_row = conn.execute("SELECT f.*, e.filepath FROM fragments f JOIN evidence e ON f.evidence_id = e.id WHERE f.id = ?", (req.source_fragment_id,)).fetchone()
        t_row = conn.execute("SELECT f.*, e.filepath FROM fragments f JOIN evidence e ON f.evidence_id = e.id WHERE f.id = ?", (req.target_fragment_id,)).fetchone()

        if not s_row:
            raise HTTPException(status_code=404, detail=f"Source fragment not found: {req.source_fragment_id}")
        if not t_row:
            raise HTTPException(status_code=404, detail=f"Target fragment not found: {req.target_fragment_id}")

        ev_path = _resolve_evidence_path(s_row["filepath"])
        with open(ev_path, "rb") as f:
            f.seek(s_row["offset_start"])
            s_bytes = f.read(s_row["size_bytes"])
            f.seek(t_row["offset_start"])
            t_bytes = f.read(t_row["size_bytes"])

        s_meta = _row_to_meta(s_row)
        t_meta = _row_to_meta(t_row)

        rel = default_relationship_engine.evaluate_relationship(
            source_meta=s_meta,
            target_meta=t_meta,
            source_bytes=s_bytes,
            target_bytes=t_bytes,
            target_format=req.target_format,
        )

        edge_id = f"edge-{s_meta.fragment_id[:8]}-{t_meta.fragment_id[:8]}"
        return RelationshipEdgeSchema(
            id=edge_id,
            evidence_id=req.evidence_id,
            source_fragment_id=s_meta.fragment_id,
            target_fragment_id=t_meta.fragment_id,
            composite_confidence=rel.composite_confidence,
            factors=EdgeEvidenceFactorsSchema(
                signature_match=rel.factors.signature_match,
                offset_continuity=rel.factors.offset_continuity,
                structural_validity=rel.factors.structural_validity,
                entropy_compatibility=rel.factors.entropy_compatibility,
                contradiction_count=rel.factors.contradiction_count,
            ),
            decision=rel.decision.value,
            decision_rationale=rel.decision_rationale,
            evidence_strings=rel.evidence_strings,
        )
    finally:
        conn.close()


@router.post(
    "/generate",
    response_model=list[RelationshipEdgeSchema],
    summary="Generate and persist candidate graph edges for an evidence record",
)
async def generate_edges(evidence_id: str = Query(...)) -> list[RelationshipEdgeSchema]:
    """Generate all candidate relationships for fragments belonging to an evidence record."""
    conn = get_db_connection()
    try:
        ev_row = conn.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
        if not ev_row:
            raise HTTPException(status_code=404, detail=f"Evidence not found: {evidence_id}")

        ev_path = _resolve_evidence_path(ev_row["filepath"])
        raw_bytes = ev_path.read_bytes()

        frag_rows = conn.execute(
            "SELECT * FROM fragments WHERE evidence_id = ? ORDER BY offset_start",
            (evidence_id,),
        ).fetchall()
        if not frag_rows:
            raise HTTPException(status_code=400, detail="No fragments found for evidence. Run analysis first.")

        metas = [_row_to_meta(r) for r in frag_rows]
        bytes_map = {m.fragment_id: raw_bytes[m.offset_start : m.offset_end] for m in metas}

        edges = default_relationship_engine.build_candidate_graph(metas, fragment_bytes_map=bytes_map)

        results: list[RelationshipEdgeSchema] = []
        for rel in edges:
            edge_id = f"edge-{rel.source_fragment_id[:8]}-{rel.target_fragment_id[:8]}"
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO candidate_edges
                       (id, evidence_id, source_fragment_id, target_fragment_id,
                        composite_confidence, signature_match, offset_continuity,
                        structural_validity, entropy_compatibility, contradiction_count,
                        decision, decision_rationale, evidence_strings_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        edge_id,
                        evidence_id,
                        rel.source_fragment_id,
                        rel.target_fragment_id,
                        rel.composite_confidence,
                        rel.factors.signature_match,
                        rel.factors.offset_continuity,
                        rel.factors.structural_validity,
                        rel.factors.entropy_compatibility,
                        rel.factors.contradiction_count,
                        rel.decision.value,
                        rel.decision_rationale,
                        json.dumps(rel.evidence_strings),
                    ),
                )
            except Exception as e:
                logger.warning("Edge insert failed: %s", e)

            results.append(RelationshipEdgeSchema(
                id=edge_id,
                evidence_id=evidence_id,
                source_fragment_id=rel.source_fragment_id,
                target_fragment_id=rel.target_fragment_id,
                composite_confidence=rel.composite_confidence,
                factors=EdgeEvidenceFactorsSchema(
                    signature_match=rel.factors.signature_match,
                    offset_continuity=rel.factors.offset_continuity,
                    structural_validity=rel.factors.structural_validity,
                    entropy_compatibility=rel.factors.entropy_compatibility,
                    contradiction_count=rel.factors.contradiction_count,
                ),
                decision=rel.decision.value,
                decision_rationale=rel.decision_rationale,
                evidence_strings=rel.evidence_strings,
            ))

        conn.commit()
        return results
    finally:
        conn.close()


@router.get(
    "/relationships",
    response_model=list[RelationshipEdgeSchema],
    summary="Retrieve candidate relationship graph edges with decomposed scores",
)
async def list_relationships(
    evidence_id: str | None = Query(default=None),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
) -> list[RelationshipEdgeSchema]:
    """Retrieve persisted candidate edges from SQLite."""
    conn = get_db_connection()
    try:
        if evidence_id:
            rows = conn.execute(
                "SELECT * FROM candidate_edges WHERE evidence_id = ? AND composite_confidence >= ? ORDER BY composite_confidence DESC",
                (evidence_id, min_confidence),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM candidate_edges WHERE composite_confidence >= ? ORDER BY composite_confidence DESC",
                (min_confidence,),
            ).fetchall()

        return [
            RelationshipEdgeSchema(
                id=r["id"],
                evidence_id=r["evidence_id"],
                source_fragment_id=r["source_fragment_id"],
                target_fragment_id=r["target_fragment_id"],
                composite_confidence=r["composite_confidence"],
                factors=EdgeEvidenceFactorsSchema(
                    signature_match=r["signature_match"],
                    offset_continuity=r["offset_continuity"],
                    structural_validity=r["structural_validity"],
                    entropy_compatibility=r["entropy_compatibility"],
                    contradiction_count=r["contradiction_count"],
                ),
                decision=r["decision"],
                decision_rationale=r["decision_rationale"],
                evidence_strings=json.loads(r["evidence_strings_json"] or "[]"),
            )
            for r in rows
        ]
    finally:
        conn.close()


@router.post(
    "/edges/{edge_id}/decision",
    response_model=RelationshipEdgeSchema,
    summary="Record investigator decision (ACCEPT/REJECT) on a candidate edge",
)
async def record_edge_decision(
    edge_id: str,
    req: EdgeDecisionRequest = Body(...),
) -> RelationshipEdgeSchema:
    """Investigator accepts or rejects a relationship edge."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM candidate_edges WHERE id = ?", (edge_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Edge not found: {edge_id}")

        conn.execute(
            "UPDATE candidate_edges SET decision = ?, decision_rationale = ? WHERE id = ?",
            (req.decision, req.rationale, edge_id),
        )
        conn.commit()

        updated = conn.execute("SELECT * FROM candidate_edges WHERE id = ?", (edge_id,)).fetchone()
        return RelationshipEdgeSchema(
            id=updated["id"],
            evidence_id=updated["evidence_id"],
            source_fragment_id=updated["source_fragment_id"],
            target_fragment_id=updated["target_fragment_id"],
            composite_confidence=updated["composite_confidence"],
            factors=EdgeEvidenceFactorsSchema(
                signature_match=updated["signature_match"],
                offset_continuity=updated["offset_continuity"],
                structural_validity=updated["structural_validity"],
                entropy_compatibility=updated["entropy_compatibility"],
                contradiction_count=updated["contradiction_count"],
            ),
            decision=updated["decision"],
            decision_rationale=updated["decision_rationale"],
            evidence_strings=json.loads(updated["evidence_strings_json"] or "[]"),
        )
    finally:
        conn.close()
