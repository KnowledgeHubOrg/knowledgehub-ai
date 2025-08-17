import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_and_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register
        response = await ac.post("/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass",
            "role_id": None
        })
        assert response.status_code == 200
        user = response.json()
        assert user["email"] == "test@example.com"

        # Login
        response = await ac.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpass"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token

@pytest.mark.asyncio
async def test_ask_question():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Dummy token for test
        headers = {"Authorization": "Bearer testtoken"}
        response = await ac.post("/questions/ask", json={
            "user_id": "00000000-0000-0000-0000-000000000000",
            "question_text": "What is HR policy?",
            "domain_id": "00000000-0000-0000-0000-000000000000"
        }, headers=headers)
        assert response.status_code == 200
        answer = response.json()
        assert "answer_text" in answer
