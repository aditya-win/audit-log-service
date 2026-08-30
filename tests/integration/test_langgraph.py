import pytest
from app.langgraph.graph import build_audit_graph
from app.langgraph.state import AuditGraphState
from app.utils.hashing import GENESIS_HASH, calculate_hash
from datetime import datetime, timezone

def generate_valid_event():
    ts = datetime.now(timezone.utc)
    ev = {
        "id": 1,
        "eventType": "USER_LOGIN",
        "actorId": "user-1",
        "resourceType": "system",
        "resourceId": "res-1",
        "payload": "{}",
        "timestamp": ts,
        "previous_hash": GENESIS_HASH
    }
    ev["current_hash"] = calculate_hash(
        ev["eventType"], ev["actorId"], ev["resourceType"], ev["resourceId"], ev["payload"], ev["timestamp"], ev["previous_hash"]
    )
    return ev

def test_successful_graph():
    graph = build_audit_graph()
    state = AuditGraphState(
        audit_events=[generate_valid_event()],
        validation_results=[],
        chain_verification={},
        findings=[],
        severity=None,
        summary=None,
        errors=[],
        retry_count=0,
        max_retries=3,
        metadata={}
    )
    
    result = graph.invoke(state)
    assert not result.get("errors")
    assert result["summary"].startswith("Processed 1 events")

def test_transient_failure_retry_success():
    graph = build_audit_graph()
    state = AuditGraphState(
        audit_events=[generate_valid_event()],
        validation_results=[],
        chain_verification={},
        findings=[],
        severity=None,
        summary=None,
        errors=[],
        retry_count=0,
        max_retries=3,
        metadata={"simulate_analyze_error": "timeout", "fail_attempts": 1}
    )
    
    result = graph.invoke(state)
    assert not result.get("errors")
    assert result["retry_count"] == 1
    assert result["summary"] is not None

def test_transient_failure_retry_retry_failure():
    graph = build_audit_graph()
    state = AuditGraphState(
        audit_events=[generate_valid_event()],
        validation_results=[],
        chain_verification={},
        findings=[],
        severity=None,
        summary=None,
        errors=[],
        retry_count=0,
        max_retries=2,
        metadata={"simulate_analyze_error": "rate_limit", "fail_attempts": 5} # Will fail 5 times, but max_retries=2
    )
    
    result = graph.invoke(state)
    assert len(result["errors"]) == 1
    assert result["retry_count"] == 2
    assert "LLM API Rate Limit" in result["errors"][0]["message"]
    assert result.get("summary") is None

def test_non_retryable_error():
    graph = build_audit_graph()
    state = AuditGraphState(
        audit_events=[generate_valid_event()],
        validation_results=[],
        chain_verification={},
        findings=[],
        severity=None,
        summary=None,
        errors=[],
        retry_count=0,
        max_retries=3,
        metadata={"simulate_analyze_error": "invalid_key", "fail_attempts": 1}
    )
    
    result = graph.invoke(state)
    assert len(result["errors"]) == 1
    assert result["retry_count"] == 0 # Didn't retry
    assert "Invalid API Key" in result["errors"][0]["message"]

def test_tampered_data():
    graph = build_audit_graph()
    event = generate_valid_event()
    event["payload"] = '{"hacked": true}' # Broken hash
    
    state = AuditGraphState(
        audit_events=[event],
        validation_results=[],
        chain_verification={},
        findings=[],
        severity=None,
        summary=None,
        errors=[],
        retry_count=0,
        max_retries=3,
        metadata={}
    )
    
    result = graph.invoke(state)
    assert result["chain_verification"]["status"] == "BROKEN"
    assert result["chain_verification"]["reason"] == "TAMPERED_PAYLOAD"
    assert result.get("summary") is None

def test_invalid_data():
    graph = build_audit_graph()
    event = generate_valid_event()
    del event["actorId"] # Missing required field
    
    state = AuditGraphState(
        audit_events=[event],
        validation_results=[],
        chain_verification={},
        findings=[],
        severity=None,
        summary=None,
        errors=[],
        retry_count=0,
        max_retries=3,
        metadata={}
    )
    
    result = graph.invoke(state)
    assert len(result["errors"]) == 1
    assert result["errors"][0]["node"] == "validate_events"
