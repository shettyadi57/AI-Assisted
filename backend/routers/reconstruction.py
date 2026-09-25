"""
Reconstruction Stage Router — Phase 4 & Phase 5 LIVE

Endpoints:
- POST /api/v1/reconstruction/candidates         — Generate ranked candidates from graph traversal
- GET  /api/v1/reconstruction/candidates         — List candidates (filter by evidence_id)
- GET  /api/v1/reconstruction/candidates/{id}    — Get candidate details with fragment chain & gaps
- POST /api/v1/reconstruction/candidates/{id}/assemble — Execute reassembly to disk with gap tracking
- GET  /api/v1/reconstruction/candidates/{id}/artifact — Download reconstructed artifact file
"""

import base64
import hashlib
import io
import json
import logging
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Query, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from backend.config import PROJECT_ROOT
from backend.database import get_db_connection
from backend.reporting import generate_html_report, generate_report_data
from backend.schemas import (
    CandidateFragmentItem,
    CandidateListResponse,
    CandidateRecord,
    GapItem,
    GenerateCandidatesRequest,
    ProvenanceQueryResponse,
    ProvenanceResponse,
    ProvenanceSpanRecord,
    ReassembleRequest,
)
from core.fragment_analyzer import FragmentMetadata, ForensicStatus
from core.reconstruction_engine import default_reconstruction_engine
from core.relationship_engine import default_relationship_engine, CandidateChain, GapInfo

logger = logging.getLogger("reconstruct.reconstruction")
router = APIRouter(prefix="/reconstruction", tags=["Pipeline Stage: Reconstruction"])

ARTIFACTS_DIR = PROJECT_ROOT / "derived-artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


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


def _row_to_candidate_record(cand_row, conn) -> CandidateRecord:
    cid = cand_row["id"]
    cf_rows = conn.execute(
        """SELECT cf.*, f.offset_start, f.size_bytes, f.sha256_hash, f.status,
                  f.inferred_format, f.role_guess
           FROM candidate_fragments cf
           JOIN fragments f ON cf.fragment_id = f.id
           WHERE cf.candidate_id = ?
           ORDER BY cf.sequence_order""",
        (cid,),
    ).fetchall()

    frags = [
        CandidateFragmentItem(
            fragment_id=r["fragment_id"],
            sequence_order=r["sequence_order"],
            offset_start=r["offset_start"],
            size_bytes=r["size_bytes"],
            sha256_hash=r["sha256_hash"],
            status=r["status"],
            inferred_format=r["inferred_format"],
            role_guess=r["role_guess"] or "UNKNOWN",
            edge_confidence=r["edge_confidence"],
            edge_signals=json.loads(r["edge_signals_json"] or "{}") if r["edge_signals_json"] else None,
            decision=r["decision"],
            decision_rationale=r["decision_rationale"],
        )
        for r in cf_rows
    ]

    gaps_raw = json.loads(cand_row["gaps_json"] or "[]")
    gaps = [
        GapItem(
            after_sequence_order=g.get("after_sequence_order", 0),
            offset_expected=g.get("offset_expected", 0),
            estimated_size_bytes=g.get("estimated_size_bytes", 0),
            description=g.get("description", ""),
            filler_type=g.get("filler_type", "zero_fill"),
        )
        for g in gaps_raw
    ]

    keys = cand_row.keys() if hasattr(cand_row, "keys") else []
    recovery_status = cand_row["recovery_status"] if "recovery_status" in keys and cand_row["recovery_status"] else cand_row["status"]

    return CandidateRecord(
        id=cid,
        name=cand_row["name"],
        target_format=cand_row["target_format"],
        evidence_id=cand_row["evidence_id"],
        total_size_bytes=cand_row["total_size_bytes"],
        fragment_count=cand_row["fragment_count"],
        recovered_fragments=cand_row["recovered_fragments"] or len(frags),
        missing_fragments=cand_row["missing_fragments"] or len(gaps),
        duplicate_fragments=cand_row["duplicate_fragments"] or 0,
        corrupted_fragments=cand_row["corrupted_fragments"] or 0,
        reconstructed_bytes=cand_row["reconstructed_bytes"] or cand_row["total_size_bytes"],
        missing_bytes=cand_row["missing_bytes"] or 0,
        coverage_pct=cand_row["coverage_pct"] or 0.0,
        composite_confidence=cand_row["composite_confidence"] or 0.0,
        status=cand_row["status"],
        recovery_status=recovery_status,
        reconstruction_sha256=cand_row["reconstruction_sha256"],
        artifact_path=cand_row["artifact_path"],
        is_finalized=bool(cand_row["is_finalized"]),
        evidence_strings=json.loads(cand_row["evidence_strings_json"] or "[]"),
        gaps=gaps,
        fragments=frags,
        provenance=json.loads(cand_row["provenance_json"] or "[]") if "provenance_json" in keys else [],
        created_at=cand_row["created_at"],
        updated_at=cand_row["updated_at"],
    )


# ─── POST /candidates — generate & persist candidates ────────────────────────

@router.post(
    "/candidates",
    response_model=list[CandidateRecord],
    status_code=status.HTTP_200_OK,
    summary="Generate ranked reconstruction candidates from relationship graph",
)
async def generate_candidates(req: GenerateCandidatesRequest = Body(...)) -> list[CandidateRecord]:
    """
    Traverse the fragment relationship graph to generate ranked candidate chains.
    Persists candidates and ordered candidate fragments to SQLite.
    """
    conn = get_db_connection()
    try:
        ev_row = conn.execute("SELECT * FROM evidence WHERE id = ?", (req.evidence_id,)).fetchone()
        if not ev_row:
            raise HTTPException(status_code=404, detail=f"Evidence not found: {req.evidence_id}")

        ev_path = _resolve_evidence_path(ev_row["filepath"])
        raw_bytes = ev_path.read_bytes()

        frag_rows = conn.execute(
            "SELECT * FROM fragments WHERE evidence_id = ? ORDER BY offset_start",
            (req.evidence_id,),
        ).fetchall()
        if not frag_rows:
            raise HTTPException(status_code=400, detail="No fragments found. Run analysis first.")

        metas = [_row_to_meta(r) for r in frag_rows]
        bytes_map = {m.fragment_id: raw_bytes[m.offset_start : m.offset_end] for m in metas}

        chains: list[CandidateChain] = default_relationship_engine.generate_candidate_chains(
            fragments=metas,
            fragment_bytes_map=bytes_map,
            evidence_id=req.evidence_id,
            target_format=req.target_format,
        )

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        for chain in chains:
            gaps_data = [
                {
                    "after_sequence_order": g.after_sequence_order,
                    "offset_expected": g.offset_expected,
                    "estimated_size_bytes": g.estimated_size_bytes,
                    "description": g.description,
                    "filler_type": g.filler_type,
                }
                for g in chain.gaps
            ]

            conn.execute(
                """INSERT OR REPLACE INTO candidates
                   (id, name, target_format, evidence_id, total_size_bytes,
                    fragment_count, composite_confidence, status, recovery_status,
                    recovered_fragments, missing_fragments, duplicate_fragments,
                    corrupted_fragments, reconstructed_bytes, missing_bytes,
                    coverage_pct, gaps_json, evidence_strings_json,
                    is_finalized, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING_REVIEW', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                (
                    chain.candidate_id,
                    chain.name,
                    chain.target_format,
                    req.evidence_id,
                    chain.total_size_bytes,
                    len(chain.ordered_fragment_ids),
                    chain.composite_confidence,
                    chain.status,
                    chain.recovered_fragments,
                    chain.missing_fragments,
                    chain.duplicate_fragments,
                    chain.corrupted_fragments,
                    chain.reconstructed_bytes,
                    chain.missing_bytes,
                    chain.coverage_pct,
                    json.dumps(gaps_data),
                    json.dumps(chain.evidence_strings),
                    now,
                    now,
                ),
            )

            # Insert candidate fragments
            conn.execute("DELETE FROM candidate_fragments WHERE candidate_id = ?", (chain.candidate_id,))
            for seq, fid in enumerate(chain.ordered_fragment_ids, start=1):
                conn.execute(
                    """INSERT OR REPLACE INTO candidate_fragments
                       (candidate_id, fragment_id, sequence_order, edge_confidence,
                        edge_signals_json, decision, created_at, updated_at)
                       VALUES (?, ?, ?, ?, '{}', 'PENDING', ?, ?)""",
                    (
                        chain.candidate_id,
                        fid,
                        seq,
                        chain.composite_confidence,
                        now,
                        now,
                    ),
                )

        conn.commit()

        # Retrieve full populated candidate records
        res_rows = conn.execute(
            "SELECT * FROM candidates WHERE evidence_id = ? ORDER BY composite_confidence DESC",
            (req.evidence_id,),
        ).fetchall()
        return [_row_to_candidate_record(r, conn) for r in res_rows]
    finally:
        conn.close()


# ─── GET /candidates — list candidates ───────────────────────────────────────

@router.get(
    "/candidates",
    response_model=CandidateListResponse,
    summary="List all reconstruction candidates",
)
async def list_candidates(
    evidence_id: str | None = Query(default=None),
    target_format: str | None = Query(default=None),
) -> CandidateListResponse:
    """Retrieve reconstruction candidates with filter options."""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM candidates WHERE 1=1"
        params: list[str] = []
        if evidence_id:
            query += " AND evidence_id = ?"
            params.append(evidence_id)
        if target_format:
            query += " AND target_format = ?"
            params.append(target_format)
        query += " ORDER BY composite_confidence DESC"

        rows = conn.execute(query, tuple(params)).fetchall()
        cands = [_row_to_candidate_record(r, conn) for r in rows]
        return CandidateListResponse(total=len(cands), candidates=cands)
    finally:
        conn.close()


# ─── GET /candidates/{id} — single candidate ─────────────────────────────────

@router.get(
    "/candidates/{candidate_id}",
    response_model=CandidateRecord,
    summary="Get candidate reconstruction details with fragment chain and gaps",
)
async def get_candidate(candidate_id: str) -> CandidateRecord:
    """Retrieve full candidate details."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Candidate not found: {candidate_id}")
        return _row_to_candidate_record(row, conn)
    finally:
        conn.close()


# ─── POST /candidates/{id}/assemble — reassemble to disk (Phase 5) ───────────

@router.post(
    "/candidates/{candidate_id}/assemble",
    response_model=CandidateRecord,
    summary="Assemble candidate into real output file on disk with explicit gap tracking",
)
async def assemble_candidate_endpoint(
    candidate_id: str,
    req: ReassembleRequest = Body(default_factory=ReassembleRequest),
) -> CandidateRecord:
    """
    Executes Phase 5 reassembly: writes candidate to disk in derived-artifacts,
    computes real SHA-256, tracks synthetic gap regions, and updates SQLite.
    """
    conn = get_db_connection()
    try:
        cand_row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not cand_row:
            raise HTTPException(status_code=404, detail=f"Candidate not found: {candidate_id}")

        ev_id = cand_row["evidence_id"]
        ev_row = conn.execute("SELECT * FROM evidence WHERE id = ?", (ev_id,)).fetchone()
        if not ev_row:
            raise HTTPException(status_code=404, detail="Associated evidence record not found")

        ev_path = _resolve_evidence_path(ev_row["filepath"])
        raw_bytes = ev_path.read_bytes()

        # Get candidate fragments
        cf_rows = conn.execute(
            """SELECT f.*, cf.sequence_order, cf.edge_confidence, cf.decision
               FROM candidate_fragments cf
               JOIN fragments f ON cf.fragment_id = f.id
               WHERE cf.candidate_id = ?
               ORDER BY cf.sequence_order""",
            (candidate_id,),
        ).fetchall()

        ordered_metas = [_row_to_meta(r) for r in cf_rows]
        ordered_ids = [m.fragment_id for m in ordered_metas]
        bytes_map = {m.fragment_id: raw_bytes[m.offset_start : m.offset_end] for m in ordered_metas}

        gaps_raw = json.loads(cand_row["gaps_json"] or "[]")
        gaps = [
            GapInfo(
                after_sequence_order=g["after_sequence_order"],
                offset_expected=g["offset_expected"],
                estimated_size_bytes=g["estimated_size_bytes"],
                description=g["description"],
                filler_type=req.filler_type,
            )
            for g in gaps_raw
        ]

        chain = CandidateChain(
            candidate_id=candidate_id,
            name=cand_row["name"],
            target_format=cand_row["target_format"],
            ordered_fragment_ids=ordered_ids,
            ordered_fragments=ordered_metas,
            composite_confidence=cand_row["composite_confidence"],
            total_size_bytes=cand_row["total_size_bytes"],
            recovered_fragments=cand_row["recovered_fragments"],
            missing_fragments=cand_row["missing_fragments"],
            duplicate_fragments=cand_row["duplicate_fragments"],
            corrupted_fragments=cand_row["corrupted_fragments"],
            reconstructed_bytes=cand_row["reconstructed_bytes"],
            missing_bytes=cand_row["missing_bytes"],
            coverage_pct=cand_row["coverage_pct"],
            gaps=gaps,
            evidence_strings=json.loads(cand_row["evidence_strings_json"] or "[]"),
            status=cand_row["status"],
        )

        # Run Phase 5 Reassembly
        reassembly = default_reconstruction_engine.reassemble_to_disk(
            chain=chain,
            fragment_store=bytes_map,
            output_dir=ARTIFACTS_DIR,
            filler_type=req.filler_type,
        )

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        prov_data = [p.to_dict() for p in reassembly.provenance_map]
        prov_json = json.dumps(prov_data)

        conn.execute(
            """UPDATE candidates
               SET status = 'ACCEPTED', recovery_status = ?, reconstruction_sha256 = ?,
                   artifact_path = ?, reconstructed_bytes = ?, provenance_json = ?, is_finalized = 1, updated_at = ?
               WHERE id = ?""",
            (
                reassembly.status,
                reassembly.reconstructed_sha256,
                reassembly.artifact_path,
                reassembly.real_data_bytes,
                prov_json,
                now,
                candidate_id,
            ),
        )

        # Record event in immutable forensic audit log (Spec Section 20)
        audit_id = str(uuid.uuid4())
        audit_payload = f"CANDIDATE_ASSEMBLED:{candidate_id}:{reassembly.reconstructed_sha256}:{now}"
        audit_hash = hashlib.sha256(audit_payload.encode()).hexdigest()
        conn.execute(
            """INSERT INTO audit_log
               (id, event_type, entity_type, entity_id, investigator_id, action_detail, entry_hash)
               VALUES (?, 'CANDIDATE_ASSEMBLED', 'candidate', ?, 'investigator', ?, ?)""",
            (
                audit_id,
                candidate_id,
                f"Assembled candidate {candidate_id} ({reassembly.status}, {reassembly.total_output_bytes} bytes, SHA-256: {reassembly.reconstructed_sha256})",
                audit_hash,
            ),
        )
        conn.commit()

        updated_cand_row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        return _row_to_candidate_record(updated_cand_row, conn)
    finally:
        conn.close()


# ─── GET /candidates/{id}/artifact — download artifact ───────────────────────

@router.get(
    "/candidates/{candidate_id}/artifact",
    summary="Download reconstructed file artifact from disk",
)
async def download_artifact(candidate_id: str):
    """Download the reconstructed artifact file."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT artifact_path, target_format FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    finally:
        conn.close()

    if not row or not row["artifact_path"]:
        raise HTTPException(status_code=404, detail="Artifact not assembled yet. Run reassembly first.")

    p = Path(row["artifact_path"])
    if not p.exists():
        raise HTTPException(status_code=404, detail="Artifact file missing on disk")

    ext = row["target_format"].lower()
    return FileResponse(
        path=str(p),
        filename=p.name,
        media_type=f"application/{ext}",
    )


# ─── GET /candidates/{id}/provenance — Phase 10 Bit-Level Mapping ────────────

@router.get(
    "/candidates/{candidate_id}/provenance",
    summary="Query bit-level provenance byte-map for reconstructed candidate",
)
async def get_candidate_provenance(
    candidate_id: str,
    offset: int | None = Query(None, description="Optional byte offset to query specific provenance span"),
):
    """
    Returns the complete provenance byte-map linking output byte spans
    to original source fragments and file offsets (Spec Section 19).
    """
    conn = get_db_connection()
    try:
        cand_row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not cand_row:
            raise HTTPException(status_code=404, detail="Candidate not found")
        keys = cand_row.keys() if hasattr(cand_row, "keys") else []
        prov_list = json.loads(cand_row["provenance_json"] or "[]") if "provenance_json" in keys else []
        total_bytes = cand_row["reconstructed_bytes"] or cand_row["total_size_bytes"] or 0
    finally:
        conn.close()

    if offset is not None:
        for span in prov_list:
            s_start = span.get("output_start", 0)
            s_end = span.get("output_end", 0)
            if s_start <= offset <= s_end:
                return {
                    "candidate_id": candidate_id,
                    "query_offset": offset,
                    "found": True,
                    "span": span,
                }
        return {
            "candidate_id": candidate_id,
            "query_offset": offset,
            "found": False,
            "span": None,
        }

    return {
        "candidate_id": candidate_id,
        "total_bytes": total_bytes,
        "spans": prov_list,
    }


# ─── GET /candidates/{id}/report — Phase 10 Forensic Evidence Report ─────────

@router.get(
    "/candidates/{candidate_id}/report",
    summary="Generate NIST FIPS compliant Forensic Evidence Report (HTML or JSON)",
)
async def get_candidate_report(
    candidate_id: str,
    format: str = Query("html", description="Output format: 'html' or 'json'"),
):
    """
    Generate a complete, publication-grade Forensic Evidence Report for the candidate.
    Includes evidence metadata, hashes, full provenance timeline, gap analysis,
    and immutable chain of custody audit history (Spec Sections 19 & 20).
    """
    conn = get_db_connection()
    try:
        cand_row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not cand_row:
            raise HTTPException(status_code=404, detail="Candidate not found")
        ev_row = conn.execute("SELECT * FROM evidence WHERE id = ?", (cand_row["evidence_id"],)).fetchone()
        if not ev_row:
            raise HTTPException(status_code=404, detail="Evidence record not found")

        cf_rows = conn.execute(
            """SELECT cf.*, f.offset_start, f.offset_end, f.size_bytes, f.sha256_hash,
                      f.status, f.inferred_format, f.role_guess, f.entropy
               FROM candidate_fragments cf
               JOIN fragments f ON cf.fragment_id = f.id
               WHERE cf.candidate_id = ?
               ORDER BY cf.sequence_order""",
            (candidate_id,),
        ).fetchall()

        audit_rows = conn.execute(
            "SELECT * FROM audit_log WHERE entity_id IN (?, ?) ORDER BY created_at ASC",
            (candidate_id, cand_row["evidence_id"]),
        ).fetchall()

        keys = cand_row.keys() if hasattr(cand_row, "keys") else []
        prov_list = json.loads(cand_row["provenance_json"] or "[]") if "provenance_json" in keys else []
    finally:
        conn.close()

    report_dict = generate_report_data(
        candidate=dict(cand_row),
        evidence=dict(ev_row),
        candidate_fragments=[dict(r) for r in cf_rows],
        provenance_spans=prov_list,
        audit_entries=[dict(a) for a in audit_rows],
    )

    if format.lower() == "json":
        return JSONResponse(content=report_dict)

    html_content = generate_html_report(report_dict)
    return HTMLResponse(content=html_content)


# ─── GET /candidates/{id}/bundle — Phase 10 Forensic Export Bundle ───────────

@router.get(
    "/candidates/{candidate_id}/bundle",
    summary="Export complete forensic bundle ZIP (Artifact + Manifest + Provenance + Audit + Report)",
)
async def export_forensic_bundle(candidate_id: str):
    """
    Package and export candidate as a verifiable forensic bundle ZIP.
    Contains reconstructed file, manifest.json, provenance_map.json, audit_trail.json,
    and self-contained EVIDENCE_REPORT.html.
    """
    conn = get_db_connection()
    try:
        cand_row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not cand_row:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not cand_row["artifact_path"] or not Path(cand_row["artifact_path"]).exists():
            raise HTTPException(status_code=400, detail="Candidate not yet assembled. Run assembly first.")

        ev_row = conn.execute("SELECT * FROM evidence WHERE id = ?", (cand_row["evidence_id"],)).fetchone()
        cf_rows = conn.execute(
            """SELECT cf.*, f.offset_start, f.offset_end, f.size_bytes, f.sha256_hash,
                      f.status, f.inferred_format, f.role_guess, f.entropy
               FROM candidate_fragments cf
               JOIN fragments f ON cf.fragment_id = f.id
               WHERE cf.candidate_id = ?
               ORDER BY cf.sequence_order""",
            (candidate_id,),
        ).fetchall()

        audit_rows = conn.execute(
            "SELECT * FROM audit_log WHERE entity_id IN (?, ?) ORDER BY created_at ASC",
            (candidate_id, cand_row["evidence_id"]),
        ).fetchall()

        keys = cand_row.keys() if hasattr(cand_row, "keys") else []
        prov_list = json.loads(cand_row["provenance_json"] or "[]") if "provenance_json" in keys else []
    finally:
        conn.close()

    artifact_path = Path(cand_row["artifact_path"])
    artifact_data = artifact_path.read_bytes()

    # Generate full report data & HTML report
    report_dict = generate_report_data(
        candidate=dict(cand_row),
        evidence=dict(ev_row),
        candidate_fragments=[dict(r) for r in cf_rows],
        provenance_spans=prov_list,
        audit_entries=[dict(a) for a in audit_rows],
    )
    html_report = generate_html_report(report_dict)

    manifest = {
        "forensic_bundle_version": "1.0",
        "tool_version": "reconstruct-v0.5.0-alpha",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence": dict(ev_row),
        "candidate": {
            "id": cand_row["id"],
            "name": cand_row["name"],
            "target_format": cand_row["target_format"],
            "recovery_status": cand_row["recovery_status"],
            "composite_confidence": cand_row["composite_confidence"],
            "coverage_pct": cand_row["coverage_pct"],
            "total_size_bytes": cand_row["total_size_bytes"],
            "reconstruction_sha256": cand_row["reconstruction_sha256"],
        },
        "fragment_sequence": [dict(r) for r in cf_rows],
        "gaps": json.loads(cand_row["gaps_json"] or "[]"),
        "reconstruction_config": {
            "scorer": "deterministic",
            "classifier": "signature",
            "gap_handling": "zero_fill",
        },
    }

    # Construct ZIP archive in-memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(artifact_path.name, artifact_data)
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("provenance_map.json", json.dumps(prov_list, indent=2))
        zf.writestr("audit_trail.json", json.dumps([dict(a) for a in audit_rows], indent=2))
        zf.writestr("EVIDENCE_REPORT.html", html_report)

    bundle_bytes = zip_buffer.getvalue()
    bundle_sha256 = hashlib.sha256(bundle_bytes).hexdigest()

    # Save bundle to derived-artifacts
    bundle_path = ARTIFACTS_DIR / f"{candidate_id}_forensic_bundle.zip"
    bundle_path.write_bytes(bundle_bytes)

    # Record export in database
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    export_id = str(uuid.uuid4())
    conn = get_db_connection()
    try:
        conn.execute(
            """INSERT INTO export_records
               (id, candidate_id, evidence_id, export_type, export_filename,
                export_path, export_sha256, size_bytes, tool_version, config_json, created_at)
               VALUES (?, ?, ?, 'BUNDLE_ZIP', ?, ?, ?, ?, 'reconstruct-v0.5.0-alpha', '{}', ?)""",
            (
                export_id,
                candidate_id,
                cand_row["evidence_id"],
                bundle_path.name,
                str(bundle_path),
                bundle_sha256,
                len(bundle_bytes),
                now,
            ),
        )
        audit_id = str(uuid.uuid4())
        audit_payload = f"BUNDLE_EXPORTED:{export_id}:{bundle_sha256}:{now}"
        audit_hash = hashlib.sha256(audit_payload.encode()).hexdigest()
        conn.execute(
            """INSERT INTO audit_log
               (id, event_type, entity_type, entity_id, investigator_id, action_detail, entry_hash)
               VALUES (?, 'BUNDLE_EXPORTED', 'candidate', ?, 'investigator', ?, ?)""",
            (
                audit_id,
                candidate_id,
                f"Exported forensic bundle {bundle_path.name} (SHA-256: {bundle_sha256})",
                audit_hash,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return FileResponse(
        path=str(bundle_path),
        filename=bundle_path.name,
        media_type="application/zip",
        headers={"X-Export-SHA256": bundle_sha256},
    )


# ─── GET /candidates/{id}/preview — Phase 10 Artifact Preview ────────────────

@router.get(
    "/candidates/{candidate_id}/preview",
    summary="Get preview representation of the reconstructed candidate",
)
async def get_candidate_preview(candidate_id: str):
    """
    Return base64 / binary preview representation of the reconstructed artifact.
    """
    conn = get_db_connection()
    try:
        cand_row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not cand_row:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not cand_row["artifact_path"]:
            raise HTTPException(status_code=400, detail="Candidate not yet assembled.")
    finally:
        conn.close()

    p = Path(cand_row["artifact_path"])
    if not p.exists():
        raise HTTPException(status_code=404, detail="Artifact file missing on disk")

    ext = cand_row["target_format"].lower()
    data = p.read_bytes()
    sz = len(data)

    is_image = ext in ("jpeg", "jpg", "png", "gif")
    is_pdf = ext == "pdf"

    head_hex = data[:64].hex(" ").upper()
    tail_hex = data[-64:].hex(" ").upper() if sz > 64 else ""

    b64_data = ""
    if is_image and sz < 5 * 1024 * 1024:
        mime = f"image/{'jpeg' if ext in ('jpeg', 'jpg') else ext}"
        b64_data = f"data:{mime};base64," + base64.b64encode(data).decode()
    elif is_pdf and sz < 5 * 1024 * 1024:
        b64_data = f"data:application/pdf;base64," + base64.b64encode(data).decode()

    return {
        "candidate_id": candidate_id,
        "filename": p.name,
        "format": cand_row["target_format"],
        "size_bytes": sz,
        "is_image": is_image,
        "is_pdf": is_pdf,
        "data_url": b64_data,
        "head_hex_preview": head_hex,
        "tail_hex_preview": tail_hex,
    }
