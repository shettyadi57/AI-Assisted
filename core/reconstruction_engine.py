"""
Reconstruction Engine — Phase 5 LIVE

Traverses candidate chains, synthesizes real output files on disk with
explicit gap markers, computes section 8 tracked metrics, and generates
bit-level provenance byte-maps linking every output byte to its source fragment.

Zero dependencies on FastAPI or web frameworks.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from core.relationship_engine import CandidateChain, FragmentRelationship, GapInfo


# ─── Data Classes ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ProvenanceByteSpan:
    """Bit-level provenance tracking for a span of bytes in the reconstructed output."""
    output_offset: int
    length_bytes: int
    source_fragment_id: str
    fragment_offset: int = 0
    edge_confidence: float = 1.0
    investigator_accepted: bool = False
    is_synthetic_filler: bool = False
    note: str = ""
    # Phase 10 Enhancements (Spec Section 19 & 20)
    output_end_offset: int = 0
    original_evidence_offset: int = 0
    original_evidence_id: str = ""
    sha256_hash: str = ""
    validation_status: str = "CONFIRMED"
    entropy: float = 0.0

    def to_dict(self) -> dict:
        """Serialize provenance span to dictionary."""
        end_off = self.output_end_offset if self.output_end_offset > 0 else max(0, self.output_offset + self.length_bytes - 1)
        return {
            "output_start": self.output_offset,
            "output_end": end_off,
            "length_bytes": self.length_bytes,
            "source_fragment_id": self.source_fragment_id,
            "original_evidence_offset": self.original_evidence_offset,
            "original_evidence_id": self.original_evidence_id,
            "sha256_hash": self.sha256_hash,
            "validation_status": self.validation_status,
            "edge_confidence": self.edge_confidence,
            "investigator_accepted": self.investigator_accepted,
            "is_synthetic_filler": self.is_synthetic_filler,
            "entropy": self.entropy,
            "note": self.note,
        }


def find_provenance_span_for_offset(
    spans: Sequence[ProvenanceByteSpan], byte_offset: int
) -> ProvenanceByteSpan | None:
    """Query provenance span covering the specified reconstructed byte offset."""
    for span in spans:
        end = span.output_end_offset if span.output_end_offset > 0 else (span.output_offset + span.length_bytes - 1)
        if span.output_offset <= byte_offset <= end:
            return span
    return None


@dataclass
class ReconstructionCandidate:
    """An assembled file candidate representing an ordered sequence of fragments."""
    candidate_id: str
    target_format: str
    ordered_fragment_ids: list[str]
    total_size_bytes: int
    composite_confidence: float
    provenance_map: list[ProvenanceByteSpan] = field(default_factory=list)
    is_finalized: bool = False
    reconstructed_sha256: str | None = None
    artifact_path: str | None = None


@dataclass
class ReassemblyResult:
    """Final output from reassembling a candidate file."""
    candidate_id: str
    target_format: str
    artifact_path: str
    reconstructed_sha256: str
    total_output_bytes: int
    real_data_bytes: int
    filler_bytes: int
    coverage_pct: float
    status: str
    provenance_map: list[ProvenanceByteSpan]
    metrics: dict[str, int | float]


# ─── Abstract Interface ─────────────────────────────────────────────────────

class ReconstructionEngineInterface(ABC):
    """Abstract interface for fragment chain assembly and provenance mapping."""

    @abstractmethod
    def assemble_candidate(
        self,
        candidate_id: str,
        target_format: str,
        edges: Sequence[FragmentRelationship],
        root_fragment_id: str,
    ) -> ReconstructionCandidate:
        """Find the optimal path in the relationship graph to assemble a candidate."""
        raise NotImplementedError

    @abstractmethod
    def synthesize_file(
        self,
        candidate: ReconstructionCandidate,
        fragment_store: Mapping[str, bytes],
    ) -> bytes:
        """Concatenate fragments according to the ordered candidate sequence."""
        raise NotImplementedError

    @abstractmethod
    def generate_provenance_map(
        self,
        candidate: ReconstructionCandidate,
        fragment_lengths: Mapping[str, int],
        edges: Sequence[FragmentRelationship],
    ) -> list[ProvenanceByteSpan]:
        """Generate a complete output-byte to source-fragment provenance map."""
        raise NotImplementedError


# ─── Live Reconstruction Engine Implementation ──────────────────────────────

class ReconstructionEngine(ReconstructionEngineInterface):
    """
    Assembles candidate chains into real files on disk with explicit gap handling.
    """

    def assemble_candidate(
        self,
        candidate_id: str,
        target_format: str,
        edges: Sequence[FragmentRelationship],
        root_fragment_id: str,
    ) -> ReconstructionCandidate:
        """
        Assemble a candidate sequence by following best edges from root.
        """
        ordered = [root_fragment_id]
        curr = root_fragment_id
        visited = {curr}

        edge_map: dict[str, list[FragmentRelationship]] = {}
        for e in edges:
            edge_map.setdefault(e.source_fragment_id, []).append(e)

        for src in edge_map:
            edge_map[src].sort(key=lambda x: x.composite_confidence, reverse=True)

        while True:
            next_edges = [e for e in edge_map.get(curr, []) if e.target_fragment_id not in visited]
            if not next_edges:
                break
            best = next_edges[0]
            ordered.append(best.target_fragment_id)
            visited.add(best.target_fragment_id)
            curr = best.target_fragment_id

        return ReconstructionCandidate(
            candidate_id=candidate_id,
            target_format=target_format,
            ordered_fragment_ids=ordered,
            total_size_bytes=0,
            composite_confidence=0.85,
        )

    def synthesize_file(
        self,
        candidate: ReconstructionCandidate,
        fragment_store: Mapping[str, bytes],
    ) -> bytes:
        """
        Concatenate fragment bytes in order.
        """
        output = io_buffer = bytearray()
        for fid in candidate.ordered_fragment_ids:
            chunk = fragment_store.get(fid, b"")
            output.extend(chunk)
        return bytes(output)

    def generate_provenance_map(
        self,
        candidate: ReconstructionCandidate,
        fragment_lengths: Mapping[str, int],
        edges: Sequence[FragmentRelationship],
    ) -> list[ProvenanceByteSpan]:
        """
        Generate provenance spans for every block in the candidate.
        """
        edge_conf_map = {(e.source_fragment_id, e.target_fragment_id): e.composite_confidence for e in edges}
        spans: list[ProvenanceByteSpan] = []
        offset = 0
        prev_id: str | None = None

        for fid in candidate.ordered_fragment_ids:
            length = fragment_lengths.get(fid, 0)
            conf = 1.0 if prev_id is None else edge_conf_map.get((prev_id, fid), 0.85)
            spans.append(ProvenanceByteSpan(
                output_offset=offset,
                length_bytes=length,
                source_fragment_id=fid,
                fragment_offset=0,
                edge_confidence=conf,
                investigator_accepted=False,
                is_synthetic_filler=False,
                note=f"Carved fragment {fid[:8]} (length: {length} bytes)",
            ))
            offset += length
            prev_id = fid

        return spans

    def reassemble_to_disk(
        self,
        chain: CandidateChain,
        fragment_store: Mapping[str, bytes],
        output_dir: Path,
        filler_type: str = "zero_fill",
    ) -> ReassemblyResult:
        """
        Assemble the candidate chain into a real output file in output_dir.
        Tracks explicit gaps and ensures gap metadata is 100% transparent.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        ext = chain.target_format.lower()
        if ext == "jpeg":
            ext = "jpg"
        out_filename = f"{chain.candidate_id}.{ext}"
        out_path = output_dir / out_filename

        output_bytes = bytearray()
        provenance: list[ProvenanceByteSpan] = []
        gap_lookup = {g.after_sequence_order: g for g in chain.gaps}

        current_offset = 0
        real_data_bytes = 0
        filler_bytes = 0

        meta_lookup = {m.fragment_id: m for m in chain.ordered_fragments}
        first_ev_id = chain.ordered_fragments[0].evidence_id if chain.ordered_fragments else ""

        for seq, fid in enumerate(chain.ordered_fragment_ids, start=1):
            chunk = fragment_store.get(fid, b"")
            sz = len(chunk)
            output_bytes.extend(chunk)
            real_data_bytes += sz

            meta = meta_lookup.get(fid)
            orig_off = meta.offset_start if meta else 0
            ev_id = meta.evidence_id if meta else first_ev_id
            sha = meta.sha256_hash if meta else hashlib.sha256(chunk).hexdigest()
            status_val = meta.status.value if meta and hasattr(meta.status, "value") else str(meta.status if meta else "CONFIRMED")
            ent = meta.entropy if meta else 0.0

            provenance.append(ProvenanceByteSpan(
                output_offset=current_offset,
                output_end_offset=current_offset + sz - 1,
                length_bytes=sz,
                source_fragment_id=fid,
                fragment_offset=0,
                original_evidence_offset=orig_off,
                original_evidence_id=ev_id,
                sha256_hash=sha,
                validation_status=status_val,
                edge_confidence=chain.composite_confidence,
                investigator_accepted=False,
                is_synthetic_filler=False,
                entropy=ent,
                note=f"Seq #{seq}: Fragment {fid[:8]} ({sz} bytes)",
            ))
            current_offset += sz

            # Check if there is an explicit gap after this sequence position
            if seq in gap_lookup:
                gap = gap_lookup[seq]
                gap_sz = gap.estimated_size_bytes
                if filler_type == "zero_fill":
                    gap_data = b"\x00" * gap_sz
                    output_bytes.extend(gap_data)
                    filler_bytes += gap_sz
                    gap_sha = hashlib.sha256(gap_data).hexdigest()
                    provenance.append(ProvenanceByteSpan(
                        output_offset=current_offset,
                        output_end_offset=current_offset + gap_sz - 1,
                        length_bytes=gap_sz,
                        source_fragment_id="GAP",
                        fragment_offset=0,
                        original_evidence_offset=gap.offset_expected,
                        original_evidence_id=first_ev_id,
                        sha256_hash=gap_sha,
                        validation_status="MISSING",
                        edge_confidence=0.0,
                        investigator_accepted=False,
                        is_synthetic_filler=True,
                        entropy=0.0,
                        note=f"SYNTHETIC GAP FILLER ({gap_sz} bytes): {gap.description}",
                    ))
                    current_offset += gap_sz

        # Write output artifact to disk
        final_data = bytes(output_bytes)
        out_path.write_bytes(final_data)
        out_sha256 = hashlib.sha256(final_data).hexdigest()

        # Update candidate chain record
        chain.status = "RECOVERED" if (filler_bytes == 0 and chain.corrupted_fragments == 0 and chain.coverage_pct >= 99.0) else "PARTIALLY RECOVERED"

        metrics = {
            "original_fragment_count": len(chain.ordered_fragment_ids) + len(chain.gaps),
            "recovered_fragment_count": chain.recovered_fragments,
            "missing_fragment_count": chain.missing_fragments,
            "duplicate_fragment_count": chain.duplicate_fragments,
            "corrupted_fragment_count": chain.corrupted_fragments,
            "reconstructed_byte_count": real_data_bytes,
            "missing_byte_count": chain.missing_bytes,
            "coverage_pct": chain.coverage_pct,
        }

        return ReassemblyResult(
            candidate_id=chain.candidate_id,
            target_format=chain.target_format,
            artifact_path=str(out_path),
            reconstructed_sha256=out_sha256,
            total_output_bytes=len(final_data),
            real_data_bytes=real_data_bytes,
            filler_bytes=filler_bytes,
            coverage_pct=chain.coverage_pct,
            status=chain.status,
            provenance_map=provenance,
            metrics=metrics,
        )


# Global default reconstruction engine instance
default_reconstruction_engine = ReconstructionEngine()
