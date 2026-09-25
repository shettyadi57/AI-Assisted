import sys
from pathlib import Path
sys.path.insert(0, ".")
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from core.fragment_analyzer import FragmentAnalyzer
from core.relationship_engine import default_relationship_engine
from core.reconstruction_engine import default_reconstruction_engine

soup_path = Path("sample-data/loose-fragment-soup.bin")
assert soup_path.exists(), "Soup file missing!"
raw_bytes = soup_path.read_bytes()

# 1. Analyze fragments
analyzer = FragmentAnalyzer(block_size=4096)
fragments = list(analyzer.analyze_blob(raw_bytes, evidence_id="soup-ev-001"))
print(f"Total fragments analyzed: {len(fragments)}")

# Slice actual bytes map
bytes_map = {}
for f in fragments:
    bytes_map[f.fragment_id] = raw_bytes[f.offset_start : f.offset_end]

# 2. Build candidate chains
chains = default_relationship_engine.generate_candidate_chains(
    fragments=fragments,
    fragment_bytes_map=bytes_map,
    evidence_id="soup-ev-001",
)
print(f"\nGenerated candidate chains: {len(chains)}")
for c in chains:
    print(f"\nCandidate: {c.candidate_id} ({c.name})")
    print(f"  Format: {c.target_format} | Status: {c.status} | Confidence: {c.composite_confidence:.2f}")
    print(f"  Coverage: {c.coverage_pct}% | Recovered: {c.recovered_fragments} | Gaps: {c.missing_fragments} | Corrupted: {c.corrupted_fragments}")
    print(f"  Ordered Fragment IDs ({len(c.ordered_fragment_ids)}):")
    for seq, fid in enumerate(c.ordered_fragment_ids, 1):
        f = next(x for x in fragments if x.fragment_id == fid)
        print(f"    #{seq}: {fid[:8]} (off={f.offset_start:5d}, fmt={f.inferred_format}, role={f.role_guess})")
    if c.gaps:
        print(f"  Gaps:")
        for g in c.gaps:
            print(f"    After #{g.after_sequence_order}: {g.description}")
    print(f"  Evidence:")
    for ev in c.evidence_strings[:4]:
        print(f"    {ev}")

# 3. Reassemble to disk
out_dir = Path("derived-artifacts")
print(f"\n--- Reassembling Artifacts into {out_dir} ---")
for c in chains:
    res = default_reconstruction_engine.reassemble_to_disk(
        chain=c,
        fragment_store=bytes_map,
        output_dir=out_dir,
        filler_type="zero_fill",
    )
    print(f"Reconstructed: {Path(res.artifact_path).name} -> {res.total_output_bytes}B, SHA256: {res.reconstructed_sha256[:16]}... Coverage: {res.coverage_pct}%")
    assert Path(res.artifact_path).exists()

print("\nALL PIPELINE CHECKS PASSED!")
