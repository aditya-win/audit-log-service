from fastapi import FastAPI
from app.config import settings
from app.api.health_routes import router as health_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
    )
    
    app.include_router(health_router, prefix=settings.api_prefix)
    
    return app

app = create_app()
