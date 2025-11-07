from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_profile_success_from_cache() -> None:
    """Test successful profile retrieval from DynamoDB cache."""
    # Mock Lambda response (200 - found in cache)
    mock_lambda_response = {
        "message": "Profile found",
        "profile": {
            "riotId": "cant type#1998",
            "puuid": (
                "AE6W6hK5V8cX9u7QgudTQsrYaGQQafYzONYl3EieQwtcZTkatRhVRLLRqAITJMKhy04eYi0vdPYPbA"
            ),
            "summonerName": "cant type",
            "tagLine": "1998",
            "region": "na1",
            "createdAt": 1762520913736,
            "updatedAt": 1762520913736,
        },
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_lambda_response
        mock_post.return_value = mock_response

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/profile",
                json={"riot_id": "cant type#1998", "region": "na1"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["riot_id"] == "cant type#1998"
    assert data["region"] == "na1"
    assert data["summoner_name"] == "cant type"
    assert "message" in data
    assert "cache" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_profile_not_found_falls_back_to_mock() -> None:
    """Test profile not found in cache (404) - falls back to mock data."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Player profile not found"}
        mock_post.return_value = mock_response

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/profile",
                json={"riot_id": "NewPlayer#NA1", "region": "na1"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["riot_id"] == "NewPlayer#NA1"
    assert data["summoner_name"] == "NewPlayer"
    assert "mock data" in data["message"]

@pytest.mark.asyncio
async def test_get_profile_invalid_riot_id_too_short() -> None:
    """Test profile retrieval with invalid riot_id (too short)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/profile",
            json={"riot_id": "AB", "region": "na1"},
        )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_profile_invalid_region_too_short() -> None:
    """Test profile retrieval with invalid region (too short)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/profile",
            json={"riot_id": "Player#NA1", "region": "a"},
        )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_profile_missing_fields() -> None:
    """Test profile retrieval with missing required fields."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/profile",
            json={"riot_id": "Player#NA1"},  # Missing region
        )
    
    assert response.status_code == 422  # Validation error
