"""
Analysis Stage Router — Phase 2 LIVE: Fragment Discovery

Real endpoints:
  POST /api/v1/analysis/fragments        — Analyze evidence, persist fragments
  GET  /api/v1/analysis/fragments        — List all fragments (optionally filter by evidence_id)
  GET  /api/v1/analysis/fragments/{id}  — Get single fragment with full hex preview

The router calls core.fragment_analyzer.FragmentAnalyzer (pure Python, no web deps).
Evidence file must already be registered via the discovery routes.
For sample_dataset evidence: reads the file from the filesystem path.
For client-upload evidence: reads from the recorded filepath (or 404 with clear message).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Query, status

from backend.config import PROJECT_ROOT
from backend.database import get_db_connection
from backend.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    FragmentListResponse,
    FragmentRecord,
    PhaseNotImplementedResponse,
    SignatureDefinitionRecord,
)
from core.fragment_analyzer import FragmentAnalyzer, FragmentMetadata, ForensicStatus
from core.signature_registry import BUILTIN_SIGNATURES, default_signature_registry

logger = logging.getLogger("reconstruct.analysis")
router = APIRouter(prefix="/analysis", tags=["Pipeline Stage: Analysis"])


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _meta_to_record(m: FragmentMetadata, created_at: str, updated_at: str) -> FragmentRecord:
    return FragmentRecord(
        id=m.fragment_id,
        evidence_id=m.evidence_id,
        offset_start=m.offset_start,
        offset_end=m.offset_end,
        size_bytes=m.size_bytes,
        sha256_hash=m.sha256_hash,
        entropy=m.entropy,
        status=m.status.value,
        entropy_class=m.entropy_class,
        content_class=m.content_class,
        hex_preview=m.hex_preview,
        flags=m.flags,
        inferred_format=m.inferred_format,
        role_guess=m.role_guess,
        signature_confidence=m.signature_confidence,
        matched_magic_hex=m.matched_magic_hex,
        matched_magic_offset=m.matched_magic_offset,
        matched_magic_length=m.matched_magic_length,
        structural_notes=m.structural_notes,
        created_at=created_at,
        updated_at=updated_at,
    )


def _row_to_record(row) -> FragmentRecord:
    # Safe column access for backwards compatibility
    keys = row.keys() if hasattr(row, "keys") else []
    return FragmentRecord(
        id=row["id"],
        evidence_id=row["evidence_id"],
        offset_start=row["offset_start"],
        offset_end=row["offset_end"],
        size_bytes=row["size_bytes"],
        sha256_hash=row["sha256_hash"],
        entropy=row["entropy"] or 0.0,
        status=row["status"],
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
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _resolve_evidence_path(filepath: str) -> Path:
    """
    Resolve the filesystem path for an evidence file.
    Handles both absolute paths (sample dataset) and client-upload stubs.
    """
    p = Path(filepath)
    if p.is_absolute() and p.exists():
        return p
    # Try relative to project root
    rel = PROJECT_ROOT / filepath
    if rel.exists():
        return rel
    raise FileNotFoundError(
        f"Evidence file not found at '{filepath}'. "
        "For client uploads, the file must be accessible on the backend filesystem."
    )


# ─── POST /fragments — analyze evidence and persist fragments ─────────────────

@router.post(
    "/fragments",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze evidence: split into fragments, compute entropy, detect duplicates",
)
async def analyze_fragments(req: AnalyzeRequest = Body(...)) -> AnalyzeResponse:
    """
    Run Phase 2 fragment analysis on a registered evidence record.

    - Reads the evidence file from the backend filesystem.
    - Splits into block_size chunks (configurable, default 4096).
    - Computes SHA-256, Shannon entropy, preliminary structural class per fragment.
    - Detects exact-duplicate fragments by content hash.
    - Persists all fragments to the SQLite `fragments` table.
    - Returns the full fragment list with all computed metadata.

    Phase 3 note: `inferred_format` is always null — file-type signature
    detection is out of scope for Phase 2.
    """
    conn = get_db_connection()
    try:
        # ── Look up the evidence record ────────────────────────────────────
        ev_row = conn.execute(
            "SELECT * FROM evidence WHERE id = ?", (req.evidence_id,)
        ).fetchone()
        if not ev_row:
            raise HTTPException(status_code=404, detail=f"Evidence not found: {req.evidence_id}")

        # ── Resolve file ───────────────────────────────────────────────────
        try:
            file_path = _resolve_evidence_path(ev_row["filepath"])
        except FileNotFoundError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # ── Optionally purge existing fragments ────────────────────────────
        existing_count = conn.execute(
            "SELECT COUNT(*) FROM fragments WHERE evidence_id = ?", (req.evidence_id,)
        ).fetchone()[0]

        if existing_count > 0 and not req.force_reanalyze:
            # Return existing results from DB rather than re-analyzing
            rows = conn.execute(
                "SELECT * FROM fragments WHERE evidence_id = ? ORDER BY offset_start",
                (req.evidence_id,),
            ).fetchall()
            frags = [_row_to_record(r) for r in rows]
            dup_count = sum(1 for f in frags if f.status == "DUPLICATE")
            return AnalyzeResponse(
                evidence_id=req.evidence_id,
                evidence_filename=ev_row["filename"],
                fragment_count=len(frags),
                duplicate_count=dup_count,
                block_size_used=req.block_size,
                fragments=frags,
            )

        if req.force_reanalyze and existing_count > 0:
            conn.execute(
                "DELETE FROM fragments WHERE evidence_id = ?", (req.evidence_id,)
            )
            conn.commit()
            logger.info("force_reanalyze=True: deleted %d existing fragments for %s", existing_count, req.evidence_id)

        # ── Read file & analyze ────────────────────────────────────────────
        raw_bytes = file_path.read_bytes()
        logger.info(
            "Analyzing evidence id=%s file=%s size=%d bytes block_size=%d",
            req.evidence_id, file_path.name, len(raw_bytes), req.block_size,
        )

        analyzer = FragmentAnalyzer(block_size=req.block_size)
        fragment_metas: list[FragmentMetadata] = list(
            analyzer.analyze_blob(raw_bytes, req.evidence_id)
        )

        # ── Persist to SQLite ──────────────────────────────────────────────
        import sqlite3
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        records: list[FragmentRecord] = []

        for meta in fragment_metas:
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO fragments
                       (id, evidence_id, offset_start, offset_end, size_bytes,
                        sha256_hash, entropy, status, inferred_format,
                        hex_preview, entropy_class, content_class, flags_json,
                        role_guess, signature_confidence, matched_magic_hex,
                        matched_magic_offset, matched_magic_length, structural_notes,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        meta.fragment_id,
                        meta.evidence_id,
                        meta.offset_start,
                        meta.offset_end,
                        meta.size_bytes,
                        meta.sha256_hash,
                        meta.entropy,
                        meta.status.value,
                        meta.inferred_format,
                        meta.hex_preview,
                        meta.entropy_class,
                        meta.content_class,
                        json.dumps(meta.flags),
                        meta.role_guess,
                        meta.signature_confidence,
                        meta.matched_magic_hex,
                        meta.matched_magic_offset,
                        meta.matched_magic_length,
                        meta.structural_notes,
                        now,
                        now,
                    ),
                )
                records.append(_meta_to_record(meta, now, now))
            except sqlite3.IntegrityError as e:
                logger.warning("Fragment insert skipped (integrity): %s — %s", meta.fragment_id, e)

        conn.commit()

        # ── Update evidence status ─────────────────────────────────────────
        conn.execute(
            "UPDATE evidence SET status = 'PROCESSED', updated_at = ? WHERE id = ?",
            (now, req.evidence_id),
        )
        conn.commit()

        dup_count = sum(1 for f in records if f.status == "DUPLICATE")
        logger.info(
            "Analysis complete: evidence=%s fragments=%d duplicates=%d",
            req.evidence_id, len(records), dup_count,
        )
        return AnalyzeResponse(
            evidence_id=req.evidence_id,
            evidence_filename=ev_row["filename"],
            fragment_count=len(records),
            duplicate_count=dup_count,
            block_size_used=req.block_size,
            fragments=records,
        )
    finally:
        conn.close()


# ─── GET /fragments — list fragments ─────────────────────────────────────────

@router.get(
    "/fragments",
    response_model=FragmentListResponse,
    summary="List fragments (filter by evidence_id)",
)
async def list_fragments(
    evidence_id: str | None = Query(default=None, description="Filter by evidence record UUID"),
    limit: int = Query(default=500, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> FragmentListResponse:
    conn = get_db_connection()
    try:
        if evidence_id:
            rows = conn.execute(
                "SELECT * FROM fragments WHERE evidence_id = ? ORDER BY offset_start LIMIT ? OFFSET ?",
                (evidence_id, limit, offset),
            ).fetchall()
            total = conn.execute(
                "SELECT COUNT(*) FROM fragments WHERE evidence_id = ?", (evidence_id,)
            ).fetchone()[0]
        else:
            rows = conn.execute(
                "SELECT * FROM fragments ORDER BY evidence_id, offset_start LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM fragments").fetchone()[0]
    finally:
        conn.close()

    return FragmentListResponse(
        evidence_id=evidence_id or "*",
        total=total,
        fragments=[_row_to_record(r) for r in rows],
    )


# ─── GET /fragments/{id} — single fragment ────────────────────────────────────

@router.get(
    "/fragments/{fragment_id}",
    response_model=FragmentRecord,
    summary="Get single fragment by ID",
)
async def get_fragment(fragment_id: str) -> FragmentRecord:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM fragments WHERE id = ?", (fragment_id,)
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Fragment not found: {fragment_id}")
    return _row_to_record(row)


# ─── GET /fragments/{id}/hex — full hex dump ──────────────────────────────────

@router.get(
    "/fragments/{fragment_id}/hex",
    summary="Get full hex dump of a fragment (reads from evidence file)",
    responses={
        422: {"description": "Evidence file not accessible"},
        404: {"description": "Fragment not found"},
    },
)
async def get_fragment_hex(
    fragment_id: str,
    max_bytes: int = Query(default=4096, ge=16, le=65536),
) -> dict:
    """
    Return a full hex dump of the fragment's bytes for the Hex Inspector panel.
    Reads the specified byte range from the evidence file directly — no cached copy.
    """
    conn = get_db_connection()
    try:
        frag_row = conn.execute(
            "SELECT f.*, e.filepath, e.filename as ev_filename "
            "FROM fragments f JOIN evidence e ON f.evidence_id = e.id "
            "WHERE f.id = ?",
            (fragment_id,),
        ).fetchone()
    finally:
        conn.close()

    if not frag_row:
        raise HTTPException(status_code=404, detail=f"Fragment not found: {fragment_id}")

    try:
        file_path = _resolve_evidence_path(frag_row["filepath"])
    except FileNotFoundError as e:
        raise HTTPException(status_code=422, detail=str(e))

    offset_start = frag_row["offset_start"]
    size = frag_row["size_bytes"]
    read_size = min(size, max_bytes)

    with open(file_path, "rb") as f:
        f.seek(offset_start)
        raw = f.read(read_size)

    # Build hex rows: 16 bytes per row, hex + ASCII side-by-side
    rows = []
    for i in range(0, len(raw), 16):
        chunk = raw[i : i + 16]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in chunk)
        rows.append({
            "offset": offset_start + i,
            "offset_hex": f"0x{offset_start + i:08X}",
            "hex": hex_part,
            "ascii": ascii_part,
        })

    keys = frag_row.keys() if hasattr(frag_row, "keys") else []
    return {
        "fragment_id": fragment_id,
        "evidence_filename": frag_row["ev_filename"],
        "offset_start": offset_start,
        "size_bytes": size,
        "bytes_returned": len(raw),
        "truncated": len(raw) < size,
        "rows": rows,
        "inferred_format": frag_row["inferred_format"] if "inferred_format" in keys else None,
        "role_guess": frag_row["role_guess"] if "role_guess" in keys else "UNKNOWN",
        "signature_confidence": frag_row["signature_confidence"] if "signature_confidence" in keys else 0.0,
        "matched_magic_hex": frag_row["matched_magic_hex"] if "matched_magic_hex" in keys else None,
        "matched_magic_offset": frag_row["matched_magic_offset"] if "matched_magic_offset" in keys else 0,
        "matched_magic_length": frag_row["matched_magic_length"] if "matched_magic_length" in keys else 0,
        "structural_notes": frag_row["structural_notes"] if "structural_notes" in keys else "",
    }


# ─── GET /signatures — list supported signatures ─────────────────────────────

@router.get(
    "/signatures",
    response_model=list[SignatureDefinitionRecord],
    summary="List all supported file format signature definitions",
)
async def list_signatures() -> list[SignatureDefinitionRecord]:
    """Return all registered format signatures and expected structural specifications."""
    return [
        SignatureDefinitionRecord(
            format_id=sig.format_id,
            name=sig.name,
            extension=sig.extension,
            category=sig.category.value,
            magic_hex=sig.header_magic.hex().upper(),
            header_offset=sig.header_offset,
            trailer_hex=sig.trailer_magic.hex().upper() if sig.trailer_magic else None,
            description=sig.description,
            expected_structural_notes=sig.expected_structural_notes,
            typical_entropy_range=list(sig.typical_entropy_range),
            confidence_base=sig.confidence_base,
        )
        for sig in BUILTIN_SIGNATURES
    ]
