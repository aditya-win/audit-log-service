# Scenario B: Retention, Redaction, and Export

## 1. Retention Policy
**Approach:** We add an `is_archived` boolean flag to the `audit_events` table.
When a record is archived (e.g., via a background job or API), its `payload` is set to `null` (or a tombstone string) to reclaim space and enforce data minimization. 
**Tamper Evidence:** During verification, if `is_archived` is true, the `VerificationService` skips calculating the `current_hash` from the payload (since the payload is gone), but it **still strictly enforces** that the record's `current_hash` matches the `previous_hash` of the next record. 
This distinguishes legitimate archival from unexpected disappearance (which would break the chain link). 

## 2. Structured Redaction
**Approach:** Cryptographic Commitment / Salted Hashes.
To allow redaction without breaking the hash chain, we introduce a `redaction_commitments` JSON column. 
However, since we already built the hash chain in Scenario A to hash the raw payload, modifying the payload directly would break the hash. 
*To solve this while preserving the chain:*
We alter the hashing mechanism for new records (or assume a schema migration). When an event is created, we don't hash the raw payload string. Instead, we hash a `payload_commitment` which is a Merkle-like hash of the payload fields. 
For simplicity in this prototype: 
1. We add a `redacted_fields` JSON column.
2. When redacting a field (e.g. `payload.account`), we remove it from `payload`.
3. We store the hash of the original field value in `redacted_fields`.
4. The `current_hash` function is updated to hash the combination of `payload` AND `redacted_fields`. 
Since `hash(original_payload) == hash(redacted_payload + redacted_fields)`, the `current_hash` remains perfectly valid and verifiable, but the sensitive plaintext is destroyed.

## 3. Bulk Export
**Approach:** Provide a `/audit/export` endpoint that returns a JSON bundle containing:
- `records`: The list of requested events.
- `metadata`: Export timestamp, query parameters.
- `chain_verification`: A cryptographic proof (e.g. a signed hash or just the boundary hashes) so the recipient can independently verify the records. 
Since the recipient gets the `previous_hash` and `current_hash` for each exported record, they can run the exact same deterministic verification logic locally to ensure the bundle hasn't been altered since export.
