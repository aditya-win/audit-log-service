from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class ChainStatus(str, Enum):
    INTACT = "INTACT"
    BROKEN = "BROKEN"

class ViolationType(str, Enum):
    HASH_MISMATCH = "HASH_MISMATCH"
    MISSING_PREVIOUS_HASH = "MISSING_PREVIOUS_HASH"
    ORPHANED_RECORD = "ORPHANED_RECORD"
    TAMPERED_PAYLOAD = "TAMPERED_PAYLOAD"

class VerificationError(BaseModel):
    recordId: int
    violationType: ViolationType
    expectedHash: str
    actualHash: str

class VerificationResponse(BaseModel):
    status: ChainStatus
    error: Optional[VerificationError] = None

class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AuditFinding(BaseModel):
    recordId: int
    severity: Severity
    description: str

class AuditReport(BaseModel):
    summary: str
    findings: List[AuditFinding]
    totalEventsProcessed: int
