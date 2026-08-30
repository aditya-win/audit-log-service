import hashlib
from typing import Dict, Any
from datetime import datetime, timezone
from app.utils.canonical_json import to_canonical_json

GENESIS_HASH = "0" * 64

def calculate_hash(event_type: str, actor_id: str, resource_type: str, resource_id: str, payload_str: str, timestamp: datetime, previous_hash: str) -> str:
    """
    Calculate the SHA-256 hash of an audit event deterministically.
    """
    # Ensure timestamp is UTC and normalized to ISO 8601 string
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    ts_str = timestamp.astimezone(timezone.utc).isoformat()
    
    # We create a dictionary to canonicalize the entire event to hash it
    # We do NOT hash python objects directly
    event_data = {
        "event_type": event_type,
        "actor_id": actor_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "payload": payload_str,
        "timestamp": ts_str,
        "previous_hash": previous_hash
    }
    
    canonical_string = to_canonical_json(event_data)
    return hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()
