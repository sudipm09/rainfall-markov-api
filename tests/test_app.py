import json
from pathlib import Path
from fastapi.testclient import TestClient
from app import app, counts

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]

def test_health():
    assert client.get('/health').json() == {'status': 'ok'}

def test_compare():
    payload = json.loads((ROOT/'data'/'fastapi_input.json').read_text())
    r = client.post('/compare', json=payload)
    assert r.status_code == 200
    info = r.json()
    assert info['july']['rainy_days'] == 26
    assert info['january']['rainy_days'] == 11
    assert sum(map(sum, info['july']['transition_counts'])) == 29
    assert sum(map(sum, info['january']['transition_counts'])) == 29
    assert info['chi_square_statistic'] > 0

def test_invalid():
    assert client.post('/compare', json={'july':[0,2],'january':[0,1]}).status_code == 422
