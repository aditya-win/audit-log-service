import pytest
from scripts.generate_logs import generate_logs

def test_generator_deterministic():
    # Same seed and count should produce identical outputs
    logs1 = generate_logs(count=50, seed=42, scenario="MIXED")
    logs2 = generate_logs(count=50, seed=42, scenario="MIXED")
    
    assert logs1 == logs2

def test_generator_different_seeds():
    logs1 = generate_logs(count=10, seed=42, scenario="VALID")
    logs2 = generate_logs(count=10, seed=99, scenario="VALID")
    
    assert logs1 != logs2

def test_generator_valid_scenario():
    logs = generate_logs(count=5, seed=1, scenario="VALID")
    assert len(logs) == 5
    for log in logs:
        assert log["eventType"] in ["USER_LOGIN", "RECORD_UPDATED", "PERMISSION_GRANTED", "DATA_ACCESS"]
        assert "actorId" in log

def test_generator_invalid_scenario():
    logs = generate_logs(count=10, seed=1, scenario="INVALID")
    # Just check that it returns the expected count and they are dicts
    assert len(logs) == 10
    assert isinstance(logs[0], dict)

def test_generator_edge_case():
    logs = generate_logs(count=10, seed=1, scenario="EDGE_CASE")
    assert len(logs) == 10

def test_generator_suspicious():
    logs = generate_logs(count=2, seed=1, scenario="SUSPICIOUS")
    for log in logs:
        assert log["eventType"] == "PERMISSION_GRANTED"
        assert log["actorId"] == "admin"
