import hashlib
import hmac
from typing import Dict, Any
from datetime import datetime, timezone
from app.utils.canonical_json import to_canonical_json
from app.config import settings

GENESIS_HASH = "0" * 64

def compute_payload_commitment(payload_str: str, redacted_fields_str: str = None) -> str:
    import json
    payload = json.loads(payload_str) if payload_str else {}
    redacted = json.loads(redacted_fields_str) if redacted_fields_str else {}
    
    field_hashes = {}
    salt_bytes = settings.redaction_salt.encode('utf-8')
    for k, v in payload.items():
        if k in redacted:
            # It's redacted, use the stored hash
            field_hashes[k] = redacted[k]
        else:
            # It's plaintext, hash its string representation using HMAC and our salt
            val_str = str(v)
            field_hashes[k] = hmac.new(salt_bytes, val_str.encode('utf-8'), hashlib.sha256).hexdigest()
            
    # Include any redacted fields that were completely removed from payload
    for k, h in redacted.items():
        if k not in field_hashes:
            field_hashes[k] = h
            
    return hashlib.sha256(to_canonical_json(field_hashes).encode('utf-8')).hexdigest()

def calculate_hash(event_type: str, actor_id: str, resource_type: str, resource_id: str, payload_str: str, timestamp: datetime, previous_hash: str, redacted_fields: str = None) -> str:
    """
    Calculate the SHA-256 hash of an audit event deterministically.
    
    SECURITY LIMITATION:
    - Hash Collisions: While SHA-256 is currently cryptographically secure against collision attacks, 
      advances in cryptanalysis could theoretically weaken it over decades.
    - Quantum Vulnerability: SHA-256 is not theoretically immune to Grover's algorithm on a sufficiently large 
      quantum computer, though its 256-bit output currently maintains adequate security margins (effective 128-bit).
    """
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    ts_str = timestamp.astimezone(timezone.utc).isoformat()
    
    payload_hash = compute_payload_commitment(payload_str, redacted_fields)
    
    event_data = {
        "event_type": event_type,
        "actor_id": actor_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "payload_hash": payload_hash,
        "timestamp": ts_str,
        "previous_hash": previous_hash
    }
    
    canonical_string = to_canonical_json(event_data)
    return hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()
