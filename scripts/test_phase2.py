"""Quick Phase 2 integration test."""
import sys
sys.path.insert(0, ".")
from backend.database import apply_migrations
apply_migrations()

from fastapi.testclient import TestClient
from backend.main import app

with TestClient(app) as client:
    # 1. Register sample dataset
    r = client.post('/api/v1/discovery/sample')
    assert r.status_code == 201, r.text
    ev = r.json()
    ev_id = ev['id']
    print("Evidence:", ev_id[:8], "size="+str(ev['file_size_bytes'])+"b  is_sample="+str(ev['is_sample_dataset']))

    # 2. Analyze fragments
    r2 = client.post('/api/v1/analysis/fragments',
                     json={'evidence_id': ev_id, 'block_size': 4096})
    assert r2.status_code == 200, r2.text
    result = r2.json()
    print("Fragments:", result['fragment_count'], " duplicates:", result['duplicate_count'], " block:", result['block_size_used'])

    for frag in result['fragments'][:3]:
        dup = ' [DUP]' if frag['status'] == 'DUPLICATE' else ''
        print("  frag", frag['id'][:8], " off="+str(frag['offset_start']),
              " ent="+str(round(frag['entropy'],4)),
              frag['entropy_class']+"/"+frag['content_class']+dup)
        print("  hex:", frag['hex_preview'][:47])

    # 3. List fragments
    r3 = client.get('/api/v1/analysis/fragments?evidence_id='+ev_id)
    assert r3.status_code == 200, r3.text
    lst = r3.json()
    print("List total="+str(lst['total']))

    # 4. Hex dump
    fid = result['fragments'][0]['id']
    r4 = client.get('/api/v1/analysis/fragments/'+fid+'/hex?max_bytes=64')
    assert r4.status_code == 200, r4.text
    hexd = r4.json()
    print("Hex dump:", hexd['bytes_returned'], "bytes,", len(hexd['rows']), "rows")
    print("  Row0 hex:", hexd['rows'][0]['hex'])
    print("  Row0 asc:", hexd['rows'][0]['ascii'])

    # 5. Idempotent
    r5 = client.post('/api/v1/analysis/fragments',
                     json={'evidence_id': ev_id, 'block_size': 4096})
    assert r5.status_code == 200
    print("Idempotent:", r5.json()['fragment_count'], "fragments (same)")

print("ALL TESTS PASSED")
