"""
Tests for Phase 9: ML Extension Point Architecture
"""

import os
import pytest
from core.ml.config import get_scorer_config, get_classifier_config
from core.ml.feature_extractor import (
    FeatureExtractor,
    compute_shannon_entropy,
    compute_ascii_printable_ratio,
    compute_byte_frequency_histogram,
    compute_histogram_l1_distance,
    default_feature_extractor,
)
from core.ml.fragment_classifier import (
    FragmentClassifierInterface,
    SignatureBasedClassifier,
    ONNXFragmentClassifier,
    get_fragment_classifier,
)
from core.ml.relationship_scorer import (
    RelationshipScorerInterface,
    DeterministicRelationshipScorer,
    ONNXRelationshipScorer,
    get_relationship_scorer,
)


def test_feature_extractor_math():
    """Verify numeric feature extraction produces real mathematical numbers."""
    data_zero = b"\x00" * 100
    entropy_zero = compute_shannon_entropy(data_zero)
    assert entropy_zero == 0.0

    data_random = bytes(range(256))
    entropy_uniform = compute_shannon_entropy(data_random)
    assert 7.99 <= entropy_uniform <= 8.0

    ascii_text = b"Hello, World!\r\n"
    assert compute_ascii_printable_ratio(ascii_text) == 1.0

    hist_a = compute_byte_frequency_histogram(b"\x00" * 10)
    hist_b = compute_byte_frequency_histogram(b"\xFF" * 10)
    l1_dist = compute_histogram_l1_distance(hist_a, hist_b)
    assert l1_dist == 2.0  # Completely disjoint histograms have L1 distance 2.0


def test_feature_extractor_pair_vector():
    """Verify pair feature extraction produces full float vectors."""
    extractor = FeatureExtractor()
    frag_a = {
        "entropy": 4.5,
        "offset_start": 0,
        "size_bytes": 4096,
        "inferred_format": "PDF",
        "role_guess": "FILE_START",
        "signature_confidence": 0.95,
    }
    frag_b = {
        "entropy": 5.0,
        "offset_start": 4096,
        "size_bytes": 4096,
        "inferred_format": "PDF",
        "role_guess": "CONTINUATION",
        "signature_confidence": 0.50,
    }

    bytes_a = b"%PDF-1.4 " + (b"A" * 4087)
    bytes_b = b"B" * 4096

    vec = extractor.extract_pair_features(frag_a, frag_b, bytes_a, bytes_b)
    assert len(vec.features) == len(extractor.FEATURE_NAMES)
    assert all(isinstance(x, float) for x in vec.features)
    assert vec.feature_dict["format_match_flag"] == 1.0
    assert vec.feature_dict["role_compatibility_score"] == 1.0
    assert vec.feature_dict["source_is_file_start"] == 1.0


def test_deterministic_relationship_scorer_interface():
    """Verify DeterministicRelationshipScorer implements the interface."""
    scorer = DeterministicRelationshipScorer()
    assert isinstance(scorer, RelationshipScorerInterface)
    assert scorer.is_model_loaded() is True

    frag_a = {
        "id": "fa1",
        "entropy": 3.5,
        "offset_start": 0,
        "size_bytes": 4096,
        "inferred_format": "PDF",
        "role_guess": "FILE_START",
        "signature_confidence": 0.95,
    }
    frag_b = {
        "id": "fa2",
        "entropy": 4.0,
        "offset_start": 4096,
        "size_bytes": 4096,
        "inferred_format": "PDF",
        "role_guess": "CONTINUATION",
        "signature_confidence": 0.50,
    }

    result = scorer.score(frag_a, frag_b, b"%PDF-1.4...", b"stream...", context={"target_format": "PDF"})
    assert result.scorer_type == "deterministic"
    assert 0.0 <= result.score <= 1.0
    assert "signature_match" in result.confidence_breakdown
    assert len(result.feature_vector) == len(FeatureExtractor.FEATURE_NAMES)


def test_signature_based_classifier_interface():
    """Verify SignatureBasedClassifier implements the interface."""
    classifier = SignatureBasedClassifier()
    assert isinstance(classifier, FragmentClassifierInterface)
    assert classifier.is_model_loaded() is True

    pdf_bytes = b"%PDF-1.4 %binary stream"
    res = classifier.classify(pdf_bytes, offset=0)
    assert res.classifier_type == "signature"
    assert res.inferred_format == "PDF"
    assert res.role_guess == "FILE_START"
    assert res.confidence >= 0.85
    assert res.matched_magic_hex is not None


def test_onnx_scorer_raises_honest_error():
    """Verify ONNXRelationshipScorer raises honest Phase 9 exception."""
    with pytest.raises(RuntimeError, match="ONNX scoring not yet available — Phase 9 ships the interface only"):
        ONNXRelationshipScorer()

    with pytest.raises(RuntimeError, match="ONNX classification not yet available — Phase 9 ships the interface only"):
        ONNXFragmentClassifier()


def test_scorer_factories():
    """Verify factory returns deterministic scorer by default and respects configuration."""
    scorer = get_relationship_scorer("deterministic")
    assert isinstance(scorer, DeterministicRelationshipScorer)

    classifier = get_fragment_classifier("signature")
    assert isinstance(classifier, SignatureBasedClassifier)

    with pytest.raises(RuntimeError):
        get_relationship_scorer("onnx")

    with pytest.raises(RuntimeError):
        get_fragment_classifier("onnx")
