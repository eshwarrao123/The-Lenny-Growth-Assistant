from typing import Any
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

    from app.api import chat, sessions, artifacts
    from app.providers.factory import get_llm_provider
    from sqlalchemy import text
    from fastapi import Response, status

    app.include_router(chat.router)
    app.include_router(sessions.router)
    app.include_router(artifacts.router)

    @app.on_event("startup")
    async def startup() -> None:
        await init_db()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await close_db()

    @app.get("/api/health")
    async def health(response: Response) -> dict[str, Any]:
        """
        Operational health check.
        Lightweight inspection of database connectivity and LLM provider reachability.
        Returns HTTP 200 (healthy/degraded) or HTTP 503 (unavailable).
        """
        # 1. Primary Database check (SELECT 1)
        db_status = "ok"
        try:
            from app.core.database import async_session_maker
            async with async_session_maker() as session:
                await session.execute(text("SELECT 1"))
        except Exception:
            db_status = "unavailable"

        # 2. Ollama Provider check (tags query)
        ollama_status = "ok"
        ollama_details = {}
        try:
            ollama = get_llm_provider("ollama")
            if hasattr(ollama, "detailed_health_check"):
                ollama_details = await ollama.detailed_health_check()
                ollama_status = ollama_details.get("status", "ok")
            elif not await ollama.health_check():
                ollama_status = "degraded"
        except Exception:
            ollama_status = "unavailable"

        # 3. Optional Cloud Provider check
        openai_status = "unconfigured"
        try:
            openai = get_llm_provider("openai")
            if await openai.health_check():
                openai_status = "ok"
            else:
                openai_status = "missing_key"
        except Exception:
            openai_status = "unavailable"

        # 4. Overall status determination
        if db_status == "unavailable":
            overall_status = "unavailable"
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif ollama_status == "ok":
            overall_status = "healthy"
        else:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "application": "ok",
            "db": db_status,
            "ollama": ollama_status,
            "openai": openai_status,
            "components": {
                "database": {"status": db_status},
                "ollama": {
                    "status": ollama_status,
                    "model": settings.ollama_model,
                    "embedding_model": settings.ollama_embedding_model,
                    **ollama_details,
                },
                "openai": {"status": openai_status},
            },
            "environment": settings.app_env,
        }

    return app


app = create_app()