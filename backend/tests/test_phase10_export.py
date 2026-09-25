"""
Unit & Integration Tests for Phase 10: Provenance, Export & Forensic Evidence Report
"""

import hashlib
import io
import json
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.config import PROJECT_ROOT
from backend.database import apply_migrations, get_db_connection
from backend.main import app
from core.reconstruction_engine import (
    ProvenanceByteSpan,
    find_provenance_span_for_offset,
)


@pytest.fixture(scope="module")
def client():
    apply_migrations()
    with TestClient(app) as c:
        yield c


def test_provenance_byte_span_lookup():
    """Verify bit-level provenance query accurately locates byte offsets."""
    spans = [
        ProvenanceByteSpan(
            output_offset=0,
            output_end_offset=4095,
            length_bytes=4096,
            source_fragment_id="frag_01",
            original_evidence_offset=8192,
            sha256_hash="abcd1234",
            validation_status="CONFIRMED",
            note="Seq #1",
        ),
        ProvenanceByteSpan(
            output_offset=4096,
            output_end_offset=8191,
            length_bytes=4096,
            source_fragment_id="frag_02",
            original_evidence_offset=12288,
            sha256_hash="ef015678",
            validation_status="CONFIRMED",
            note="Seq #2",
        ),
    ]

    span_start = find_provenance_span_for_offset(spans, 0)
    assert span_start is not None
    assert span_start.source_fragment_id == "frag_01"
    assert span_start.original_evidence_offset == 8192

    span_mid = find_provenance_span_for_offset(spans, 4095)
    assert span_mid is not None
    assert span_mid.source_fragment_id == "frag_01"

    span_next = find_provenance_span_for_offset(spans, 4096)
    assert span_next is not None
    assert span_next.source_fragment_id == "frag_02"
    assert span_next.original_evidence_offset == 12288

    span_out_of_bounds = find_provenance_span_for_offset(spans, 99999)
    assert span_out_of_bounds is None


def test_phase10_pipeline_e2e_export_and_report(client):
    """
    Execute full pipeline on sample dataset and verify Phase 10:
    - Provenance endpoint
    - HTML and JSON Evidence Reports
    - Forensic Bundle ZIP export
    - Cryptographic verification of artifact SHA-256 against report/manifest
    """
    # 1. Ingest sample dataset
    ingest_res = client.post("/api/v1/discovery/sample")
    assert ingest_res.status_code in (200, 201)
    ev_id = ingest_res.json()["id"]

    # 2. Carve fragments
    frag_res = client.post("/api/v1/analysis/fragments", json={"evidence_id": ev_id, "force_reanalyze": True})
    assert frag_res.status_code == 200

    # 3. Generate candidate chains
    cand_gen = client.post("/api/v1/reconstruction/candidates", json={"evidence_id": ev_id})
    assert cand_gen.status_code == 200
    candidates = cand_gen.json()
    assert len(candidates) > 0

    # Pick the PDF candidate
    pdf_cand = next((c for c in candidates if c["target_format"].lower() == "pdf"), candidates[0])
    cid = pdf_cand["id"]

    # 4. Assemble candidate to disk
    assemble_res = client.post(f"/api/v1/reconstruction/candidates/{cid}/assemble")
    assert assemble_res.status_code == 200
    assembled = assemble_res.json()
    assert assembled["status"] == "ACCEPTED"
    assert assembled["reconstruction_sha256"] is not None
    art_path = Path(assembled["artifact_path"])
    assert art_path.exists()

    actual_file_bytes = art_path.read_bytes()
    actual_file_sha256 = hashlib.sha256(actual_file_bytes).hexdigest()
    assert actual_file_sha256 == assembled["reconstruction_sha256"]

    # 5. Test Provenance Endpoint
    prov_res = client.get(f"/api/v1/reconstruction/candidates/{cid}/provenance")
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert len(prov_data["spans"]) > 0

    # Test Provenance Offset Query
    prov_query_res = client.get(f"/api/v1/reconstruction/candidates/{cid}/provenance?offset=0")
    assert prov_query_res.status_code == 200
    q_data = prov_query_res.json()
    assert q_data["found"] is True
    assert q_data["span"]["output_start"] == 0

    # 6. Test Evidence Report (JSON format)
    report_json_res = client.get(f"/api/v1/reconstruction/candidates/{cid}/report?format=json")
    assert report_json_res.status_code == 200
    rep_json = report_json_res.json()
    assert rep_json["candidate_summary"]["reconstruction_sha256"] == actual_file_sha256
    assert rep_json["evidence_metadata"]["filename"] == "loose-fragment-soup.bin"
    assert len(rep_json["provenance_spans"]) == len(prov_data["spans"])

    # 7. Test Evidence Report (HTML format)
    report_html_res = client.get(f"/api/v1/reconstruction/candidates/{cid}/report?format=html")
    assert report_html_res.status_code == 200
    assert "text/html" in report_html_res.headers["content-type"]
    html_text = report_html_res.text
    assert "FORENSIC EVIDENCE REPORT" in html_text
    assert actual_file_sha256 in html_text
    assert "Bit-Level Provenance Mapping" in html_text

    # 8. Test Forensic Bundle ZIP Export
    bundle_res = client.get(f"/api/v1/reconstruction/candidates/{cid}/bundle")
    assert bundle_res.status_code == 200
    assert "application/zip" in bundle_res.headers["content-type"]
    bundle_sha_header = bundle_res.headers.get("X-Export-SHA256")

    bundle_bytes = bundle_res.content
    calc_bundle_sha = hashlib.sha256(bundle_bytes).hexdigest()
    assert bundle_sha_header == calc_bundle_sha

    # Unpack and verify bundle contents
    with zipfile.ZipFile(io.BytesIO(bundle_bytes), "r") as z:
        names = z.namelist()
        assert art_path.name in names
        assert "manifest.json" in names
        assert "provenance_map.json" in names
        assert "audit_trail.json" in names
        assert "EVIDENCE_REPORT.html" in names

        # Verify manifest content
        manifest_raw = json.loads(z.read("manifest.json").decode())
        assert manifest_raw["candidate"]["reconstruction_sha256"] == actual_file_sha256
        assert manifest_raw["tool_version"] == "reconstruct-v0.5.0-alpha"

        # Verify extracted artifact file inside zip matches original byte for byte
        extracted_artifact = z.read(art_path.name)
        assert hashlib.sha256(extracted_artifact).hexdigest() == actual_file_sha256

    # 9. Verify database export record
    conn = get_db_connection()
    try:
        rec = conn.execute("SELECT * FROM export_records WHERE candidate_id = ?", (cid,)).fetchone()
        assert rec is not None
        assert rec["export_sha256"] == calc_bundle_sha
    finally:
        conn.close()
