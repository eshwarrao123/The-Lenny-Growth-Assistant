"""
Pytest fixtures for backend tests.
"""
import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base


# Monkey-patch models to use SQLite-compatible types for testing
def _apply_sqlite_type_overrides():
    """Replace PostgreSQL-specific types with SQLite-compatible ones."""
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    from sqlalchemy import JSON, String
    from pgvector.sqlalchemy import Vector
    
    # Override JSONB with JSON for SQLite
    import app.models
    for model_name in ['Episode', 'TranscriptChunk', 'Message']:
        model = getattr(app.models, model_name, None)
        if model and hasattr(model, '__table__'):
            for col in model.__table__.columns:
                if isinstance(col.type, JSONB):
                    col.type = JSON()
    
    # Note: We skip VECTOR and UUID type replacement as they're handled by SQLAlchemy's type coercion


@pytest_asyncio.fixture
async def async_session():
    """
    Create an in-memory SQLite database session for testing.
    """
    _apply_sqlite_type_overrides()
    
    # Create in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
