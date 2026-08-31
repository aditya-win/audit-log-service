# AI Usage & Traceability Log

This document satisfies the requirement for AI traceability, explaining how AI was utilized to build this system, what was accepted, modified, or rejected, and the overarching governance applied.

## Process Overview
This project was built using an AI-assisted pair-programming approach (via AI coding agents/assistants). 
The process followed a strict **Engineer-Led, AI-Accelerated** model:
1. **Engineer Intent:** The engineer defined the architecture, stack choices (FastAPI, SQLite, Pydantic, LangGraph), and exact constraints (e.g., deterministic JSON serialization, zero AI involvement in hash validation).
2. **AI Execution:** The AI generated boilerplate, implemented repetitive ORM models, drafted unit tests, and stubbed documentation based on the engineer's prompts.
3. **Engineer Review:** Every output was reviewed. AI hallucinations or logic gaps were caught by the engineer and iteratively refined through subsequent prompts.

## Key Traceability Notes

### 1. Architectural Setup & Hashing
- **Prompted:** Create a FastAPI base with a deterministic SHA-256 hashing utility.
- **Accepted:** The basic `calculate_hash` function and Pydantic schema validation.
- **Modified/Corrected:** The AI initially did not account for timezone-aware versus naive datetimes in the hash serialization, which would break determinism across different machines. The engineer directed the AI to enforce strict UTC `isoformat()` strings for all timestamps before hashing.

### 2. Scenario B (Redaction)
- **Prompted:** Implement a redaction strategy that preserves tamper evidence.
- **Rejected:** The AI initially suggested simply deleting the payload and recalculating the hash. This was rejected because recalculating a historical hash breaks the entire chain (the core problem of redaction).
- **Accepted (After Guidance):** The engineer conceptualized the "Cryptographic Commitment" approach (salting and hashing individual fields, storing the hashes in a `redacted_fields` dictionary). The AI successfully wrote the complex dictionary traversal code to implement this design.

### 3. LangGraph Agent (Analysis)
- **Prompted:** Create a state machine using LangGraph to analyze audit logs asynchronously.
- **Modified:** The AI generated a basic graph, but state updates were failing because Pydantic ignores fields starting with underscores (e.g., `_last_failed_node`). The engineer caught this framework-specific gotcha and instructed the AI to rename the internal state variables to fix the bug.
- **Accepted:** The AI successfully built the `retry_node` logic to handle transient LLM failures up to 3 times, demonstrating excellent resilience.

### 4. Testing & Code Coverage
- **Prompted:** Write tests to ensure 90%+ code coverage across the API, Hashing, and LangGraph layers.
- **Accepted:** The AI generated 50+ robust Pytest unit and integration tests.
- **Modified:** The AI-generated test for the Tamper Demonstration script failed on Windows due to an SQLite file locking issue (`PermissionError`). The engineer directed the AI to call `engine.dispose()` before attempting to delete the temporary database file, fixing the test suite.

## Conclusion
AI was heavily utilized for velocity (writing 50+ tests, scaffolding API routes, formatting Markdown), but the **core cryptographic logic, architectural design decisions, and security guardrails** were explicitly designed and enforced by the human engineer.
