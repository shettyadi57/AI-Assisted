# Prior Art & Technical Differentiation

## 1. Prior Art & Shared Limitations

In digital forensics and data recovery, file carving is the process of extracting files from raw disk images, damaged media, or unallocated slack space without relying on filesystem metadata. Current open-source and commercial standards address this problem with specific heuristics:

| Tool | Approach | Limitation |
|------|----------|------------|
| **Scalpel** | Header/footer signature carving | Finds fragments; cannot explain *why* they were ordered or assess ordering confidence |
| **PhotoRec** | Broad-format batch carving | Produces outputs, not reasoning — no fragment relationship transparency |
| **bulk_extractor** | Byte-level feature scanning | Surface-level feature tagging; no structural validation of fragment sequences |

### Shared Blind Spot
**None of these tools expose reconstruction reasoning.** 
They do not provide visibility into why fragments were ordered in a particular sequence, what the statistical confidence of each edge is and why, or allow a human forensic investigator to accept or reject an individual fragment relationship before finalization. 

Existing tools operate as **automated batch tools, not interactive forensic investigation workbenches.**

---

## 2. Our Approach: Reconstruct

Reconstruct treats file fragment ordering as a **scored graph-construction problem** with transparent, inspectable evidence per edge:

```
Fragment A ──[edge: 0.91]──► Fragment B ──[edge: 0.74]──► Fragment C
             │                             │
             ├─ Signature match: ✓          ├─ Signature match: ✓
             ├─ Offset continuity: ✓        ├─ Offset continuity: ~
             ├─ Structural validity: ✓      ├─ Structural validity: ✓
             └─ Entropy profile: ✓          └─ Entropy profile: ✗
```

### Multi-Signal Evidence Scoring
Every candidate relationship between fragments is **scored on independent axes of evidence**, surfaced to the investigator as human-readable factors rather than an opaque black-box percentage:
1. **Signature & Magic Byte Alignment:** Verification of file format headers, chunk identifiers, and marker consistency.
2. **Offset & Sector Continuity:** Physical media proximity and logical sequence alignment.
3. **Structural Validity:** Format-specific internal parser validation (e.g., JPEG marker streams, PNG chunk CRC32 checksums, PDF cross-reference tables).
4. **Entropy Profile Compatibility:** Compression and encryption transition profiling across fragment boundaries.
5. **Contradiction Detection:** Penalization of mutually exclusive markers or impossible length offsets.

### Human-in-the-Loop Workbench
An investigator can **accept or reject individual fragment-to-fragment edges** before the candidate file is finalized. This preserves the ability to reconstruct the *why*, not just the *what*.

### Complete Provenance & Chain of Custody
Full provenance is maintained from start to finish:
- Every output byte traces back to its source fragment and physical offset.
- Every edge traces back to its decomposed evidence scores.
- Every investigator decision (accept/reject/override) is logged in an immutable, cryptographic audit trail.

---

## 3. Technical Difference Summary

| Dimension | Batch Tools (Scalpel / PhotoRec / bulk_extractor) | Reconstruct Workbench |
|-----------|---------------------------------------------------|-----------------------|
| **Fragment Ordering Model** | Heuristic / format-signature-driven batch carve | Candidate relationship scoring (graph edges with multi-factor evidence) |
| **Confidence Communication** | None, or opaque single percentage | Decomposed per-factor evidence: signature match, offset continuity, structural validity, entropy |
| **Investigator Control** | None — batch accept-all | Accept / reject individual fragment relationships before file finalization |
| **Audit Trail & Provenance** | None | Full provenance: output byte → source fragment → edge evidence → investigator decision |
| **Workflow Model** | Automated pipeline, inspect output file | **Human-in-the-loop investigation workbench** |

---

## 4. Master Context: Non-Negotiable Forensic Rules

Every phase of the Reconstruct architecture adheres to the following non-negotiable rules:

1. **No Fabricated Results:** Every score and metric originates from real computational analysis or verified sample data.
2. **Explainable Confidence Scores:** Multi-signal breakdown is stored and displayed alongside any composite score.
3. **Evidence is Read-Only:** Raw evidence files are cryptographically hashed (SHA-256) on ingest; all analysis writes to derived storage.
4. **Six Distinct Forensic States:** `CONFIRMED`, `INFERRED`, `UNCERTAIN`, `MISSING`, `CORRUPTED`, `DUPLICATE` — never collapsed into a binary or generic state.
5. **Phase-Gated Skeletons (HTTP 501):** Features not yet implemented return HTTP 501 with a descriptive phase payload, never fake success responses.
6. **Mandatory Human Verification:** No reconstructed file is marked finalized without explicit investigator decision; rejections are immutably logged.
7. **Legal Disclaimer:** Permanent UI notice: *"Portfolio / prototype tool. Not legally admissible."*
