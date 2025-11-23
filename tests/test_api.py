"""API unit tests using FastAPI TestClient (Milestone 6)."""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure API module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from api.main import app, load_artifacts

# Trigger startup manually for testing
load_artifacts()

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert data['status'] == 'ok'
    assert 'model_loaded' in data
    assert 'data_available' in data


def test_predict_endpoint_valid():
    """Test predict endpoint with valid forecast data."""
    payload = {
        "region_id": "R1",
        "forecast": [
            {"date": "2025-11-24", "temp_mean": 25.0, "rel_humidity": 70.0, "pm25": 35.0},
            {"date": "2025-11-25", "temp_mean": 26.0, "rel_humidity": 68.0, "pm25": 38.0},
            {"date": "2025-11-26", "temp_mean": 24.5, "rel_humidity": 72.0, "pm25": 33.0}
        ]
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'region_id' in data
    assert 'predictions' in data
    assert len(data['predictions']) == 3
    
    # Check first prediction structure
    pred = data['predictions'][0]
    assert 'date' in pred
    assert 'risk_score' in pred
    assert 'expected_admissions' in pred
    assert 'top_drivers' in pred
    assert 0 <= pred['risk_score'] <= 1
    assert pred['expected_admissions'] >= 0


def test_predict_endpoint_empty():
    """Test predict endpoint with empty forecast."""
    payload = {
        "region_id": "R1",
        "forecast": []
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400


def test_alert_endpoint():
    """Test alert endpoint."""
    payload = {
        "region_id": "R1",
        "current_temp_mean": 35.0
    }
    response = client.post("/alert", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'triggered' in data
    assert 'threshold_value' in data
    assert 'current_value' in data
    assert 'expected_admissions' in data
    assert 'recommended_actions' in data
    assert isinstance(data['recommended_actions'], list)


def test_alert_below_threshold():
    """Test alert when below threshold."""
    payload = {
        "region_id": "R1",
        "current_temp_mean": 15.0,
        "threshold": 30.0
    }
    response = client.post("/alert", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data['triggered'] == False
    assert len(data['recommended_actions']) == 0
