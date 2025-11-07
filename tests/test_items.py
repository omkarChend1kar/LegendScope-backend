import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "environment" in payload


@pytest.mark.asyncio
async def test_item_crud_flow() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/items", json={"name": "Sample", "description": "Demo", "price": 10.5}
        )
        assert create_response.status_code == 201
        item = create_response.json()
        item_id = item["id"]

        list_response = await client.get("/api/items")
        assert list_response.status_code == 200
        items = list_response.json()
        assert any(entry["id"] == item_id for entry in items)

        get_response = await client.get(f"/api/items/{item_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == "Sample"

        delete_response = await client.delete(f"/api/items/{item_id}")
        assert delete_response.status_code == 204

        missing_response = await client.get(f"/api/items/{item_id}")
        assert missing_response.status_code == 404
