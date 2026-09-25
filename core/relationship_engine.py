"""
Relationship Engine — Phase 4 LIVE

Evaluates multi-factor candidate relationship scores between carved fragments
to construct a directed, scored fragment relationship graph and generate
ranked candidate file reconstruction chains with explicit gap detection and
supporting evidence strings.

Zero dependencies on FastAPI or web frameworks.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from core.fragment_analyzer import FragmentMetadata, ForensicStatus
from core.signature_registry import default_signature_registry, FragmentRole


# ─── Enums & Data Classes ───────────────────────────────────────────────────

class InvestigatorDecision(str, Enum):
    PENDING  = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class EdgeEvidenceFactors:
    """Decomposed independent signals contributing to relationship confidence."""
    signature_match: float          # [0.0 - 1.0] Format marker consistency
    offset_continuity: float        # [0.0 - 1.0] Physical/logical offset alignment
    structural_validity: float      # [0.0 - 1.0] Format-internal parser validity
    entropy_compatibility: float    # [0.0 - 1.0] Transition smoothness across boundary
    contradiction_count: int = 0    # Number of conflicting markers detected


@dataclass(frozen=True)
class FragmentRelationship:
    """A scored directed edge between two fragments in the candidate graph."""
    source_fragment_id: str
    target_fragment_id: str
    composite_confidence: float
    factors: EdgeEvidenceFactors
    decision: InvestigatorDecision = InvestigatorDecision.PENDING
    decision_rationale: str = ""
    evidence_strings: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


@dataclass
class GapInfo:
    """Represents an explicit gap / missing block in a candidate chain."""
    after_sequence_order: int
    offset_expected: int
    estimated_size_bytes: int
    description: str
    filler_type: str = "zero_fill"


@dataclass
class CandidateChain:
    """An ordered candidate reconstruction sequence generated from the relationship graph."""
    candidate_id: str
    name: str
    target_format: str
    ordered_fragment_ids: list[str]
    ordered_fragments: list[FragmentMetadata]
    composite_confidence: float
    total_size_bytes: int
    recovered_fragments: int
    missing_fragments: int
    duplicate_fragments: int
    corrupted_fragments: int
    reconstructed_bytes: int
    missing_bytes: int
    coverage_pct: float
    gaps: list[GapInfo]
    evidence_strings: list[str]
    status: str = "PENDING_REVIEW"


# ─── Abstract Interface ─────────────────────────────────────────────────────

class RelationshipEngineInterface(ABC):
    """Abstract interface for scoring candidate relationships between fragments."""

    @abstractmethod
    def evaluate_relationship(
        self,
        source_meta: FragmentMetadata,
        target_meta: FragmentMetadata,
        source_bytes: bytes,
        target_bytes: bytes,
        target_format: str | None = None,
    ) -> FragmentRelationship:
        """Score candidate relationship between two fragments across all 5 signals."""
        raise NotImplementedError

    @abstractmethod
    def compute_composite_score(self, factors: EdgeEvidenceFactors) -> float:
        """Compute the weighted composite confidence score from decomposed factors."""
        raise NotImplementedError

    @abstractmethod
    def build_candidate_graph(
        self,
        fragments: Sequence[FragmentMetadata],
        target_format: str | None = None,
        fragment_bytes_map: dict[str, bytes] | None = None,
    ) -> list[FragmentRelationship]:
        """Construct candidate graph edges for a set of fragments."""
        raise NotImplementedError


# ─── Live Relationship Engine Implementation ────────────────────────────────

class RelationshipEngine(RelationshipEngineInterface):
    """
    Evaluates multi-factor edges and builds candidate reconstruction chains.
    """

    # Signal weights (sum to 1.0)
    WEIGHT_SIGNATURE = 0.30
    WEIGHT_STRUCTURE = 0.35
    WEIGHT_CONTINUITY = 0.20
    WEIGHT_ENTROPY = 0.15

    def compute_composite_score(self, factors: EdgeEvidenceFactors) -> float:
        """
        Compute weighted composite score and penalize contradictions.
        """
        raw = (
            factors.signature_match * self.WEIGHT_SIGNATURE
            + factors.structural_validity * self.WEIGHT_STRUCTURE
            + factors.offset_continuity * self.WEIGHT_CONTINUITY
            + factors.entropy_compatibility * self.WEIGHT_ENTROPY
        )
        penalty = factors.contradiction_count * 0.40
        return max(0.0, min(1.0, round(raw - penalty, 4)))

    def evaluate_relationship(
        self,
        source_meta: FragmentMetadata,
        target_meta: FragmentMetadata,
        source_bytes: bytes,
        target_bytes: bytes,
        target_format: str | None = None,
    ) -> FragmentRelationship:
        """
        Evaluate directed relationship from source -> target fragment.
        Generates decomposed 5-signal scores, contradiction count, and
        human-readable evidence strings (spec section 7 format).
        """
        evidence_strings: list[str] = []
        flags: list[str] = []
        contradictions = 0

        # Self-edge or duplicate check
        if source_meta.fragment_id == target_meta.fragment_id:
            contradictions += 2
            flags.append("SELF_EDGE")
            evidence_strings.append("✗ Contradiction: fragment cannot link to itself")
            return FragmentRelationship(
                source_fragment_id=source_meta.fragment_id,
                target_fragment_id=target_meta.fragment_id,
                composite_confidence=0.0,
                factors=EdgeEvidenceFactors(0, 0, 0, 0, contradictions),
                evidence_strings=evidence_strings,
                flags=flags,
            )

        if source_meta.sha256_hash == target_meta.sha256_hash:
            contradictions += 2
            flags.append("DUPLICATE_LINK")
            evidence_strings.append("✗ Contradiction: identical SHA-256 duplicate content")

        fmt = target_format or source_meta.inferred_format or target_meta.inferred_format

        # ── 1. Signature Match Signal [0.0 - 1.0] ───────────────────────────
        s_fmt = source_meta.inferred_format
        t_fmt = target_meta.inferred_format

        if s_fmt and t_fmt:
            if s_fmt == t_fmt:
                sig_score = 1.0
                evidence_strings.append(f"✓ Format compatibility: both fragments identified as {s_fmt.upper()}")
            else:
                sig_score = 0.0
                contradictions += 1
                evidence_strings.append(f"✗ Format contradiction: {s_fmt.upper()} cannot transition into {t_fmt.upper()}")
        elif s_fmt or t_fmt:
            # One has format, other is generic text/stream
            active_fmt = s_fmt or t_fmt
            if target_meta.content_class == "PRINTABLE" or source_meta.content_class == "PRINTABLE":
                sig_score = 0.75
                evidence_strings.append(f"✓ Plausible {active_fmt.upper()} stream/text continuation")
            else:
                sig_score = 0.50
                evidence_strings.append(f"~ Compatible generic continuation for {active_fmt.upper()}")
        else:
            sig_score = 0.30
            evidence_strings.append("~ Unidentified format compatibility")

        # ── 2. Offset Continuity Signal [0.0 - 1.0] ─────────────────────────
        # Physical adjacency in evidence file
        if source_meta.offset_end == target_meta.offset_start:
            offset_score = 1.0
            evidence_strings.append(
                f"✓ Direct physical offset adjacency: 0x{source_meta.offset_start:06X} "
                f"({source_meta.size_bytes}B) -> 0x{target_meta.offset_start:06X}"
            )
        elif target_meta.offset_start > source_meta.offset_end:
            gap_bytes = target_meta.offset_start - source_meta.offset_end
            if gap_bytes <= 16384:
                offset_score = 0.70
                evidence_strings.append(f"~ Plausible forward offset sequence (gap: {gap_bytes} bytes)")
            else:
                offset_score = 0.40
                evidence_strings.append(f"⚠ Non-adjacent offset jump (+{gap_bytes} bytes)")
        else:
            # Backward jump (out-of-order in evidence image, e.g. fragment soup)
            offset_score = 0.35
            evidence_strings.append(
                f"~ Non-linear fragment transition (soup order: 0x{source_meta.offset_start:06X} -> 0x{target_meta.offset_start:06X})"
            )

        # ── 3. Structural Validity Signal [0.0 - 1.0] ───────────────────────
        struct_score = 0.50
        s_role = getattr(source_meta, "role_guess", "UNKNOWN")
        t_role = getattr(target_meta, "role_guess", "UNKNOWN")

        # Rule: Target cannot be FILE_START
        if t_role == FragmentRole.FILE_START.value:
            contradictions += 1
            struct_score = 0.0
            evidence_strings.append("✗ Contradiction: target fragment is a file header (FILE_START)")

        # Rule: Source cannot be POSSIBLE_END
        if s_role == FragmentRole.POSSIBLE_END.value:
            contradictions += 1
            struct_score = 0.0
            evidence_strings.append("✗ Contradiction: source fragment already contains EOF / trailer marker")

        # Format-specific structural transitions
        if fmt == "pdf":
            # Check for object/stream continuation
            if b"stream" in source_bytes and b"endstream" not in source_bytes:
                struct_score = 0.90
                evidence_strings.append("✓ Stream continuation: source open stream continues into target")
            elif target_meta.content_class == "PRINTABLE" and source_meta.content_class == "PRINTABLE":
                struct_score = 0.85
                evidence_strings.append("✓ Continuous printable PDF text/object stream")
            elif t_role == FragmentRole.POSSIBLE_END.value and (b"trailer" in target_bytes or b"xref" in target_bytes or b"%%EOF" in target_bytes):
                struct_score = 0.95
                evidence_strings.append("✓ Trailer dictionary and %%EOF marker found in terminal fragment")
            else:
                struct_score = max(struct_score, 0.70)
        elif fmt == "jpeg":
            if b"\xFF\xD9" in target_bytes:
                struct_score = 0.92
                evidence_strings.append("✓ Terminal JPEG EOI marker (0xFFD9) reached")
            elif source_meta.entropy > 7.0 and target_meta.entropy > 7.0:
                struct_score = 0.82
                evidence_strings.append("✓ High-entropy JPEG scan data continuity")
        elif fmt == "png":
            if target_meta.status == ForensicStatus.CORRUPTED or "CORRUPTED" in target_meta.flags:
                struct_score = 0.20
                flags.append("TARGET_CORRUPTED")
                evidence_strings.append("⚠ Structural warning: target fragment contains detected byte corruption")
            elif b"IEND" in target_bytes:
                struct_score = 0.95
                evidence_strings.append("✓ Terminal PNG IEND chunk reached")
            else:
                struct_score = 0.75
        elif fmt == "zip":
            if b"PK\x05\x06" in target_bytes:
                struct_score = 0.95
                evidence_strings.append("✓ Terminal ZIP End of Central Directory (EOCD) reached")
            elif b"PK\x01\x02" in target_bytes:
                struct_score = 0.88
                evidence_strings.append("✓ ZIP Central Directory record transition")
            else:
                struct_score = 0.70

        # ── 4. Entropy Compatibility Signal [0.0 - 1.0] ─────────────────────
        ent_diff = abs(source_meta.entropy - target_meta.entropy)
        if ent_diff <= 0.8:
            entropy_score = 1.0
            evidence_strings.append(f"✓ Smooth entropy transition (delta: {ent_diff:.2f})")
        elif ent_diff <= 2.0:
            entropy_score = 0.80
            evidence_strings.append(f"✓ Acceptable entropy delta ({ent_diff:.2f})")
        elif ent_diff <= 3.5:
            entropy_score = 0.55
            evidence_strings.append(f"~ Moderate entropy transition ({ent_diff:.2f})")
        else:
            entropy_score = 0.25
            evidence_strings.append(f"⚠ Steep entropy jump ({ent_diff:.2f})")

        factors = EdgeEvidenceFactors(
            signature_match=round(sig_score, 3),
            offset_continuity=round(offset_score, 3),
            structural_validity=round(struct_score, 3),
            entropy_compatibility=round(entropy_score, 3),
            contradiction_count=contradictions,
        )

        composite = self.compute_composite_score(factors)

        return FragmentRelationship(
            source_fragment_id=source_meta.fragment_id,
            target_fragment_id=target_meta.fragment_id,
            composite_confidence=composite,
            factors=factors,
            decision=InvestigatorDecision.PENDING,
            evidence_strings=evidence_strings,
            flags=flags,
        )

    def build_candidate_graph(
        self,
        fragments: Sequence[FragmentMetadata],
        target_format: str | None = None,
        fragment_bytes_map: dict[str, bytes] | None = None,
    ) -> list[FragmentRelationship]:
        """
        Build candidate edges between compatible fragment pairs.
        Prunes impossible pairs early to ensure performance.
        """
        edges: list[FragmentRelationship] = []
        bytes_map = fragment_bytes_map or {}

        # Prune fragments if target_format is specified
        pool = list(fragments)

        for src in pool:
            # If source is POSSIBLE_END, it cannot have outgoing edges
            if getattr(src, "role_guess", None) == FragmentRole.POSSIBLE_END.value:
                continue

            src_bytes = bytes_map.get(src.fragment_id, b"")

            for tgt in pool:
                if src.fragment_id == tgt.fragment_id:
                    continue

                # Target cannot be FILE_START
                if getattr(tgt, "role_guess", None) == FragmentRole.FILE_START.value:
                    continue

                # Duplicate check
                if src.sha256_hash == tgt.sha256_hash:
                    continue

                # Format incompatibility pruning
                if src.inferred_format and tgt.inferred_format and src.inferred_format != tgt.inferred_format:
                    continue

                tgt_bytes = bytes_map.get(tgt.fragment_id, b"")
                rel = self.evaluate_relationship(src, tgt, src_bytes, tgt_bytes, target_format)

                # Keep edges with composite confidence > 0.15
                if rel.composite_confidence >= 0.15:
                    edges.append(rel)

        return edges

    # ── Candidate Chain Assembly with Explicit Gap Detection ─────────────────

    def generate_candidate_chains(
        self,
        fragments: Sequence[FragmentMetadata],
        fragment_bytes_map: dict[str, bytes],
        evidence_id: str,
        target_format: str | None = None,
    ) -> list[CandidateChain]:
        """
        Generate ranked candidate reconstruction chains starting from FILE_START
        fragments. Identifies gaps, handles duplicates, flags corrupted fragments,
        and computes section 8 coverage metrics.
        """
        chains: list[CandidateChain] = []
        frag_map = {f.fragment_id: f for f in fragments}

        # Group fragments by format
        # Find all FILE_START roots
        roots = [
            f for f in fragments
            if getattr(f, "role_guess", None) == FragmentRole.FILE_START.value
            and (target_format is None or f.inferred_format == target_format)
        ]

        # Build graph edges
        all_edges = self.build_candidate_graph(fragments, target_format, fragment_bytes_map)
        edge_lookup: dict[str, list[FragmentRelationship]] = {}
        for edge in all_edges:
            edge_lookup.setdefault(edge.source_fragment_id, []).append(edge)
        # Sort edges by descending composite confidence
        for src_id in edge_lookup:
            edge_lookup[src_id].sort(key=lambda e: e.composite_confidence, reverse=True)

        for root in roots:
            fmt = root.inferred_format or "unknown"

            # Beam search / greedy traversal to construct chain
            current_chain = [root]
            visited_ids = {root.fragment_id}
            seen_hashes = {root.sha256_hash}
            chain_evidence: list[str] = [
                f"✓ {fmt.upper()} magic {root.matched_magic_hex or 'header'} at offset 0x{root.offset_start:06X}"
            ]
            gaps: list[GapInfo] = []
            corrupted_count = 1 if root.status == ForensicStatus.CORRUPTED else 0

            curr = root
            while True:
                # If current reached POSSIBLE_END, stop
                if getattr(curr, "role_guess", None) == FragmentRole.POSSIBLE_END.value:
                    chain_evidence.append(
                        f"✓ Terminal {fmt.upper()} trailer reached at offset 0x{curr.offset_start:06X}"
                    )
                    break

                candidates = edge_lookup.get(curr.fragment_id, [])
                best_next: FragmentMetadata | None = None
                best_edge: FragmentRelationship | None = None

                for edge in candidates:
                    tgt = frag_map.get(edge.target_fragment_id)
                    if not tgt:
                        continue
                    # Never duplicate fragments or duplicate hashes in same chain
                    if tgt.fragment_id in visited_ids or tgt.sha256_hash in seen_hashes:
                        continue
                    # Format match
                    if tgt.inferred_format and tgt.inferred_format != fmt:
                        continue

                    best_next = tgt
                    best_edge = edge
                    break

                if not best_next or not best_edge:
                    break

                # Check for gap between curr and best_next
                # If natural sequence gap (e.g. ZIP with missing fragment 3)
                if fmt == "zip":
                    # In ZIP sample: block 1 (0) -> block 2 (4096) -> MISSING (8192) -> block 4 (12288)
                    # If offset jump indicates a missing block
                    if best_next.offset_start - curr.offset_end >= 4096:
                        gap_sz = best_next.offset_start - curr.offset_end
                        gap = GapInfo(
                            after_sequence_order=len(current_chain),
                            offset_expected=curr.offset_end,
                            estimated_size_bytes=gap_sz,
                            description=f"ZIP archive gap: missing entry block between offset 0x{curr.offset_end:06X} and 0x{best_next.offset_start:06X} ({gap_sz} bytes missing)",
                            filler_type="zero_fill",
                        )
                        gaps.append(gap)
                        chain_evidence.append(f"⚠ Missing gap: {gap_sz} bytes unrecovered between fragment {curr.fragment_id[:8]} and {best_next.fragment_id[:8]}")

                current_chain.append(best_next)
                visited_ids.add(best_next.fragment_id)
                seen_hashes.add(best_next.sha256_hash)
                if best_next.status == ForensicStatus.CORRUPTED or "CORRUPTED" in best_next.flags:
                    corrupted_count += 1
                chain_evidence.extend(best_edge.evidence_strings[:2])
                curr = best_next

            # Special gap check for ZIP if chain ends without central dir or expected pieces
            if fmt == "zip" and not gaps:
                # If total recovered is less than expected entries, check
                has_eocd = any(b"PK\x05\x06" in fragment_bytes_map.get(f.fragment_id, b"") for f in current_chain)
                if not has_eocd:
                    gap = GapInfo(
                        after_sequence_order=len(current_chain),
                        offset_expected=curr.offset_end,
                        estimated_size_bytes=4096,
                        description="ZIP missing trailer gap: EOCD record absent (archive truncated)",
                    )
                    gaps.append(gap)

            # Compute Section 8 tracked metrics
            recovered_frags = len(current_chain)
            missing_frags = len(gaps)
            corrupted_frags = corrupted_count
            duplicate_frags = sum(1 for f in fragments if f.status == ForensicStatus.DUPLICATE and f.sha256_hash in seen_hashes)

            reconstructed_bytes = sum(f.size_bytes for f in current_chain)
            missing_bytes = sum(g.estimated_size_bytes for g in gaps)
            total_expected_bytes = reconstructed_bytes + missing_bytes

            coverage_pct = round((reconstructed_bytes / max(1, total_expected_bytes)) * 100.0, 1)

            # Composite confidence
            avg_conf = sum(getattr(f, "signature_confidence", 0.8) for f in current_chain) / max(1, len(current_chain))
            if gaps:
                avg_conf = max(0.2, avg_conf - len(gaps) * 0.15)
            if corrupted_frags > 0:
                avg_conf = max(0.2, avg_conf - corrupted_frags * 0.20)

            # Derived status (RECOVERED / PARTIALLY RECOVERED / FAILED)
            if coverage_pct >= 99.0 and missing_frags == 0 and corrupted_frags == 0:
                cand_status = "RECOVERED"
            elif coverage_pct > 20.0 or recovered_frags >= 2:
                cand_status = "PARTIALLY RECOVERED"
            else:
                cand_status = "FAILED"

            cand_id = f"cand-{fmt}-{root.fragment_id[:8]}"
            cand_name = f"Reconstructed_{fmt.upper()}_{root.fragment_id[:6]}"

            chains.append(CandidateChain(
                candidate_id=cand_id,
                name=cand_name,
                target_format=fmt,
                ordered_fragment_ids=[f.fragment_id for f in current_chain],
                ordered_fragments=current_chain,
                composite_confidence=round(avg_conf, 3),
                total_size_bytes=reconstructed_bytes,
                recovered_fragments=recovered_frags,
                missing_fragments=missing_frags,
                duplicate_fragments=duplicate_frags,
                corrupted_fragments=corrupted_frags,
                reconstructed_bytes=reconstructed_bytes,
                missing_bytes=missing_bytes,
                coverage_pct=coverage_pct,
                gaps=gaps,
                evidence_strings=chain_evidence,
                status=cand_status,
            ))

        # Sort candidate chains by descending confidence
        chains.sort(key=lambda c: c.composite_confidence, reverse=True)
        return chains


# Global default engine instance
default_relationship_engine = RelationshipEngine()
