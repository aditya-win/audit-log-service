from app.langgraph.state import AuditGraphState

def classify_findings_node(state: AuditGraphState) -> AuditGraphState:
    findings = state.get("findings", [])
    if not findings:
        state["severity"] = "INFO"
    else:
        state["severity"] = "HIGH"
        
    for finding in findings:
        finding["severity"] = "HIGH" if "admin" in finding.get("description", "").lower() else "MEDIUM"
        
    return state
