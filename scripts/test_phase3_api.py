import sys
sys.path.insert(0, ".")
from fastapi.testclient import TestClient
from backend.main import app

with TestClient(app) as client:
    r = client.post('/api/v1/discovery/sample')
    ev_id = r.json()['id']
    r2 = client.post('/api/v1/analysis/fragments', json={'evidence_id': ev_id, 'force_reanalyze': True})
    assert r2.status_code == 200, r2.text
    data = r2.json()
    print('Analyzed fragments:', data['fragment_count'])
    for f in data['fragments']:
        print(f"{f['id'][:8]} off={f['offset_start']:5d} fmt={str(f['inferred_format']):5s} role={f['role_guess']:12s} conf={f['signature_confidence']:.2f} status={f['status']:9s} magic={str(f['matched_magic_hex'])[:16]}")
    
    # Check signatures endpoint
    r3 = client.get('/api/v1/analysis/signatures')
    assert r3.status_code == 200, r3.text
    sigs = r3.json()
    print('Supported signatures:', len(sigs), [s['format_id'] for s in sigs])
