import argparse
import json
import random
from datetime import datetime, timedelta, timezone

def generate_valid(seed_random, index, base_time=None):
    if base_time is None:
        base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        
    event_types = ["USER_LOGIN", "RECORD_UPDATED", "PERMISSION_GRANTED", "DATA_ACCESS"]
    return {
        "eventType": seed_random.choice(event_types),
        "actorId": f"actor-{seed_random.randint(1, 100)}",
        "resourceType": "system",
        "resourceId": f"res-{seed_random.randint(1, 500)}",
        "payload": {"status": "success", "index": index},
        "timestamp": (base_time - timedelta(minutes=seed_random.randint(1, 1000))).isoformat()
    }

def generate_invalid(seed_random, index):
    base = generate_valid(seed_random, index)
    flaw_type = seed_random.choice([
        "missing_actorId", "invalid_timestamp", "unknown_event_type", "oversized_payload", "future_timestamp"
    ])
    
    if flaw_type == "missing_actorId":
        del base["actorId"]
    elif flaw_type == "invalid_timestamp":
        base["timestamp"] = "not-a-date"
    elif flaw_type == "unknown_event_type":
        base["eventType"] = "UNKNOWN_OR_BAD"
    elif flaw_type == "oversized_payload":
        base["payload"] = {"data": "x" * 15000}
    elif flaw_type == "future_timestamp":
        base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        base["timestamp"] = (base_time + timedelta(days=5)).isoformat()
        
    return base

def generate_edge_case(seed_random, index):
    base = generate_valid(seed_random, index)
    edge_type = seed_random.choice([
        "unicode", "empty_payload", "large_valid", "identical"
    ])
    
    if edge_type == "unicode":
        base["payload"] = {"msg": "Hello \u4f60\u597d"}
    elif edge_type == "empty_payload":
        base["payload"] = {}
    elif edge_type == "large_valid":
        base["payload"] = {"data": "x" * 5000}
    elif edge_type == "identical":
        # Deterministically same as index 0
        return generate_valid(random.Random(0), 0)
        
    return base

def generate_suspicious(seed_random, index):
    base = generate_valid(seed_random, index)
    base["eventType"] = "PERMISSION_GRANTED"
    base["actorId"] = "admin"
    base["payload"] = {"reason": "bypass", "risk": "high", "ip": "10.0.0.99"}
    return base

def generate_logs(count: int, seed: int, scenario: str):
    seed_random = random.Random(seed)
    logs = []
    
    for i in range(count):
        if scenario == "VALID":
            logs.append(generate_valid(seed_random, i))
        elif scenario == "INVALID":
            logs.append(generate_invalid(seed_random, i))
        elif scenario == "EDGE_CASE":
            logs.append(generate_edge_case(seed_random, i))
        elif scenario == "SUSPICIOUS":
            logs.append(generate_suspicious(seed_random, i))
        elif scenario == "MIXED":
            choice = seed_random.choices(
                ["VALID", "INVALID", "EDGE_CASE", "SUSPICIOUS"],
                weights=[70, 10, 10, 10]
            )[0]
            if choice == "VALID":
                logs.append(generate_valid(seed_random, i))
            elif choice == "INVALID":
                logs.append(generate_invalid(seed_random, i))
            elif choice == "EDGE_CASE":
                logs.append(generate_edge_case(seed_random, i))
            elif choice == "SUSPICIOUS":
                logs.append(generate_suspicious(seed_random, i))
                
    return logs

def main():
    parser = argparse.ArgumentParser(description="Synthetic Audit Log Generator")
    parser.add_argument("--count", type=int, default=10, help="Number of records to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation")
    parser.add_argument("--scenario", type=str, choices=["VALID", "INVALID", "EDGE_CASE", "SUSPICIOUS", "MIXED"], default="VALID")
    parser.add_argument("--output", type=str, help="Output JSON file path (prints to stdout if omitted)")
    
    args = parser.parse_args()
    
    logs = generate_logs(args.count, args.seed, args.scenario)
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(logs, f, indent=2)
    else:
        print(json.dumps(logs, indent=2))

if __name__ == "__main__":
    main()
