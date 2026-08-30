from app.langgraph.state import AuditGraphState

def load_events_node(state: AuditGraphState) -> AuditGraphState:
    # In a real app, this might load from a DB if state["audit_events"] is empty
    # For now, we assume events are injected into the initial state
    if not state.get("audit_events"):
        state["errors"].append({"node": "load_events", "message": "No events provided."})
    return state
