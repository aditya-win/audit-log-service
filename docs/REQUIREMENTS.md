# Audit Log Service Requirements Analysis

## 1. Functional Requirements
- **Write API (Append-only)**: Accept an event record containing `eventType`, `actorId`, `resourceType`, `resourceId`, `payload`, and `timestamp`.
- **Query API**: Retrieve events with filtering by `actorId`, `resourceType`, and `resourceId`, `eventType`, and time range (`from`/`to`). Support pagination.
- **Tamper Evidence (Hash Chain)**: Each record must include a hash of its own content and a hash of the preceding record (or genesis value).
- **Chain Verification Endpoint**: Expose `GET /audit/verify` that walks the chain, reports if intact, and if broken, indicates the first inconsistency and violation type.
- **Retention Policy (Scenario B)**: Support configurable archival/soft-deletion of older records without breaking chain verification.
- **Structured Redaction (Scenario B)**: Support redactable fields within payloads for data privacy while maintaining tamper-evidence.
- **Bulk Export (Scenario B)**: Export all records for a `resourceId` or `actorId` as a verifiable bundle including chain metadata.
- **Compliance Reporting (Scenario C)**: Provide auditing of access to client account data (clarification needed).

## 2. Non-functional Requirements
- **Technology Stack**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite, LangGraph.
- **Integrity**: Cryptographic verification must be deterministic Python logic; no LLM involvement in hash validation.
- **Resilience**: Implement intelligent retry mechanisms for transient failures using LangGraph.
- **Performance**: Support large result sets via pagination.

## 3. Ambiguous Requirements (Ambiguity Matrix)
| Requirement | Ambiguity | Clarification / Action |
|-------------|-----------|------------------------|
| Timestamp | Caller-supplied vs server-assigned. | Assume server-assigned for integrity, with optional caller timestamp inside payload. |
| Scenario C Access Audit | "Regulators need to be able to audit access to client account data." is under-specified. | Requires definition of what constitutes an "access" event, required fields, and specific regulatory reporting format. |
| Redaction | "without breaking the hash chain" | Will need a cryptographic commitment scheme (e.g., salting/hashing the redacted field separately). |

## 4. Assumptions
- SQLite is sufficient for the prototype as per assignment scope.
- Redis is not required as LangGraph can manage state in-memory or in SQLite for this scale.
- A single genesis record per database/chain is sufficient.

## 5. Scenario A: Greenfield Core Service
- Implement core Write API, Query API, hash chain logic, and `GET /audit/verify`.
- Develop synthetic log generator to simulate traffic.
- Develop tamper database script to demonstrate detection.

## 6. Scenario B: Retention and Redaction
- Implement retention (archival/soft-delete) handling in verification.
- Implement field-level redaction using a cryptographic commitment approach.
- Implement bulk export endpoint.

## 7. Scenario C: Compliance Reporting
- Normalize "audit access to client account data" requirement.
- Determine if existing service can handle this via specific `eventType` (e.g., `DATA_ACCESS`).

## 8. Acceptance Criteria
- Write API successfully stores events.
- Query API successfully filters and paginates.
- Chain verification returns valid for untouched chains.
- Chain verification correctly identifies tampered records (via script).
- Transient errors in LangGraph are retried; non-transient fail immediately.

## 9. Security Requirements
- Deterministic canonicalization for hashing.
- No update or delete endpoints exposed.
- Protection against SQL injection (handled via SQLAlchemy).
- Input validation (handled via Pydantic).
- Redaction scheme must prevent reverse-engineering of sensitive data.

## 10. Testing Requirements
- Unit tests for Pydantic schemas, hashing, canonicalization.
- Integration tests for FastAPI endpoints, filtering, pagination.
- Testing of LangGraph retry behavior (success, transient failure, exhaustion).
- Tamper detection tests.

## 11. Documentation Requirements
- `README.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md`, `API.md`, `THREAT_MODEL.md`.
- Specific scenario docs (`SCENARIO_A.md`, `SCENARIO_B.md`, `SCENARIO_C.md`).
- `FINAL_ENGINEERING_SUMMARY.md`.

## 12. AI Traceability Requirements
- Complete log of AI usage in `ai/AI_USAGE_LOG.md` and `ai/PROMPT_LOG.md`.
- `ATTESTATION.md` file signed by the author.
- Clear commit history showing the iterative development process.

## 13. Implementation Order
1. Initialization (FastAPI setup).
2. Pydantic schemas.
3. Database and Hash Chain core logic (SQLAlchemy).
4. REST APIs.
5. Synthetic Log Generator & Tampering scripts.
6. LangGraph integration & Retry mechanism.
7. Scenario B (Retention, Redaction, Export).
8. Scenario C (Compliance Reporting analysis/implementation).
9. Security & Testing.
10. Documentation.
