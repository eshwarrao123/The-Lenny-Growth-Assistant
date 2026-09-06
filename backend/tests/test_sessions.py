import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db


@pytest.mark.asyncio
async def test_list_sessions_empty(async_session):
    """Verify GET /api/sessions returns a list when queried."""
    app.dependency_overrides[get_db] = lambda: async_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/sessions")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_and_list_sessions(async_session):
    """Verify POST /api/sessions creates a session and GET /api/sessions lists it."""
    app.dependency_overrides[get_db] = lambda: async_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Create session
            create_resp = await ac.post("/api/sessions")
            assert create_resp.status_code == 200
            created = create_resp.json()
            assert "id" in created
            assert created["title"] == "New Chat"

            # List sessions
            list_resp = await ac.get("/api/sessions")
            assert list_resp.status_code == 200
            sessions = list_resp.json()
            assert len(sessions) >= 1
            assert any(s["id"] == created["id"] for s in sessions)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_session_by_id(async_session):
    """Verify GET /api/sessions/{id} retrieves session details."""
    app.dependency_overrides[get_db] = lambda: async_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            create_resp = await ac.post("/api/sessions")
            session_id = create_resp.json()["id"]

            get_resp = await ac.get(f"/api/sessions/{session_id}")
            assert get_resp.status_code == 200
            detail = get_resp.json()
            assert detail["id"] == session_id
            assert "messages" in detail
            assert "artifacts" in detail
    finally:
        app.dependency_overrides.clear()
