# Audit Log Service

A tamper-evident, chronologically secure audit logging service built with FastAPI, Pydantic, SQLAlchemy, and LangGraph.

This project implements a cryptographically verifiable append-only audit log. It ensures that any tampering (payload modifications, missing records, or altered hashes) is mathematically detectable. Additionally, it features an intelligent LangGraph-powered AI analysis workflow to asynchronously inspect audit records for suspicious activities with robust retry mechanisms for transient failures.

## Features

- **Append-Only Deterministic Hash Chain**: Every event is cryptographically linked to the previous event using a canonical SHA-256 hash.
- **Data Privacy & Redaction**: Supports structured redaction using cryptographic commitments (salted field hashes), allowing sensitive data removal without invalidating the chain's integrity.
- **Archival/Retention**: Allows minimizing storage by securely archiving payloads while retaining verifiable chain links.
- **AI-Powered Analysis**: Integrates LangGraph to execute autonomous findings and reporting workflows on audit records, strictly sandboxed from modifying the chain.
- **Tamper Evidence**: Fully automated verification logic that mathematically guarantees the data has not been secretly mutated.

## Technology Stack
- **Web Framework**: FastAPI
- **Data Validation**: Pydantic v2
- **Database**: SQLite & SQLAlchemy (ORM)
- **AI Agent Workflow**: LangGraph
- **Testing**: Pytest & Pytest-Cov

---

## Setup Instructions

1. **Clone the repository** and navigate to the root directory.

2. **Create and activate a virtual environment**:
   ```powershell
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```
   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   pip install pytest pytest-cov
   ```

4. **Run the Test Suite (Ensures 90%+ Coverage)**:
   ```powershell
   pytest
   ```

5. **Start the API Server**:
   ```powershell
   fastapi dev app/main.py
   ```
   The API will be available at `http://127.0.0.1:8000`. API documentation is available at `http://127.0.0.1:8000/api/v1/docs`.

---

## Architecture Summary

1. **API Layer (`app/api/`)**: FastAPI routes strictly handle validation and request shaping using strict Pydantic schemas. Destructive REST operations (`PUT`, `DELETE`) are intentionally omitted to enforce append-only rules.
2. **Business & Verification Layer (`app/services/`)**: Centralized coordination. The `VerificationService` re-computes hashes from the raw data and compares them to the stored chain to prove data integrity.
3. **Data Access Layer (`app/repositories/`)**: SQLAlchemy handles database abstractions.
4. **Agent Workflow (`app/langgraph/`)**: A LangGraph state machine handles event processing, vulnerability classification, and summary generation. It employs intelligent retry nodes for handling transient network or LLM failures (e.g., rate limits, timeouts) while failing instantly on non-retryable logical errors.

---

## Developer Scripts

### 1. Run the Synthetic Generator
Use the synthetic generator to deterministically seed the database with valid, invalid, suspicious, or edge-case payloads.
```powershell
# Generates 50 logs using a deterministic seed and prints to stdout
python -m scripts.generate_logs --count 50 --seed 42 --scenario MIXED

# Or pipe them to a file
python -m scripts.generate_logs --count 100 --seed 1 --scenario VALID --output logs.json
```

### 2. Run the Tamper Demonstration
This script demonstrates the tamper-evident properties of the system. It simulates an attacker bypassing the API to directly modify SQLite data, and shows how the verification engine instantly catches the breach.
```powershell
python -m scripts.verify_demo
```

### 3. Generate a Compliance Report
Extracts an auditor-ready Markdown or JSON report verifying chain integrity and summarizing `DATA_ACCESS` events for a specific client.
```powershell
# Markdown format (default)
python -m scripts.compliance_report --client-id client-123

# JSON format
python -m scripts.compliance_report --client-id client-123 --format json
```

---

## Security Notes & Limitations

- **Authentication / RBAC**: We have secured all endpoints using `X-API-Key` authentication. However, in a full production environment, this should be upgraded to strict Role-Based Access Control (RBAC) (e.g., JWT, OAuth2) to ensure fine-grained resource ownership (e.g., tenant boundaries) and auditor-specific roles.
- **Hash Collisions**: SHA-256 is currently secure against collision attacks. However, no hash algorithm is permanently immune to advances in cryptanalysis or quantum computing. 
- **Chain Truncation**: While the hash chain prevents in-place tampering, it cannot inherently prevent a malicious DBA from truncating the database (deleting the last N records). Production systems must anchor the latest `current_hash` to external immutable ledgers or time-stamping authorities periodically to prevent truncation attacks.
- **Rate Limiting**: The API lacks rate limiting, making it vulnerable to Denial of Service (DoS) attacks designed to exhaust SQLite write locks or storage.