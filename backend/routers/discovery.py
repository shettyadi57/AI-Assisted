"""
Discovery Stage Router — Phase 1 LIVE: Evidence Ingest & Registry

Real endpoints:
  POST /api/v1/discovery/ingest  — Register an evidence file (client-computed SHA-256)
  GET  /api/v1/discovery/evidence — List all evidence records
  POST /api/v1/discovery/sample   — Load the built-in sample dataset (loose-fragment-soup)
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse

from backend.database import get_db_connection
from backend.schemas import (
    EvidenceIngestRequest,
    EvidenceListResponse,
    EvidenceRecord,
    PhaseNotImplementedResponse,
)
from backend.config import PROJECT_ROOT

logger = logging.getLogger("reconstruct.discovery")
router = APIRouter(prefix="/discovery", tags=["Pipeline Stage: Discovery"])

SAMPLE_SOUP = PROJECT_ROOT / "sample-data" / "loose-fragment-soup.bin"
SAMPLE_MANIFEST = PROJECT_ROOT / "sample-data" / "manifest.json"

VALID_SOURCE_TYPES = {
    "raw_disk_image",
    "forensic_image",
    "binary_fragment_files",
    "extracted_block_files",
    "zip_of_fragments",
    "sample_dataset",
}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _row_to_record(row) -> EvidenceRecord:
    meta = json.loads(row["metadata_json"] or "{}")
    return EvidenceRecord(
        id=row["id"],
        filename=row["filename"],
        file_size_bytes=row["file_size_bytes"],
        sha256_hash=row["sha256_hash"],
        md5_hash=row["md5_hash"],
        source_type=meta.get("source_type", "unknown"),
        status=row["status"],
        is_sample_dataset=meta.get("is_sample_dataset", False),
        disclaimer=(
            "Sample dataset — not real evidence. Not legally admissible."
            if meta.get("is_sample_dataset") else
            "Evidence is read-only. Not legally admissible."
        ),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post(
    "/ingest",
    response_model=EvidenceRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Register evidence file (client-computed SHA-256)",
)
async def ingest_evidence(req: EvidenceIngestRequest = Body(...)) -> EvidenceRecord:
    """
    Register evidence with a client-supplied SHA-256.
    Evidence is treated as read-only immediately upon registration.
    """
    if req.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid source_type '{req.source_type}'. "
                   f"Valid: {sorted(VALID_SOURCE_TYPES)}",
        )

    evidence_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    meta = json.dumps(
        {
            "source_type": req.source_type,
            "is_sample_dataset": req.is_sample_dataset,
        }
    )

    conn = get_db_connection()
    try:
        conn.execute(
            """INSERT INTO evidence
               (id, filename, filepath, file_size_bytes, sha256_hash,
                status, metadata_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'INGESTED', ?, ?, ?)""",
            (
                evidence_id,
                req.filename,
                f"client-upload/{req.filename}",
                req.file_size_bytes,
                req.sha256_hash,
                meta,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM evidence WHERE id = ?", (evidence_id,)
        ).fetchone()
    finally:
        conn.close()

    return _row_to_record(row)


@router.post(
    "/sample",
    response_model=EvidenceRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Load built-in sample dataset (loose-fragment-soup)",
)
async def load_sample_dataset() -> EvidenceRecord:
    """
    Register the built-in synthetic sample dataset.
    The SHA-256 is computed by the backend from the actual file bytes.
    Marked is_sample_dataset=True in all responses — never shown as real evidence.
    """
    if not SAMPLE_SOUP.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "Sample dataset not found. "
                "Run `python sample-data/generate.py` to generate it."
            ),
        )

    logger.info("Computing SHA-256 of sample dataset: %s", SAMPLE_SOUP)
    sha256 = _sha256_file(SAMPLE_SOUP)
    md5 = _md5_file(SAMPLE_SOUP)
    size = SAMPLE_SOUP.stat().st_size
    filename = "loose-fragment-soup.bin"

    # Check if already registered (idempotent on same hash)
    conn = get_db_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM evidence WHERE sha256_hash = ?", (sha256,)
        ).fetchone()
        if existing:
            logger.info("Sample dataset already registered: %s", existing["id"])
            return _row_to_record(existing)

        evidence_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        meta = json.dumps(
            {
                "source_type": "sample_dataset",
                "is_sample_dataset": True,
                "generate_script": "sample-data/generate.py",
                "seed": 42,
                "block_size": 4096,
            }
        )
        conn.execute(
            """INSERT INTO evidence
               (id, filename, filepath, file_size_bytes, sha256_hash, md5_hash,
                status, metadata_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'INGESTED', ?, ?, ?)""",
            (
                evidence_id,
                filename,
                str(SAMPLE_SOUP),
                size,
                sha256,
                md5,
                meta,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM evidence WHERE id = ?", (evidence_id,)
        ).fetchone()
    finally:
        conn.close()

    logger.info("Sample dataset registered: id=%s sha256=%s…", evidence_id, sha256[:16])
    return _row_to_record(row)


@router.get(
    "/evidence",
    response_model=EvidenceListResponse,
    summary="List all registered evidence",
)
async def list_evidence() -> EvidenceListResponse:
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM evidence ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()

    items = [_row_to_record(r) for r in rows]
    return EvidenceListResponse(total=len(items), items=items)


@router.delete(
    "/evidence/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an evidence record (does not delete the file)",
)
async def delete_evidence(evidence_id: str) -> None:
    conn = get_db_connection()
    try:
        result = conn.execute(
            "DELETE FROM evidence WHERE id = ?", (evidence_id,)
        )
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Evidence record not found")
    finally:
        conn.close()
