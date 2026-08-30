from app.langgraph.state import AuditGraphState
from app.utils.hashing import calculate_hash, GENESIS_HASH

def verify_chain_node(state: AuditGraphState) -> AuditGraphState:
    events = state.get("audit_events", [])
    expected_prev = GENESIS_HASH
    
    for event in events:
        if event.get("previous_hash") != expected_prev:
            state["chain_verification"] = {"status": "BROKEN", "reason": "HASH_MISMATCH", "recordId": event.get("id")}
            state["errors"].append({"node": "verify_chain", "message": "Cryptographic integrity failure."})
            return state
            
        calc_hash = calculate_hash(
            event_type=event.get("event_type", event.get("eventType")),
            actor_id=event.get("actor_id", event.get("actorId")),
            resource_type=event.get("resource_type", event.get("resourceType")),
            resource_id=event.get("resource_id", event.get("resourceId")),
            payload_str=event.get("payload", "{}"),
            timestamp=event.get("timestamp"),
            previous_hash=event.get("previous_hash")
        )
        
        if event.get("current_hash") != calc_hash:
            state["chain_verification"] = {"status": "BROKEN", "reason": "TAMPERED_PAYLOAD", "recordId": event.get("id")}
            state["errors"].append({"node": "verify_chain", "message": "Cryptographic integrity failure."})
            return state
            
        expected_prev = event.get("current_hash")
        
    state["chain_verification"] = {"status": "INTACT"}
    return state
