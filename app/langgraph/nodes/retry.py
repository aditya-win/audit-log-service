from app.langgraph.state import AuditGraphState
from app.langgraph.retry_policy import is_retryable

def retry_node(state: AuditGraphState) -> AuditGraphState:
    state["retry_count"] = state.get("retry_count", 0) + 1
    state["errors"].pop() # Clear the transient error so we can retry cleanly
    
    metadata = state.get("metadata", {})
    if "fail_attempts" in metadata:
        metadata["fail_attempts"] -= 1
        if metadata["fail_attempts"] <= 0:
            metadata["simulate_analyze_error"] = None
            
    return state
