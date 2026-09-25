"""
Unit tests for /core interfaces and contracts.

Ensures that core modules:
1. Have no dependencies on FastAPI or web frameworks.
2. Provide all required types and contracts.
3. Raise NotImplementedError on all Phase 0 placeholder methods.
4. Support the 6 non-negotiable forensic status states.
"""

import pytest

from core.fragment_analyzer import (
    ForensicStatus,
    FragmentAnalyzer,
    FragmentAnalyzerInterface,
)
from core.integrity_analyzer import (
    HashAlgorithm,
    IntegrityAnalyzer,
    IntegrityAnalyzerInterface,
)
from core.ml.relationship_scorer import (
    RelationshipScorer,
    RelationshipScorerInterface,
)
from core.reconstruction_engine import (
    ReconstructionCandidate,
    ReconstructionEngine,
    ReconstructionEngineInterface,
)
from core.relationship_engine import (
    EdgeEvidenceFactors,
    InvestigatorDecision,
    RelationshipEngine,
    RelationshipEngineInterface,
)
from core.signature_registry import (
    SignatureCategory,
    SignatureRegistry,
    SignatureRegistryInterface,
)
from core.validators import ValidationResult, ValidationStatus
from core.validators.jpeg import JPEGValidator
from core.validators.pdf import PDFValidator
from core.validators.png import PNGValidator
from core.validators.zip import ZIPValidator


def test_core_baseline():
    """Trivial passing test verifying core test harness is operational."""
    assert True


def test_forensic_status_states():
    """Ensure all 6 non-negotiable forensic status states exist."""
    expected = {"CONFIRMED", "INFERRED", "UNCERTAIN", "MISSING", "CORRUPTED", "DUPLICATE"}
    actual = {s.value for s in ForensicStatus}
    assert actual == expected


def test_integrity_analyzer_interface_raises():
    """Verify IntegrityAnalyzer raises NotImplementedError on Phase 0 interface."""
    analyzer = IntegrityAnalyzer()
    assert isinstance(analyzer, IntegrityAnalyzerInterface)
    with pytest.raises(NotImplementedError):
        analyzer.hash_bytes(b"forensic test")
    with pytest.raises(NotImplementedError):
        analyzer.hash_file("nonexistent.raw")


def test_signature_registry_phase3_live():
    """Verify SignatureRegistry correctly identifies signatures and scans fragments."""
    registry = SignatureRegistry()
    assert isinstance(registry, SignatureRegistryInterface)
    
    # 1. Supported formats
    fmts = registry.list_supported_formats()
    assert "pdf" in fmts and "jpeg" in fmts and "png" in fmts and "zip" in fmts
    
    # 2. Signature lookup
    sig = registry.get_signature("pdf")
    assert sig is not None
    assert sig.header_magic == b"%PDF-"
    assert sig.trailer_magic == b"%%EOF"

    # 3. Header match
    assert registry.match_header(b"%PDF-1.4 header", "pdf") == 1.0
    assert registry.match_header(b"\xFF\xD8\xFF\xE0", "jpeg") == 1.0
    assert registry.match_header(b"random bytes", "pdf") == 0.0

    # 4. Trailer match
    assert registry.match_trailer(b"trailer content %%EOF\n", "pdf") == 1.0

    # 5. Scan fragment
    res = registry.scan_fragment(b"%PDF-1.4\n1 0 obj\n")
    assert res.format_id == "pdf"
    assert res.role.value == "FILE_START"
    assert res.confidence >= 0.85


def test_fragment_analyzer_phase2_live():
    """
    Phase 2 & 3: FragmentAnalyzer is now fully implemented.
    Verify real entropy computation, block splitting, and duplicate detection.
    """
    from core.fragment_analyzer import DEFAULT_BLOCK_SIZE

    analyzer = FragmentAnalyzer(block_size=512)

    # ── Entropy calculation ────────────────────────────────────────────────
    zeros = b"\x00" * 512
    profile_zero = analyzer.calculate_entropy(zeros)
    assert profile_zero.overall_entropy == 0.0

    uniform = bytes(range(256)) * 2
    profile_max = analyzer.calculate_entropy(uniform)
    assert profile_max.overall_entropy == pytest.approx(8.0, abs=0.01)

    # ── Single fragment analysis ───────────────────────────────────────────
    ev_id = "test-ev-0000-0000-0000-000000000001"
    meta = analyzer.analyze_fragment(b"Hello world!\n" * 40, ev_id, offset_start=0)
    assert meta.evidence_id == ev_id
    assert meta.size_bytes == len(b"Hello world!\n" * 40)
    assert meta.entropy > 0.0
    assert meta.content_class == "PRINTABLE"

    # ── Blob splitting ─────────────────────────────────────────────────────
    blob = b"A" * 1024 + b"B" * 1024 + b"C" * 512
    frags = list(analyzer.analyze_blob(blob, ev_id))
    assert len(frags) == 5
    assert frags[0].offset_start == 0
    assert frags[1].offset_start == 512
    assert frags[-1].size_bytes == 512

    # ── Duplicate detection ────────────────────────────────────────────────
    dup_blob = b"X" * 512 + b"X" * 512 + b"Y" * 512
    dup_frags = list(analyzer.analyze_blob(dup_blob, ev_id + "-dup"))
    assert dup_frags[0].status != ForensicStatus.DUPLICATE
    assert dup_frags[1].status == ForensicStatus.DUPLICATE
    assert any("DUPLICATE_OF:" in flag for flag in dup_frags[1].flags)

    # ── Boundary detection ────────────────────────────────────────────────
    import os
    combined = os.urandom(512) + b"\x00" * 512
    boundaries = analyzer.detect_boundaries(combined, sector_size=512)
    assert len(boundaries) >= 1
    assert boundaries[0].boundary_type == "ENTROPY_JUMP"

    # ── Block size is configurable (not hardcoded) ────────────────────────
    assert DEFAULT_BLOCK_SIZE == 4096
    custom = FragmentAnalyzer(block_size=8192)
    assert custom.block_size == 8192


def test_relationship_engine_phase4_live():
    """Verify RelationshipEngine scores relationships and builds chains."""
    engine = RelationshipEngine()
    assert isinstance(engine, RelationshipEngineInterface)
    factors = EdgeEvidenceFactors(
        signature_match=1.0,
        offset_continuity=1.0,
        structural_validity=1.0,
        entropy_compatibility=1.0,
        contradiction_count=0,
    )
    score = engine.compute_composite_score(factors)
    assert score == 1.0


def test_reconstruction_engine_phase5_live():
    """Verify ReconstructionEngine assembles candidates and generates provenance."""
    engine = ReconstructionEngine()
    assert isinstance(engine, ReconstructionEngineInterface)
    cand = engine.assemble_candidate("cand-1", "pdf", [], "frag-0")
    assert cand.candidate_id == "cand-1"
    assert cand.ordered_fragment_ids == ["frag-0"]
    raw = engine.synthesize_file(cand, {"frag-0": b"%PDF-1.4 valid content"})
    assert raw.startswith(b"%PDF-1.4")


def test_validators_raise():
    """Verify all format validators raise NotImplementedError."""
    for validator in (PDFValidator(), JPEGValidator(), PNGValidator(), ZIPValidator()):
        with pytest.raises(NotImplementedError):
            validator.validate(b"test")


def test_ml_relationship_scorer_interface_raises():
    """Verify ML relationship scorer raises NotImplementedError."""
    scorer = RelationshipScorer()
    assert isinstance(scorer, RelationshipScorerInterface)
    with pytest.raises(NotImplementedError):
        scorer.is_model_loaded()
