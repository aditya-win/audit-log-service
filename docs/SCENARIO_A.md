# Scenario A: Greenfield Core Audit Log Service

## 1. Requirement Decomposition
The core requirement was to build an append-only, tamper-evident audit log service. This was broken down into the following distinct tasks:
- **Task 1: API & Data Modeling:** Define strict Pydantic schemas for `AuditEventCreate` and `AuditEventResponse`.
- **Task 2: Database Layer:** Implement SQLAlchemy ORM with an `audit_events` table (SQLite for prototype).
- **Task 3: Deterministic Hashing:** Implement a Canonical JSON serializer to ensure unordered JSON payloads hash consistently across different architectures.
- **Task 4: The Hash Chain:** Link each event to the previous event using a cryptographic `previous_hash` to ensure historical immutability.
- **Task 5: Chain Verification:** Expose a `GET /audit/verify` endpoint that re-traverses the database and recalculates all hashes to prove data integrity.

## 2. Execution & Implementation
- **Framework:** FastAPI was chosen over Flask for its native Pydantic validation and asynchronous routing capabilities.
- **Append-Only Enforcement:** REST `PUT` and `DELETE` endpoints were intentionally omitted. The data repository only exposes `append_event` and retrieval functions.
- **Hash Engine:** `app/utils/hashing.py` handles the SHA-256 generation. It forces all timestamps to a strict UTC ISO-8601 format before hashing to prevent timezone-related deterministic failures.

## 3. Validation & Testing
- **Unit & Integration Tests:** Over 50 Pytest cases were written to validate validation boundaries (e.g., oversized payloads) and chain integrity.
- **Tamper Demonstration Script:** We built `scripts/verify_demo.py` to mathematically prove the system works. This script:
  1. Generates a valid hash chain.
  2. Directly edits an `actor_id` in the SQLite database (bypassing the API).
  3. Re-runs the verification engine, successfully catching the `TAMPERED_PAYLOAD` and flagging the chain as `BROKEN`.
- **Code Coverage:** The execution of Scenario A achieved >90% test coverage across the API, Service, and Repository layers.
