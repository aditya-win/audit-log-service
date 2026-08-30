import random
from app.langgraph.state import AuditGraphState
from app.langgraph.retry_policy import TransientFailureError, NonRetryableError

def analyze_events_node(state: AuditGraphState) -> AuditGraphState:
    try:
        # Check if we should simulate an LLM transient failure based on metadata
        simulate_error = state.get("metadata", {}).get("simulate_analyze_error")
        if simulate_error == "timeout":
            raise TransientFailureError("LLM API Timeout")
        elif simulate_error == "rate_limit":
            raise TransientFailureError("LLM API Rate Limit 429")
        elif simulate_error == "invalid_key":
            raise NonRetryableError("Invalid API Key")

        findings = []
        for event in state.get("audit_events", []):
            if event.get("eventType") == "PERMISSION_GRANTED" and event.get("actorId") == "admin":
                findings.append({
                    "recordId": event.get("id"),
                    "description": "Admin granted permissions directly."
                })
        
        state["findings"] = findings
        return state
        
    except Exception as e:
        state["last_failed_node"] = "analyze_events"
        state["errors"].append({"node": "analyze_events", "message": str(e), "error_obj": e})
        return state
