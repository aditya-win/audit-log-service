import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.audit_event import AuditEvent
from app.config import settings

def tamper_record(record_id: int, field: str, new_value: str, db_url: str = settings.database_url):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        record = session.query(AuditEvent).filter(AuditEvent.id == record_id).first()
        if not record:
            print(f"Record with ID {record_id} not found.")
            return False
            
        old_value = getattr(record, field)
        setattr(record, field, new_value)
        session.commit()
        
        print(f"Successfully tampered record {record_id}.")
        print(f"Field '{field}' changed from '{old_value}' to '{new_value}'.")
        print("Note: current_hash was NOT recalculated.")
        return True
    except Exception as e:
        print(f"Error tampering with database: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tamper with the audit log database for demonstration purposes.")
    parser.add_argument("--id", type=int, required=True, help="ID of the record to tamper")
    parser.add_argument("--field", type=str, required=True, choices=["event_type", "actor_id", "resource_type", "resource_id", "payload", "timestamp", "previous_hash", "current_hash"], help="Field to modify")
    parser.add_argument("--value", type=str, required=True, help="New value for the field")
    
    args = parser.parse_args()
    tamper_record(args.id, args.field, args.value)
