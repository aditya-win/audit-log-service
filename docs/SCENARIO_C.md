# Scenario C: Compliance Reporting

## Original Ambiguous Requirement
> "Regulators need to be able to audit access to client account data."

## Identified Ambiguities & Questions
When analyzing this requirement, several ambiguities were identified before proceeding with implementation:
1. **Who is executing the audit?** Are regulators accessing the system directly, or is our internal compliance team running a report for them?
2. **What defines "client account data"?** Does this mean *all* events related to a specific client ID, or only `DATA_ACCESS` read events?
3. **Format of the output?** Do regulators need a CSV, a JSON API payload, or a human-readable PDF/Markdown report?
4. **Scale:** Are we exporting data for a single client (thousands of records) or the entire system (millions of records)?

## Clarified Requirement & Assumptions
**Assumption:** Regulators do not have direct API access. An internal compliance officer runs a specific query for a given client when audited. They need a verifiable, human-readable summary of who accessed that specific client's data.
**Clarified Requirement:** "Provide a secure, internal administrative script that extracts all `DATA_ACCESS` events tied to a specific `resourceId` (client account). The script must verify the global cryptographic chain's integrity before returning data, and output a structured Markdown or JSON report grouped by the actors who accessed the data."

## Concrete Technical Design
- **Tooling:** A Python CLI script (`scripts/compliance_report.py`) interacting directly with the SQLAlchemy ORM. No public REST API endpoint was created, adhering to the principle of least privilege.
- **Verification First:** The script utilizes the core `VerificationService` to run a full hash chain validation. If the chain is broken, the report prominently displays a `❌ BROKEN` warning, alerting the auditor that the underlying data is legally compromised.
- **Data Grouping:** It filters for `event_type == "DATA_ACCESS"` and `resource_id == <client_id>`, then logically groups the output by `actor_id` so auditors can easily see *who* viewed the data.

## Scope Boundaries
- **Implemented:** Chain verification, DB extraction, Actor-grouping, Markdown/JSON export capabilities.
- **Scoped Out:** We did not implement an external-facing API for regulators. We scoped out complex PDF generation in favor of universally readable Markdown. We did not implement email delivery of the report.
