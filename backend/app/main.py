from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.logging import setup_logging

setup_logging()

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Lenny Growth Assistant API",
        description="Backend API for The Lenny Growth Assistant",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api import chat, sessions
    from app.providers.factory import get_llm_provider
    from sqlalchemy.future import select
    from app.models import Episode

    app.include_router(chat.router)
    app.include_router(sessions.router)

    @app.on_event("startup")
    async def startup() -> None:
        await init_db()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await close_db()

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        # Lightweight DB check
        db_status = "ok"
        try:
            from app.core.database import async_session_maker
            async with async_session_maker() as session:
                await session.execute(select(Episode).limit(1))
        except Exception as e:
            db_status = "error"

        # Lightweight provider checks
        ollama_status = "ok"
        try:
            ollama = get_llm_provider("ollama")
            if not await ollama.health_check():
                ollama_status = "degraded"
        except Exception:
            ollama_status = "error"
            
        openai_status = "ok"
        try:
            openai = get_llm_provider("openai")
            if not await openai.health_check():
                openai_status = "missing_key"
        except Exception:
            openai_status = "error"

        overall_status = "ok" if db_status == "ok" else "degraded"

        return {
            "status": overall_status,
            "db": db_status,
            "ollama": ollama_status,
            "openai": openai_status
        }

    return app


app = create_app()