# Architecture Decision Record and Design

## 1. Components
The system follows a layered architecture to separate concerns, maintain testability, and ensure cryptographic determinism.

- **FastAPI API Layer**: Exposes REST endpoints (`/audit`, `/audit/{id}`, `/audit/verify`). Handles HTTP requests, responses, and status codes.
- **Pydantic Schema Layer**: Defines strongly-typed request and response schemas (e.g., `AuditEventCreate`, `AuditEventResponse`). Ensures strict data validation before reaching the service layer.
- **Dependency Injection Layer**: Manages the lifecycle and injection of database sessions, services, and repositories into the API layer.
- **Service / Business Layer**: Contains core business logic. Coordinates repositories, hash chain generation, and external workflows. 
- **Repository Layer**: Abstracts database operations. Provides a clean interface for querying and persisting data using SQLAlchemy.
- **SQLAlchemy Models**: Defines the database tables (`AuditEvent`) and relationships.
- **Hash-Chain Integrity Layer**: Pure Python logic that serializes event payloads into canonical JSON and hashes them with SHA-256 to create a deterministic hash chain.
- **Verification Layer**: Walks the database to ensure the hash chain is unbroken. Detects and reports the first inconsistency.
- **Retention Layer (Scenario B)**: Handles soft-deletion or archival of old records.
- **Redaction Layer (Scenario B)**: Implements field-level redaction using a cryptographic commitment so the original hash remains valid.
- **Export Layer (Scenario B)**: Handles packaging records with verifiable metadata for bulk export.
- **Synthetic Log Generator**: A separate component/script that deterministically generates valid, invalid, edge-case, and suspicious audit events for testing and demonstration.
- **LangGraph Audit Workflow**: Orchestrates the multi-step process of loading, validating, verifying, and analyzing events (using an LLM).
- **Retry Mechanism**: Integrated within LangGraph. Intelligently retries transient failures (e.g., LLM rate limits) while immediately failing on deterministic issues (e.g., hash mismatch).

## 2. Data Flow
1. **Ingestion**: Client `POST`s an event -> FastAPI Route -> Pydantic Validation -> `AuditService` -> `HashChainService` (calculates hash) -> `AuditRepository` -> SQLite DB.
2. **Retrieval**: Client `GET`s events -> FastAPI Route -> `AuditService` -> `AuditRepository` -> Returns mapped Pydantic models.
3. **Verification**: Client `GET`s `/audit/verify` -> FastAPI Route -> `VerificationService` -> Iterates through DB records -> Calculates expected hashes -> Compares with stored hashes -> Returns status.
4. **LangGraph Processing**: `Load Events` -> `Validate Structure` -> `Chain Verification` (deterministic) -> `Analyze Events` (LLM) -> (Retry if transient failure) -> `Classify Findings` -> `Generate Report`.

## 3. Database Schema
**Table: `audit_events`**
- `id`: Integer, Primary Key, Auto-increment
- `event_type`: String, Indexed
- `actor_id`: String, Indexed
- `resource_type`: String, Indexed
- `resource_id`: String, Indexed
- `payload`: JSON (stored as String in SQLite)
- `timestamp`: DateTime, Indexed
- `previous_hash`: String (SHA-256)
- `current_hash`: String (SHA-256)

## 4. API Contracts
- `POST /audit`: Accepts `AuditEventCreate`. Returns `AuditEventResponse`.
- `GET /audit`: Accepts query params (`actorId`, `resourceType`, etc.). Returns Paginated `AuditEventResponse`.
- `GET /audit/{id}`: Returns `AuditEventResponse`.
- `GET /audit/verify`: Returns `VerificationResponse` (Status: `INTACT` | `BROKEN`, details if broken).

## 5. Dependency Boundaries
- The **API Layer** depends on the **Service Layer** and **Schema Layer**. It does *not* interact directly with the DB.
- The **Service Layer** depends on the **Repository Layer** and the **Integrity Layer**.
- The **LangGraph Workflow** is invoked as a background or separate process, depending on the **Service Layer** for deterministic checks, but managing its own state.
- **Cryptographic Verification** is strictly isolated from LLMs.

## 6. Security Boundaries
- **Validation**: Pydantic drops all unknown fields and enforces types at the perimeter.
- **Immutability**: No `PUT`, `PATCH`, or `DELETE` endpoints are exposed.
- **Canonicalization**: Payloads are sorted and stripped of whitespace before hashing to prevent identical data from having different hashes.

## 7. Retry Boundaries
- **Retryable (Transient)**: Network timeouts, LLM API rate limits (HTTP 429), temporary DB locks.
- **Non-Retryable (Deterministic)**: Invalid schema (HTTP 422), broken hash chain, unauthorized access, missing fields.
- **Implementation**: LangGraph conditional edges check the error type. Transient errors increment a `retry_count`. If `retry_count < 3`, it loops back; otherwise, it moves to an `Error Node`.

## 8. Testing Boundaries
- **Unit Tests**: Test Pydantic schemas, canonical JSON serialization, hashing algorithms, and individual LangGraph nodes.
- **Integration Tests**: Test FastAPI endpoints (using `TestClient`), database persistence, and full chain verification over SQLite.
- **Security Tests**: Scripted tampering of SQLite DB to prove the verification endpoint catches mutations.

## 9. SQLite Limitations
- **Concurrency**: SQLite locks the whole database for writes. Given the append-only nature of this service, a single writer should be used, or the `AuditRepository` must handle `sqlite3.OperationalError: database is locked` gracefully (potentially via the retry mechanism).
- **JSON Support**: SQLite has JSON functions, but we will store canonicalized JSON as strings to guarantee hash consistency across different environments.
- **Scale**: SQLite is fine for prototype/demonstration, but a production system would require PostgreSQL for concurrent appends and advanced JSONB indexing.
