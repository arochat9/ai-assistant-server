import uuid

import pytest
from fastapi import status

from app.models.message import MessageStatus


class TestMessageRoutes:
    """Integration tests for message routes"""

    @pytest.mark.asyncio
    async def test_messages_endpoint_exists(self, async_client):
        """Test that the messages endpoint is accessible"""
        response = await async_client.options("/api/v1/messages/")
        assert response.status_code != 404, "Messages endpoint should exist"

        # Also test that the health endpoint works
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    @pytest.mark.asyncio
    async def test_create_message(self, async_client):
        """Test successful message creation"""
        # Prepare test data with correct schema
        message_id = str(uuid.uuid4())
        message_data = {
            "message_id": message_id,
            "text_content": "Test message content",
            "chat_id": "test-chat-id",
            "chat_display_name": "Test Chat",
            "chat_members_struct": [
                {"user_id": "test-user-id", "name": "Test User", "is_sender": True},
                {"user_id": "other-user-id", "name": "Other User", "is_sender": False},
            ],
            "is_spam": False,
        }

        # Send request
        response = await async_client.post("/api/v1/messages/", json=message_data)

        # Verify response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message_id"] == message_id
        assert data["text_content"] == "Test message content"
        assert data["chat_id"] == "test-chat-id"
        assert data["status"] == MessageStatus.UNPROCESSED.value
        assert data["text_character_count"] == len(message_data["text_content"])
        assert "time_received" in data

    @pytest.mark.asyncio
    async def test_create_duplicate_message(self, async_client):
        """Test handling of duplicate message IDs"""
        # Create message with specific ID
        message_id = str(uuid.uuid4())
        message_data = {
            "message_id": message_id,
            "text_content": "Original message",
            "chat_id": "test-chat-id",
            "chat_display_name": "Test Chat",
            "chat_members_struct": [
                {"user_id": "test-user-id", "name": "Test User", "is_sender": True}
            ],
        }

        # First request should succeed
        response = await async_client.post("/api/v1/messages/", json=message_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Second request with same ID should fail
        duplicate_data = {
            "message_id": message_id,  # Same ID
            "text_content": "Duplicate message",
            "chat_id": "test-chat-id",
            "chat_display_name": "Test Chat",
            "chat_members_struct": [
                {"user_id": "test-user-id", "name": "Test User", "is_sender": True}
            ],
        }
        response = await async_client.post("/api/v1/messages/", json=duplicate_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Database error" in response.json()["detail"]
