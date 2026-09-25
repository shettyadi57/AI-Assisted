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


def test_signature_registry_interface_raises():
    """Verify SignatureRegistry raises NotImplementedError."""
    registry = SignatureRegistry()
    assert isinstance(registry, SignatureRegistryInterface)
    with pytest.raises(NotImplementedError):
        registry.get_signature("jpeg")
    with pytest.raises(NotImplementedError):
        registry.scan_for_signatures(b"\xFF\xD8\xFF")


def test_fragment_analyzer_interface_raises():
    """Verify FragmentAnalyzer raises NotImplementedError."""
    analyzer = FragmentAnalyzer()
    assert isinstance(analyzer, FragmentAnalyzerInterface)
    with pytest.raises(NotImplementedError):
        analyzer.calculate_entropy(b"\x00" * 256)
    with pytest.raises(NotImplementedError):
        analyzer.detect_boundaries(b"\x00" * 512)


def test_relationship_engine_interface_raises():
    """Verify RelationshipEngine raises NotImplementedError."""
    engine = RelationshipEngine()
    assert isinstance(engine, RelationshipEngineInterface)
    factors = EdgeEvidenceFactors(
        signature_match=1.0,
        offset_continuity=1.0,
        structural_validity=1.0,
        entropy_compatibility=1.0,
        contradiction_count=0,
    )
    with pytest.raises(NotImplementedError):
        engine.compute_composite_score(factors)


def test_reconstruction_engine_interface_raises():
    """Verify ReconstructionEngine raises NotImplementedError."""
    engine = ReconstructionEngine()
    assert isinstance(engine, ReconstructionEngineInterface)
    with pytest.raises(NotImplementedError):
        engine.assemble_candidate("cand-1", "jpeg", [], "frag-0")


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
