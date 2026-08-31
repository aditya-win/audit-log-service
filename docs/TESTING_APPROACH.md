# Testing Approach, Limitations, and Trade-Offs

## 1. Testing Approach: What is Covered
Our testing strategy prioritized **cryptographic integrity, data validation, and AI resilience**. The test suite (`tests/`) achieved **93.8% total coverage** across the application.

### Key Coverage Areas:
- **Hash Determinism (`tests/integration/test_hash_chain.py`)**: Tests mathematically prove that identical payloads generate identical hashes, and that modifying *any* field (timestamp, actor, payload) drastically alters the resulting hash.
- **API Guardrails (`tests/integration/test_api.py`)**: Tests ensure Pydantic aggressively rejects oversized payloads (DoS prevention) and invalid event types (422 Unprocessable Entity).
- **LangGraph Resilience (`tests/integration/test_langgraph.py`)**: We explicitly tested the asynchronous retry mechanism. We mocked LLM/Network exceptions to ensure the graph safely loops through the `RetryNode` up to 3 times before failing gracefully.
- **Tamper Detection (`tests/integration/test_tamper_detection.py`)**: Tests simulate direct SQLite mutations (bypassing the API) to prove the verification engine catches `TAMPERED_PAYLOAD` and `BROKEN_CHAIN` states immediately.

## 2. What is NOT Covered & Why (Limitations)
- **High-Concurrency Write Tests**: We did not write multi-threading or stress tests to hammer the API with 1,000+ concurrent appends. 
  * **Why**: The prototype utilizes SQLite. SQLite locks the entire database file on writes, so high concurrency will inherently result in `database is locked` OperationalErrors. Production concurrency testing is deferred until a distributed database (like PostgreSQL) is implemented.
- **Authentication & Authorization (RBAC)**: There are no tests verifying that "User A cannot see User B's audit logs".
  * **Why**: Auth is completely scoped out of this prototype. Adding JWTs and Oauth2 would bloat the implementation away from the core algorithmic challenge (the hash chain and LangGraph).
- **LLM Output Quality (Hallucination Testing)**: We do not assert the exact text of the AI's analysis findings.
  * **Why**: LLM outputs are inherently non-deterministic. We tested the *structure* of the LLM output (forcing JSON schemas via LangChain), but asserting specific contextual text invites flaky tests.

## 3. Core Trade-Offs
- **File-Backed DB vs. Memory DB for Testing**: We initially attempted to run tests against an in-memory SQLite database (`sqlite:///:memory:`). However, FastAPI dependency injection creates new session threads, resulting in isolated memory databases that couldn't share state.
  * **Trade-off**: We traded slightly slower test execution times (by writing tests to a temporary disk file `test_audit.db`) to achieve stability and avoid thread-sharing complexities. 
- **Redaction via Salted Hashing vs. Soft Deletion**: In Scenario B, we chose to hash individual fields to maintain cryptographic commitment during redaction. 
  * **Trade-off**: This drastically increased the complexity of our Canonical JSON logic, but it was the only way to satisfy *both* data privacy and mathematical tamper-evidence simultaneously.
