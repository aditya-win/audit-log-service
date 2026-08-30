import json
from typing import Any

def to_canonical_json(data: Any) -> str:
    """
    Serialize data to a deterministic, canonical JSON string.
    Keys are sorted, and no extra spaces are added.
    """
    return json.dumps(data, separators=(',', ':'), sort_keys=True)
