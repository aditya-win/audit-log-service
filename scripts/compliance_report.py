import argparse
import json
from collections import defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.services.verification_service import VerificationService

def generate_compliance_report(client_id: str, db_url: str = settings.database_url, output_format: str = "markdown"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # 1. Verify the overall chain integrity first to ensure the data is trustworthy
        repo = AuditRepository(session)
        verifier = VerificationService(repo)
        verification_result = verifier.verify_chain()
        
        is_trustworthy = verification_result.status.value == "INTACT"
        
        # 2. Load DATA_ACCESS events for the client
        # In our schema, resource_id could be the client account ID
        events = session.query(AuditEvent).filter(
            AuditEvent.event_type == "DATA_ACCESS",
            AuditEvent.resource_id == client_id
        ).order_by(AuditEvent.timestamp).all()
        
        # 3. Group by actorId
        access_by_actor = defaultdict(list)
        for event in events:
            access_by_actor[event.actor_id].append({
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "payload": json.loads(event.payload) if event.payload else {"_archived": True},
                "is_archived": bool(event.is_archived)
            })
            
        if output_format == "json":
            report = {
                "client_id": client_id,
                "chain_integrity": verification_result.status.value,
                "total_access_events": len(events),
                "access_by_actor": dict(access_by_actor)
            }
            return json.dumps(report, indent=2)
            
        # Markdown format
        lines = []
        lines.append(f"# Compliance Report: Data Access for Client `{client_id}`")
        lines.append(f"**Chain Integrity Status:** `{'✅ INTACT' if is_trustworthy else '❌ BROKEN'}`")
        if not is_trustworthy:
            lines.append(f"> **WARNING:** The underlying audit log is compromised. Data in this report may be tampered with.")
            
        lines.append(f"\n**Total Access Events:** {len(events)}\n")
        
        for actor, actor_events in access_by_actor.items():
            lines.append(f"## Actor: `{actor}`")
            lines.append(f"- **Total accesses:** {len(actor_events)}")
            for ev in actor_events:
                status = "(Archived)" if ev["is_archived"] else ""
                lines.append(f"  - `[{ev['timestamp']}]` Event ID: {ev['id']} {status}")
            lines.append("")
            
        return "\n".join(lines)
        
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Scenario C Compliance Report")
    parser.add_argument("--client-id", type=str, required=True, help="The client account ID (resource_id)")
    parser.add_argument("--format", type=str, choices=["json", "markdown"], default="markdown", help="Output format")
    parser.add_argument("--db-url", type=str, default=settings.database_url, help="Database URL")
    
    args = parser.parse_args()
    print(generate_compliance_report(args.client_id, args.db_url, args.format))
