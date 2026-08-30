from fastapi import FastAPI
from app.config import settings
from app.api.health_routes import router as health_router
from app.api.audit_routes import router as audit_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
    )
    
    # SECURITY LIMITATION: 
    # This application currently lacks Authentication and Authorization (e.g., JWT, OAuth2).
    # In production, all routes should be protected by RBAC, ensuring only authorized services can append,
    # and only authorized compliance officers can trigger verifications or exports.
    # Rate limiting should also be applied to prevent DoS attacks.

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(audit_router, prefix=settings.api_prefix)
    
    return app

app = create_app()
