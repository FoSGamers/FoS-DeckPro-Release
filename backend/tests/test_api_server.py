import pytest
from fastapi.testclient import TestClient
from api_server import app
import time

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data

def test_get_metrics():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "memory" in data
    assert "responseTime" in data
    assert "timestamp" in data
    assert isinstance(data["cpu"], float)
    assert isinstance(data["memory"], float)
    assert isinstance(data["responseTime"], float)

def test_run_test_success():
    test_name = "test_success"
    response = client.post("/api/test", json={"name": test_name})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_name
    assert data["status"] == "success"
    assert "id" in data
    assert "duration" in data
    assert "timestamp" in data

def test_run_test_failure():
    # We can't directly test the failure case since it's random
    # But we can verify the endpoint exists and accepts the request
    test_name = "test_failure"
    response = client.post("/api/test", json={"name": test_name})
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["name"] == test_name
        assert data["status"] == "success"
    else:
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data

def test_get_tests():
    # First run a test to ensure we have some data
    client.post("/api/test", json={"name": "test_get_tests"})
    
    response = client.get("/api/tests")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        test = data[0]
        assert "id" in test
        assert "name" in test
        assert "status" in test
        assert "duration" in test
        assert "timestamp" in test

def test_invalid_test_request():
    response = client.post("/api/test", json={})
    assert response.status_code == 422  # Validation error

def test_metrics_update():
    # Test that metrics are updated over time
    response1 = client.get("/api/metrics")
    time.sleep(1)  # Wait for 1 second
    response2 = client.get("/api/metrics")
    
    data1 = response1.json()
    data2 = response2.json()
    
    assert data1["timestamp"] != data2["timestamp"]
    # CPU and memory might be the same, but response time should be different
    assert data1["responseTime"] != data2["responseTime"] 