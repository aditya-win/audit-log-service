from typing import TypedDict, List, Dict, Any, Optional

class AuditGraphState(TypedDict):
    audit_events: List[Dict[Any, Any]]
    validation_results: List[Dict[str, Any]]
    chain_verification: Dict[str, Any]
    findings: List[Dict[str, Any]]
    severity: Optional[str]
    summary: Optional[str]
    errors: List[Dict[str, Any]]
    retry_count: int
    max_retries: int
    metadata: Dict[str, Any]
    last_failed_node: Optional[str]  # Internal tracking for retry routing
