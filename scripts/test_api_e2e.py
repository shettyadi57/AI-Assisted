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

    # 8. Test Bit-level provenance
    r_prov = client.get(f"/api/v1/reconstruction/candidates/{top_cand['id']}/provenance")
    assert r_prov.status_code == 200, r_prov.text
    prov_spans = r_prov.json()['spans']
    print(f"8. Bit-Level Provenance: {len(prov_spans)} spans mapped")
    r_prov_q = client.get(f"/api/v1/reconstruction/candidates/{top_cand['id']}/provenance?offset=0")
    assert r_prov_q.status_code == 200, r_prov_q.text
    assert r_prov_q.json()['found'] is True
    print(f"   Queried offset 0: mapped to fragment {r_prov_q.json()['span']['source_fragment_id'][:8]} at evidence offset 0x{r_prov_q.json()['span']['original_evidence_offset']:X}")

    # 9. Test Forensic Evidence Report (HTML & JSON)
    r_rep_html = client.get(f"/api/v1/reconstruction/candidates/{top_cand['id']}/report?format=html")
    assert r_rep_html.status_code == 200, r_rep_html.text
    assert "FORENSIC EVIDENCE REPORT" in r_rep_html.text
    r_rep_json = client.get(f"/api/v1/reconstruction/candidates/{top_cand['id']}/report?format=json")
    assert r_rep_json.status_code == 200, r_rep_json.text
    print(f"9. Generated Evidence Report (HTML size: {len(r_rep_html.text)} chars, JSON summary ok)")

    # 10. Test Forensic Bundle ZIP Export
    r_bundle = client.get(f"/api/v1/reconstruction/candidates/{top_cand['id']}/bundle")
    assert r_bundle.status_code == 200, r_bundle.text
    assert "application/zip" in r_bundle.headers["content-type"]
    bundle_sha = r_bundle.headers.get("X-Export-SHA256")
    print(f"10. Exported Forensic Bundle: {len(r_bundle.content)} bytes (SHA-256: {bundle_sha[:16]}...)")

    # 11. Test Candidate Preview
    r_prev = client.get(f"/api/v1/reconstruction/candidates/{top_cand['id']}/preview")
    assert r_prev.status_code == 200, r_prev.text
    prev = r_prev.json()
    print(f"11. Candidate Preview: format={prev['format']} is_pdf={prev['is_pdf']} size={prev['size_bytes']} bytes")

print("\nALL API END-TO-END TESTS PASSED (PHASES 1-5, 9, 10 VERIFIED)!")
