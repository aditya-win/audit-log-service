# Live Defense Demonstration Guide

Use this step-by-step guide during your live review session to demonstrate that all scenarios (A, B, and C) work perfectly.

## Step 0: Start the Environment
Ensure your Docker container is running.
**Input (Terminal):**
```cmd
docker-compose up -d --build
```
**Process:** Docker builds the FastAPI app, configures SQLAlchemy, and initializes a fresh SQLite volume.
**Output:** Docker shows `Started audit-api`. You can view the swagger UI at `http://127.0.0.1:8000/docs`.

---

## Scenario A: Core Audit Service & Tamper Evidence

### 1. Generate & Inject Logs
**Input (Terminal):**
```cmd
python -m scripts.generate_logs --count 20 --seed 42 --scenario VALID --output test_logs.json
python -m scripts.inject_logs --file test_logs.json --url http://127.0.0.1:8000/audit
```
**Process:** Generates 20 deterministic JSON payloads and POSTs them to the FastAPI server. Pydantic validates them, and the `VerificationService` calculates the SHA-256 chain.
**Output:** `Successfully injected 20/20 logs.`

### 2. Verify the Intact Chain
**Input (Terminal or Browser):**
```cmd
curl -H "X-API-Key: super-secret-key-123" http://127.0.0.1:8000/audit/verify
```
**Process:** The server recalculates every hash in the database and compares it to the stored `current_hash`.
**Output:** `{"status":"INTACT","error":null}`

### 3. Demonstrate Tamper Detection
**Input (Terminal):**
```cmd
python -m scripts.verify_demo
```
**Process:** This script creates an isolated demo database, inserts 5 logs, and then directly hacks the SQLite database (changing an `actor_id` to `hacker`) without updating the hash.
**Output:** The verification catches it instantly!
```text
Status: BROKEN
Tampering successfully detected!
  First inconsistent record ID: 3
  Violation type: TAMPERED_PAYLOAD
```

---

## Scenario B: Redaction and Archival

### 1. Test Structured Redaction
We want to redact sensitive data from Record ID #1 without breaking its hash.
**Input (PowerShell):**
```powershell
# Redact the 'action' field from Record 1
Invoke-RestMethod -Uri "http://127.0.0.1:8000/audit/1/redact" -Method Post -Headers @{"X-API-Key"="super-secret-key-123"} -Body '["action"]' -ContentType "application/json"
```
*(If using `cmd`, you can do this via the Swagger UI at `http://127.0.0.1:8000/docs`)*
**Process:** The system deletes the `action` value from the payload and stores its individual hash in `redacted_fields`.
**Output (Run Verification again):** 
```cmd
curl -H "X-API-Key: super-secret-key-123" http://127.0.0.1:8000/audit/verify
```
-> `{"status":"INTACT","error":null}` (The chain is unbroken despite data removal!)

### 2. Test Bulk Export
Export all records related to a specific actor.
**Input (Terminal):**
```cmd
curl -H "X-API-Key: super-secret-key-123" http://127.0.0.1:8000/audit/export/bundle?actorId=actor-82
```
**Process:** The system extracts all records where `actor_id == actor-82` and bundles them with their cryptographic signatures.
**Output:** A massive JSON bundle of verified records.

---

## Scenario C: Compliance Reporting

### 1. Run the Auditor Script
An internal auditor needs to see all `DATA_ACCESS` events for client account `res-216`.
**Input (Terminal):**
```cmd
python -m scripts.compliance_report --client-id res-216
```
**Process:** The Python script connects directly to the DB, verifies the global hash chain FIRST (to ensure the data is trustworthy), then extracts and groups the specific client's data.
**Output (Markdown Report):**
```markdown
# Compliance Report: Data Access for Client `res-216`
**Chain Integrity Status:** `INTACT`

**Total Access Events:** 1

## Actor: `actor-82`
- **Total accesses:** 1
  - `[2024-12-31T23:59:00]` Event ID: 24 
```
