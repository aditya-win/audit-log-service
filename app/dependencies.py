from typing import Generator
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.services.verification_service import VerificationService

# For the prototype, sqlite is fine. Use check_same_thread=False for FastAPI concurrency.
engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_audit_repository(db: Session = Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)

def get_audit_service(repo: AuditRepository = Depends(get_audit_repository)) -> AuditService:
    return AuditService(repo)

def get_verification_service(repo: AuditRepository = Depends(get_audit_repository)) -> VerificationService:
    return VerificationService(repo)
