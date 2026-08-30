from app.langgraph.state import AuditGraphState

def generate_report_node(state: AuditGraphState) -> AuditGraphState:
    events_processed = len(state.get("audit_events", []))
    findings_count = len(state.get("findings", []))
    severity = state.get("severity", "INFO")
    
    state["summary"] = f"Processed {events_processed} events. Found {findings_count} issues. Overall severity: {severity}."
    return state
