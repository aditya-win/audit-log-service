from app.langgraph.state import AuditGraphState

def validate_events_node(state: AuditGraphState) -> AuditGraphState:
    results = []
    has_invalid = False
    
    for event in state.get("audit_events", []):
        if not event.get("actorId") or not event.get("eventType"):
            results.append({"id": event.get("id"), "valid": False, "reason": "Missing required fields"})
            has_invalid = True
        else:
            results.append({"id": event.get("id"), "valid": True})
            
    state["validation_results"] = results
    
    if has_invalid:
        state["errors"].append({"node": "validate_events", "message": "One or more events are malformed."})
        
    return state
