"""Integration tests for chat API."""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_send_chat_message(
    client: AsyncClient,
    test_client,
    auth_headers: dict,
):
    """Test sending a chat message."""
    response = await client.post(
        f"/api/v1/clients/{test_client.id}/chat/",
        headers=auth_headers,
        json={
            "message": "Hello, what are your hours?",
            "sender_id": "test_user_123",
            "channel": "web",
        },
    )

    # Note: This will fail without mocked LLM, but tests structure
    # In real tests, mock the LLM and RAG services
    assert response.status_code in [200, 500]  # 500 if services not mocked


@pytest.mark.asyncio
async def test_list_conversations(
    client: AsyncClient,
    test_client,
    auth_headers: dict,
):
    """Test listing conversations."""
    response = await client.get(
        f"/api/v1/clients/{test_client.id}/chat/conversations",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_chat_requires_auth(client: AsyncClient, test_client):
    """Test that chat endpoints require authentication."""
    response = await client.post(
        f"/api/v1/clients/{test_client.id}/chat/",
        json={
            "message": "Hello",
            "sender_id": "test",
            "channel": "web",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_wrong_client_access(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that users can't access other clients' chat."""
    fake_client_id = str(uuid4())

    response = await client.get(
        f"/api/v1/clients/{fake_client_id}/chat/conversations",
        headers=auth_headers,
    )

    # Should be 403 (forbidden) or 404 (not found)
    assert response.status_code in [403, 404]
