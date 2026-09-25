"""
ML Feature Extraction Module (Phase 9 — Spec Section 12 & 21)

Extracts numeric feature vectors from adjacent fragment pairs and individual
fragments suitable for consumption by an ML / ONNX model.

All calculations are real mathematical transforms of actual fragment data:
- Shannon entropy of head and tail slices
- Boundary byte transition distances and L1 byte frequency histogram divergence
- Physical and logical offset deltas
- Role compatibility and signature confidence signals
- Format consistency and printable ASCII ratios
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True)
class PairFeatureVector:
    """Extracted numeric feature vector for a pair of candidate adjacent fragments."""
    features: list[float]
    feature_names: list[str]
    feature_dict: dict[str, float]

    def as_vector(self) -> list[float]:
        """Return the flat numeric feature vector."""
        return list(self.features)


def compute_shannon_entropy(data: bytes) -> float:
    """Compute Shannon entropy [0.0 - 8.0] for a byte slice."""
    if not data:
        return 0.0
    length = len(data)
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    entropy = 0.0
    for count in counts:
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def compute_byte_frequency_histogram(data: bytes) -> list[float]:
    """Compute normalized 256-bin byte frequency distribution."""
    if not data:
        return [0.0] * 256
    counts = [0.0] * 256
    for b in data:
        counts[b] += 1.0
    length = float(len(data))
    return [c / length for c in counts]


def compute_histogram_l1_distance(hist_a: Sequence[float], hist_b: Sequence[float]) -> float:
    """Compute L1 total variation distance between two 256-bin histograms [0.0 - 2.0]."""
    return round(sum(abs(a - b) for a, b in zip(hist_a, hist_b)), 4)


def compute_ascii_printable_ratio(data: bytes) -> float:
    """Return fraction of bytes that are printable ASCII (0x20..0x7E, plus \r, \n, \t)."""
    if not data:
        return 0.0
    printable_count = sum(1 for b in data if (0x20 <= b <= 0x7E) or b in (0x09, 0x0A, 0x0D))
    return round(printable_count / len(data), 4)


class FeatureExtractor:
    """
    Extracts dense numeric feature vectors from fragment pairs for ML scoring.
    """

    FEATURE_NAMES: list[str] = [
        "entropy_source",
        "entropy_target",
        "entropy_delta",
        "boundary_byte_diff_norm",
        "boundary_hist_l1_dist",
        "offset_delta_norm",
        "ascii_ratio_source",
        "ascii_ratio_target",
        "ascii_ratio_delta",
        "format_match_flag",
        "role_compatibility_score",
        "source_confidence",
        "target_confidence",
        "source_is_file_start",
        "target_is_possible_end",
        "source_has_eof_marker",
    ]

    def extract_pair_features(
        self,
        source_meta: dict | object,
        target_meta: dict | object,
        source_bytes: bytes,
        target_bytes: bytes,
    ) -> PairFeatureVector:
        """
        Extract numeric feature vector from source and target fragments.
        Supports both FragmentMetadata instances and dictionary records.
        """
        def get_attr(obj: dict | object, key: str, default: float | str | int | None = 0):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # 1. Entropy features
        source_entropy = float(get_attr(source_meta, "entropy", 0.0) or compute_shannon_entropy(source_bytes))
        target_entropy = float(get_attr(target_meta, "entropy", 0.0) or compute_shannon_entropy(target_bytes))
        entropy_delta = round(abs(source_entropy - target_entropy), 4)

        # 2. Boundary byte transition
        last_byte = source_bytes[-1] if len(source_bytes) > 0 else 0
        first_byte = target_bytes[0] if len(target_bytes) > 0 else 0
        boundary_byte_diff_norm = round(abs(int(last_byte) - int(first_byte)) / 255.0, 4)

        # 3. Boundary histogram L1 distance (tail 256 bytes vs head 256 bytes)
        tail_slice = source_bytes[-256:] if len(source_bytes) >= 256 else source_bytes
        head_slice = target_bytes[:256] if len(target_bytes) >= 256 else target_bytes
        hist_a = compute_byte_frequency_histogram(tail_slice)
        hist_b = compute_byte_frequency_histogram(head_slice)
        boundary_hist_l1_dist = compute_histogram_l1_distance(hist_a, hist_b)

        # 4. Offset delta (normalized to 0..1 scale using 1MB ceiling)
        src_start = int(get_attr(source_meta, "offset_start", 0) or 0)
        src_len = int(get_attr(source_meta, "size_bytes", len(source_bytes)) or len(source_bytes))
        tgt_start = int(get_attr(target_meta, "offset_start", 0) or 0)
        offset_gap = max(0, tgt_start - (src_start + src_len))
        offset_delta_norm = round(min(1.0, offset_gap / 1048576.0), 4)

        # 5. Printable ASCII ratios
        ascii_source = compute_ascii_printable_ratio(source_bytes)
        ascii_target = compute_ascii_printable_ratio(target_bytes)
        ascii_delta = round(abs(ascii_source - ascii_target), 4)

        # 6. Format match
        src_fmt = str(get_attr(source_meta, "inferred_format", "UNKNOWN") or "UNKNOWN").upper()
        tgt_fmt = str(get_attr(target_meta, "inferred_format", "UNKNOWN") or "UNKNOWN").upper()
        format_match_flag = 1.0 if (src_fmt != "UNKNOWN" and src_fmt == tgt_fmt) else 0.0

        # 7. Role compatibility score
        src_role = str(get_attr(source_meta, "role_guess", "UNKNOWN") or "UNKNOWN").upper()
        tgt_role = str(get_attr(target_meta, "role_guess", "UNKNOWN") or "UNKNOWN").upper()
        role_comp = 0.5  # Neutral default
        if src_role == "FILE_START" and tgt_role in ("CONTINUATION", "POSSIBLE_END"):
            role_comp = 1.0
        elif src_role == "CONTINUATION" and tgt_role in ("CONTINUATION", "POSSIBLE_END"):
            role_comp = 0.9
        elif src_role == "POSSIBLE_END" and tgt_role in ("FILE_START", "CONTINUATION"):
            role_comp = 0.0  # EOF cannot precede another fragment
        elif tgt_role == "FILE_START":
            role_comp = 0.1  # FILE_START should not be a target of a continuation

        # 8. Signature confidence scores
        source_conf = float(get_attr(source_meta, "signature_confidence", 0.0) or 0.0)
        target_conf = float(get_attr(target_meta, "signature_confidence", 0.0) or 0.0)

        # 9. Role flags
        source_is_file_start = 1.0 if src_role == "FILE_START" else 0.0
        target_is_possible_end = 1.0 if tgt_role == "POSSIBLE_END" else 0.0

        # 10. Source EOF marker presence
        source_has_eof_marker = 1.0 if src_role == "POSSIBLE_END" else 0.0

        feature_dict = {
            "entropy_source": source_entropy,
            "entropy_target": target_entropy,
            "entropy_delta": entropy_delta,
            "boundary_byte_diff_norm": boundary_byte_diff_norm,
            "boundary_hist_l1_dist": boundary_hist_l1_dist,
            "offset_delta_norm": offset_delta_norm,
            "ascii_ratio_source": ascii_source,
            "ascii_ratio_target": ascii_target,
            "ascii_ratio_delta": ascii_delta,
            "format_match_flag": format_match_flag,
            "role_compatibility_score": role_comp,
            "source_confidence": source_conf,
            "target_confidence": target_conf,
            "source_is_file_start": source_is_file_start,
            "target_is_possible_end": target_is_possible_end,
            "source_has_eof_marker": source_has_eof_marker,
        }

        features = [feature_dict[name] for name in self.FEATURE_NAMES]

        return PairFeatureVector(
            features=features,
            feature_names=list(self.FEATURE_NAMES),
            feature_dict=feature_dict,
        )


default_feature_extractor = FeatureExtractor()
