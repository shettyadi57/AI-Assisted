"""Phase 0 unit tests — the only modules with full implementations."""

from __future__ import annotations

import io
import hashlib
import pytest
from pathlib import Path

# ─── integrity.py tests ────────────────────────────────────────────────────
from analysis.integrity import hash_bytes, hash_file, hash_stream, verify_file


def test_hash_bytes_known_value():
    data = b"hello world"
    expected = hashlib.sha256(data).hexdigest()
    assert hash_bytes(data) == expected


def test_hash_bytes_empty():
    assert hash_bytes(b"") == hashlib.sha256(b"").hexdigest()


def test_hash_stream():
    data = b"fragment data"
    stream = io.BytesIO(data)
    assert hash_stream(stream) == hashlib.sha256(data).hexdigest()


def test_hash_file(tmp_path: Path):
    f = tmp_path / "sample.bin"
    f.write_bytes(b"test evidence bytes")
    assert hash_file(f) == hashlib.sha256(b"test evidence bytes").hexdigest()


def test_hash_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        hash_file(tmp_path / "nonexistent.bin")


def test_verify_file_ok(tmp_path: Path):
    f = tmp_path / "ok.bin"
    f.write_bytes(b"ok")
    assert verify_file(f, hashlib.sha256(b"ok").hexdigest()) is True


def test_verify_file_tampered(tmp_path: Path):
    f = tmp_path / "tampered.bin"
    f.write_bytes(b"modified")
    assert verify_file(f, hashlib.sha256(b"original").hexdigest()) is False


# ─── signature_registry.py tests ───────────────────────────────────────────
from analysis.signature_registry import (
    SIGNATURE_REGISTRY,
    get_signature,
    scan_for_signatures,
    header_match_score,
)


def test_registry_non_empty():
    assert len(SIGNATURE_REGISTRY) >= 16


def test_get_known_signature():
    sig = get_signature("jpeg")
    assert sig is not None
    assert sig.header_magic == b"\xFF\xD8\xFF"


def test_get_unknown_signature():
    assert get_signature("does_not_exist") is None


def test_scan_finds_jpeg():
    jpeg_start = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
    hits = scan_for_signatures(jpeg_start + b"\x00" * 100)
    assert any(sig.format_id == "jpeg" for _, sig in hits)


def test_scan_finds_png():
    png_start = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    hits = scan_for_signatures(png_start)
    assert any(sig.format_id == "png" for _, sig in hits)


def test_scan_finds_sqlite():
    sqlite_start = b"SQLite format 3\x00" + b"\x00" * 50
    hits = scan_for_signatures(sqlite_start)
    assert any(sig.format_id == "sqlite3" for _, sig in hits)


def test_scan_empty_data():
    assert scan_for_signatures(b"") == []


def test_header_match_score_full():
    sig = get_signature("jpeg")
    data = b"\xFF\xD8\xFF\xE0some more bytes"
    assert header_match_score(data, sig) == 1.0


def test_header_match_score_zero():
    sig = get_signature("jpeg")
    data = b"\x00\x00\x00\x00some more bytes"
    assert header_match_score(data, sig) == 0.0


def test_header_match_score_partial():
    sig = get_signature("jpeg")
    # First byte matches, rest doesn't
    data = b"\xFF\x00\x00\x00some more bytes"
    score = header_match_score(data, sig)
    assert 0.0 < score < 1.0


# ─── confidence_analyzer.py tests ──────────────────────────────────────────
from analysis.confidence_analyzer import (
    ConfidenceEvidence,
    compute_composite,
    stub_evidence,
)


def test_compute_composite_all_perfect():
    ev = ConfidenceEvidence(
        sig_header_match=1.0,
        sig_offset_continuity=1.0,
        sig_structural_validity=1.0,
        sig_entropy_profile=1.0,
        sig_contradiction_count=0,
    )
    result = compute_composite(ev)
    assert result.composite_score == pytest.approx(1.0, abs=0.001)
    assert result.evidence_status == "CONFIRMED"


def test_compute_composite_all_zero():
    ev = ConfidenceEvidence(
        sig_header_match=0.0,
        sig_offset_continuity=0.0,
        sig_structural_validity=0.0,
        sig_entropy_profile=0.0,
        sig_contradiction_count=0,
    )
    result = compute_composite(ev)
    assert result.composite_score == pytest.approx(0.0, abs=0.001)
    assert result.evidence_status == "CORRUPTED"


def test_compute_composite_contradiction_penalty():
    ev = ConfidenceEvidence(
        sig_header_match=1.0,
        sig_offset_continuity=1.0,
        sig_structural_validity=1.0,
        sig_entropy_profile=1.0,
        sig_contradiction_count=3,  # 3 × 0.10 = 0.30 penalty
    )
    result = compute_composite(ev)
    assert result.composite_score == pytest.approx(0.70, abs=0.01)
    assert result.evidence_status in ("INFERRED", "UNCERTAIN")


def test_compute_composite_no_signals():
    ev = ConfidenceEvidence()  # all None
    result = compute_composite(ev)
    assert result.composite_score is None
    assert result.evidence_status == "UNCERTAIN"


def test_compute_composite_partial_signals():
    ev = ConfidenceEvidence(
        sig_header_match=1.0,
        sig_offset_continuity=None,  # not computed
        sig_structural_validity=None,
        sig_entropy_profile=None,
    )
    result = compute_composite(ev)
    # Only header_match present → weight redistributed to 1.0
    assert result.composite_score == pytest.approx(1.0, abs=0.001)


def test_stub_evidence_is_uncertain():
    ev = stub_evidence("test stub", coming_in_phase=3)
    assert ev.evidence_status == "UNCERTAIN"
    assert ev.composite_score is None
    assert "Phase 3" in (ev.not_computed_reason or "")


# ─── fragment_analyzer.py — FeatureNotAvailableError test ──────────────────
from analysis.fragment_analyzer import (
    FeatureNotAvailableError,
    FragmentAnalyzer,
    EvidenceReadError,
)


def test_feature_not_available_error():
    err = FeatureNotAvailableError("test feature", 2)
    assert err.coming_in_phase == 2
    assert "Phase 2" in str(err)


def test_fragment_analyzer_missing_file(tmp_path: Path):
    with pytest.raises(EvidenceReadError):
        FragmentAnalyzer(tmp_path / "ghost.bin")


def test_fragment_analyzer_identify_fragments_raises(tmp_path: Path):
    f = tmp_path / "evidence.bin"
    f.write_bytes(b"\xFF\xD8\xFF" + b"\x00" * 100)
    analyzer = FragmentAnalyzer(f)
    with pytest.raises(FeatureNotAvailableError) as exc_info:
        analyzer.identify_fragments()
    assert exc_info.value.coming_in_phase == 2


def test_scan_signatures_only_works(tmp_path: Path):
    """scan_signatures_only() is implemented in Phase 0 and must work now."""
    f = tmp_path / "evidence.bin"
    f.write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 100)
    analyzer = FragmentAnalyzer(f)
    hits = analyzer.scan_signatures_only()
    assert any(fmt_id == "jpeg" for _, fmt_id in hits)
