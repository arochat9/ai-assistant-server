import uuid
import pytest

from fastapi import status

from app.models.message import MessageStatus


class TestMessageRoutes:
    """Integration tests for message routes"""
    
    def test_messages_endpoint_exists(self, client):
        """Test that the messages endpoint is accessible"""
        response = client.options("/api/v1/messages/")
        assert response.status_code != 404, "Messages endpoint should exist"
        
        # Also test that the health endpoint works
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_create_message(self, client):
        """Test successful message creation"""
        # Prepare test data
        message_id = str(uuid.uuid4())
        message_data = {
            "message_id": message_id,
            "text_content": "Test message content",
            "user_id": "test-user-id",
            "chat_id": "test-chat-id",
            "user_info_struct": {"test": "data"},
            "is_spam": False,
        }

        # Send request
        response = client.post("/api/v1/messages/", json=message_data)
        # Verify response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message_id"] == message_id
        assert data["text_content"] == "Test message content"
        assert data["user_id"] == "test-user-id"
        assert data["chat_id"] == "test-chat-id"
        assert data["status"] == MessageStatus.UNPROCESSED
        assert data["text_character_count"] == len(message_data["text_content"])
        assert "time_received" in data

    def test_create_duplicate_message(self, client):
        """Test handling of duplicate message IDs"""
        # Create message with specific ID
        message_id = str(uuid.uuid4())
        message_data = {
            "message_id": message_id,
            "text_content": "Original message",
            "user_id": "test-user-id",
            "chat_id": "test-chat-id",
        }
        # First request should succeed
        response = client.post("/api/v1/messages/", json=message_data)
        assert response.status_code == status.HTTP_201_CREATED
        # Second request with same ID should fail
        duplicate_data = {
            "message_id": message_id,  # Same ID
            "text_content": "Duplicate message",
            "user_id": "test-user-id",
            "chat_id": "test-chat-id",
        }
        response = client.post("/api/v1/messages/", json=duplicate_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_msg = f"Message with ID {message_id} already exists"
        assert error_msg in response.json()["detail"]
