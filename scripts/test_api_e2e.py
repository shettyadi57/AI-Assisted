import sys
from pathlib import Path
sys.path.insert(0, ".")
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from backend.main import app

with TestClient(app) as client:
    # 1. Register sample dataset
    r = client.post('/api/v1/discovery/sample')
    assert r.status_code == 201, r.text
    ev_id = r.json()['id']
    print(f"1. Registered evidence: {ev_id[:8]}")

    # 2. Analyze fragments
    r2 = client.post('/api/v1/analysis/fragments', json={'evidence_id': ev_id, 'force_reanalyze': True})
    assert r2.status_code == 200, r2.text
    frags = r2.json()['fragments']
    print(f"2. Analyzed {len(frags)} fragments")

    # 3. Test linking / graph generation
    r_link = client.post(f'/api/v1/linking/generate?evidence_id={ev_id}')
    assert r_link.status_code == 200, r_link.text
    edges = r_link.json()
    print(f"3. Generated {len(edges)} relationship edges")
    if edges:
        print(f"   Sample edge: {edges[0]['source_fragment_id'][:8]} -> {edges[0]['target_fragment_id'][:8]} (conf={edges[0]['composite_confidence']:.2f})")

    # 4. Test candidate generation
    r_cand = client.post('/api/v1/reconstruction/candidates', json={'evidence_id': ev_id})
    assert r_cand.status_code == 200, r_cand.text
    candidates = r_cand.json()
    print(f"4. Generated {len(candidates)} candidates:")
    for c in candidates:
        print(f"   Candidate {c['id']}: fmt={c['target_format']:4s} status={c['status']:18s} cov={c['coverage_pct']:5.1f}% conf={c['composite_confidence']:.2f} frags={len(c['fragments'])} gaps={len(c['gaps'])}")

    # 5. Test reassembly on top candidate (PDF)
    top_cand = next((c for c in candidates if c['target_format'] == 'pdf'), candidates[0])
    r_asm = client.post(f"/api/v1/reconstruction/candidates/{top_cand['id']}/assemble", json={'filler_type': 'zero_fill'})
    assert r_asm.status_code == 200, r_asm.text
    asm = r_asm.json()
    print(f"5. Assembled candidate {asm['id']}:")
    print(f"   Status: {asm['status']}")
    print(f"   SHA-256: {asm['reconstruction_sha256']}")
    print(f"   Artifact path: {asm['artifact_path']}")

    # 6. Test artifact download
    r_dl = client.get(f"/api/v1/reconstruction/candidates/{top_cand['id']}/artifact")
    assert r_dl.status_code == 200, r_dl.status_code
    print(f"6. Downloaded artifact: {len(r_dl.content)} bytes")

    # 7. Test ZIP with gap reassembly
    zip_cand = next((c for c in candidates if c['target_format'] == 'zip'), None)
    if zip_cand:
        r_zip = client.post(f"/api/v1/reconstruction/candidates/{zip_cand['id']}/assemble", json={'filler_type': 'zero_fill'})
        assert r_zip.status_code == 200, r_zip.text
        z_asm = r_zip.json()
        print(f"7. ZIP Candidate: Status={z_asm['status']}, Coverage={z_asm['coverage_pct']}%, Gaps={len(z_asm['gaps'])}")

print("\nALL API END-TO-END TESTS PASSED!")
