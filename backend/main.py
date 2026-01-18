#API docs -> http://127.0.0.1:8000/docs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings
from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_parse import router as parse_router
from app.api.v1.routes_export import router as export_router

from app.db.session import engine
from app.db.base import Base

def create_app() -> FastAPI:
    app = FastAPI(title="Lector de Estados de Cuenta API", version="0.1.0")

    # CORS (para React)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(parse_router, prefix="/api/v1")
    app.include_router(export_router, prefix="/api/v1")

    # Crear tablas en arranque (MVP; luego migramos a Alembic)
    @app.on_event("startup")
    def _startup():
        Base.metadata.create_all(bind=engine)

    return app

app = create_app()
