import json
import httpx
import argparse
import time

def inject_logs(file_path: str, api_url: str):
    print(f"Loading logs from {file_path}...")
    with open(file_path, 'r') as f:
        logs = json.load(f)
        
    print(f"Found {len(logs)} logs. Injecting into {api_url}...")
    
    success_count = 0
    headers = {"X-API-Key": "super-secret-key-123"}
    with httpx.Client(headers=headers) as client:
        for i, log in enumerate(logs):
            try:
                response = client.post(api_url, json=log)
                if response.status_code == 201:
                    success_count += 1
                elif response.status_code == 422:
                    # Intentionally malformed (Scenario MIXED)
                    pass
                else:
                    print(f"Failed to inject log {i}: {response.text}")
            except Exception as e:
                print(f"Connection error on log {i}: {e}")
                
    print(f"\nSuccessfully injected {success_count}/{len(logs)} logs.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject generated logs into the API")
    parser.add_argument("--file", type=str, default="test_logs.json", help="Path to the JSON file")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8000/audit", help="API URL to post to")
    
    args = parser.parse_args()
    inject_logs(args.file, args.url)
