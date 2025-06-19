import requests

def test_health_endpoint():
    resp = requests.get('http://localhost:8000/health')
    assert resp.status_code == 200
    assert resp.json().get('status') == 'ok'

def test_self_audit_placeholder():
    assert True 