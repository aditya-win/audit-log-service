from app.repositories.audit_repository import AuditRepository
from app.schemas.verification import VerificationResponse, VerificationError, ChainStatus, ViolationType
from app.utils.hashing import calculate_hash, GENESIS_HASH

class VerificationService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def verify_chain(self) -> VerificationResponse:
        iterator = self.repository.get_all_ordered_iterator()
        expected_previous_hash = GENESIS_HASH

        for record in iterator:
            # 1. Check previous hash link
            if record.previous_hash != expected_previous_hash:
                return VerificationResponse(
                    status=ChainStatus.BROKEN,
                    error=VerificationError(
                        recordId=record.id,
                        violationType=ViolationType.MISSING_PREVIOUS_HASH if record.previous_hash is None else ViolationType.HASH_MISMATCH,
                        expectedHash=expected_previous_hash,
                        actualHash=record.previous_hash
                    )
                )

            # 2. Check current hash based on content
            expected_current_hash = calculate_hash(
                event_type=record.event_type,
                actor_id=record.actor_id,
                resource_type=record.resource_type,
                resource_id=record.resource_id,
                payload_str=record.payload,
                timestamp=record.timestamp,
                previous_hash=record.previous_hash
            )

            if record.current_hash != expected_current_hash:
                return VerificationResponse(
                    status=ChainStatus.BROKEN,
                    error=VerificationError(
                        recordId=record.id,
                        violationType=ViolationType.TAMPERED_PAYLOAD,
                        expectedHash=expected_current_hash,
                        actualHash=record.current_hash
                    )
                )

            expected_previous_hash = record.current_hash

        return VerificationResponse(status=ChainStatus.INTACT)
