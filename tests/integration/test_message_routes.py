import uuid

import pytest
from fastapi import status

from app.models.message import MessageStatus


class TestMessageRoutes:
    """Integration tests for message routes"""

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
        assert data["user_id"] == "test-user-id"  # New field
        assert data["sender_name"] == "Test User"  # New field
        assert data["is_spam"] is False
        assert data["chat_members_struct"] == message_data["chat_members_struct"]
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

    @pytest.mark.asyncio
    async def test_message_with_minimal_data(self, async_client):
        """Test message creation with only required fields"""
        message_id = str(uuid.uuid4())
        message_data = {
            "message_id": message_id,
            "text_content": "Minimal message",
            "chat_id": "minimal-chat",
            "chat_members_struct": [
                {"user_id": "minimal-user", "name": "Minimal User", "is_sender": True}
            ],
        }

        response = await async_client.post("/api/v1/messages/", json=message_data)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["message_id"] == message_id
        assert data["replied_to_fk"] is None
        assert data["is_spam"] is False

    @pytest.mark.asyncio
    async def test_message_reply_functionality(self, async_client):
        """Test message reply functionality using replied_to_fk"""
        # Create original message
        original_id = str(uuid.uuid4())
        original_data = {
            "message_id": original_id,
            "text_content": "Original message",
            "chat_id": "reply-chat",
            "chat_members_struct": [
                {"user_id": "user-1", "name": "User One", "is_sender": True}
            ],
        }

        response = await async_client.post("/api/v1/messages/", json=original_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Create reply message
        reply_id = str(uuid.uuid4())
        reply_data = {
            "message_id": reply_id,
            "text_content": "This is a reply",
            "chat_id": "reply-chat",
            "chat_members_struct": [
                {"user_id": "user-2", "name": "User Two", "is_sender": True}
            ],
            "replied_to_fk": original_id,
        }

        response = await async_client.post("/api/v1/messages/", json=reply_data)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["replied_to_fk"] == original_id
        assert data["user_id"] == "user-2"
