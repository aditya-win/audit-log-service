# Audit Log Service API Reference

## Authentication
All sensitive endpoints require an API Key passed via the `X-API-Key` HTTP header.
- **Header:** `X-API-Key`
- **Default (Prototype):** `super-secret-key-123`

---

## Endpoints

### 1. Create Audit Event
Append a new immutable event to the hash chain.
- **Method:** `POST`
- **Path:** `/audit`
- **Request Body (JSON):**
  ```json
  {
    "eventType": "USER_LOGIN",
    "actorId": "user-123",
    "resourceType": "auth",
    "resourceId": "session-1",
    "payload": { "ip": "127.0.0.1" }
  }
  ```
- **Response (201 Created):**
  Returns the saved `AuditEventResponse` including `currentHash` and `previousHash`.

### 2. Query Audit Events
Retrieve a paginated list of audit events.
- **Method:** `GET`
- **Path:** `/audit`
- **Query Parameters:**
  - `actorId` (optional)
  - `resourceType` (optional)
  - `resourceId` (optional)
  - `startDate` (optional, ISO8601)
  - `endDate` (optional, ISO8601)
  - `page` (default: 1)
  - `pageSize` (default: 10, max: 100)

### 3. Get Single Event
Retrieve a specific audit event by its ID.
- **Method:** `GET`
- **Path:** `/audit/{id}`

### 4. Verify Chain Integrity
Trigger a global re-calculation of the cryptographic hash chain to prove tamper-evidence.
- **Method:** `GET`
- **Path:** `/audit/verify`
- **Response (200 OK):**
  ```json
  {
    "status": "INTACT",
    "error": null
  }
  ```

### 5. Archive Event (Scenario B)
Soft-delete an event payload due to retention policy.
- **Method:** `POST`
- **Path:** `/audit/{id}/archive`
- **Response:** `204 No Content`

### 6. Redact Event (Scenario B)
Cryptographically redact specific fields within an event payload without breaking the hash chain.
- **Method:** `POST`
- **Path:** `/audit/{id}/redact`
- **Request Body (JSON Array):** `["sensitive_field_1", "sensitive_field_2"]`
- **Response (200 OK):** `{"status": "redacted"}`

### 7. Bulk Export (Scenario B)
Export a verifiable bundle of records for a specific actor or resource.
- **Method:** `GET`
- **Path:** `/audit/export/bundle`
- **Query Parameters:**
  - `actorId` (optional)
  - `resourceId` (optional)

### 8. Health Check (Public)
- **Method:** `GET`
- **Path:** `/health`
- **Auth:** No authentication required.
