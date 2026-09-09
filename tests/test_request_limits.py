import pytest
from httpx import ASGITransport, AsyncClient

from src.mcpbridge.api import MAX_BODY_BYTES, app


@pytest.mark.asyncio
async def test_declared_oversized_request_is_rejected_before_routing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/plan",
            headers={"content-length": str(MAX_BODY_BYTES + 1), "content-type": "application/json"},
            content=b"{}",
        )
    assert response.status_code == 413
    assert response.json()["detail"] == "request body too large"


@pytest.mark.asyncio
async def test_invalid_content_length_is_rejected_cleanly():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/plan",
            headers={"content-length": "not-a-number", "content-type": "application/json"},
            content=b"{}",
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "invalid content-length"


@pytest.mark.asyncio
async def test_chunked_oversized_request_is_rejected_by_actual_body_size():
    async def oversized_chunks():
        yield b"x" * (MAX_BODY_BYTES // 2)
        yield b"x" * (MAX_BODY_BYTES // 2 + 1)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/plan",
            headers={"content-type": "application/json", "transfer-encoding": "chunked"},
            content=oversized_chunks(),
        )
    assert response.status_code == 413
    assert response.json()["detail"] == "request body too large"
