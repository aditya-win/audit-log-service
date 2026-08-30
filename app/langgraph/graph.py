from langgraph.graph import StateGraph, END
from app.langgraph.state import AuditGraphState
from app.langgraph.retry_policy import is_retryable
from app.langgraph.nodes.load_events import load_events_node
from app.langgraph.nodes.validate_events import validate_events_node
from app.langgraph.nodes.verify_chain import verify_chain_node
from app.langgraph.nodes.analyze_events import analyze_events_node
from app.langgraph.nodes.classify_findings import classify_findings_node
from app.langgraph.nodes.generate_report import generate_report_node
from app.langgraph.nodes.retry import retry_node

def check_validation(state: AuditGraphState):
    if state.get("errors"):
        return "error_end"
    return "verify_chain"

def check_integrity(state: AuditGraphState):
    if state.get("chain_verification", {}).get("status") == "BROKEN":
        return "error_end"
    return "analyze_events"

def check_analysis_retry(state: AuditGraphState):
    if state.get("errors") and state.get("last_failed_node") == "analyze_events":
        last_error = state["errors"][-1]
        error_obj = last_error.get("error_obj")
        
        if is_retryable(error_obj) and state.get("retry_count", 0) < state.get("max_retries", 3):
            return "retry"
        else:
            return "error_end"
            
    return "classify_findings"

def build_audit_graph():
    workflow = StateGraph(AuditGraphState)
    
    workflow.add_node("load_events", load_events_node)
    workflow.add_node("validate_events", validate_events_node)
    workflow.add_node("verify_chain", verify_chain_node)
    workflow.add_node("analyze_events", analyze_events_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("classify_findings", classify_findings_node)
    workflow.add_node("generate_report", generate_report_node)
    
    workflow.set_entry_point("load_events")
    workflow.add_edge("load_events", "validate_events")
    
    workflow.add_conditional_edges(
        "validate_events",
        check_validation,
        {
            "verify_chain": "verify_chain",
            "error_end": END
        }
    )
    
    workflow.add_conditional_edges(
        "verify_chain",
        check_integrity,
        {
            "analyze_events": "analyze_events",
            "error_end": END
        }
    )
    
    workflow.add_conditional_edges(
        "analyze_events",
        check_analysis_retry,
        {
            "retry": "retry",
            "classify_findings": "classify_findings",
            "error_end": END
        }
    )
    
    workflow.add_edge("retry", "analyze_events")
    workflow.add_edge("classify_findings", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()
