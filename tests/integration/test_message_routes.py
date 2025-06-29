import uuid

import pytest
from fastapi import status
from sqlalchemy.future import select

from app.models import Chat, User
from app.models.chat import ChatType
from app.models.message import MessageStatus


class TestMessageRoutes:
    """Integration tests for message routes"""

    @staticmethod
    def unique_id(prefix="test"):
        """Generate a unique ID for tests"""
        return f"{prefix}_{str(uuid.uuid4())[:8]}"

    @staticmethod
    def _create_message_data(
        msg_id=None,
        chat_id=None,
        chat_name="Test Chat",
        members=None,
        text="Test message",
        **kwargs,
    ):
        """DRY helper to create message data with unique IDs"""
        if chat_id is None:
            chat_id = TestMessageRoutes.unique_id("chat")

        if members is None:
            members = [
                {
                    "user_id": TestMessageRoutes.unique_id("user"),
                    "name": "User One",
                    "is_sender": True,
                }
            ]

        return {
            "message_id": msg_id or str(uuid.uuid4()),
            "text_content": text,
            "chat_id": chat_id,
            "chat_display_name": chat_name,
            "chat_members_struct": members,
            **kwargs,
        }

    @staticmethod
    async def _post_message(client, **kwargs):
        """DRY helper to post message and return response"""
        data = TestMessageRoutes._create_message_data(**kwargs)
        return await client.post("/api/v1/messages/", json=data), data

    @staticmethod
    async def _get_user_from_db(db_session, user_id):
        """Helper to get user from database"""
        result = await db_session.execute(select(User).where(User.user_id == user_id))
        return result.scalars().first()

    @staticmethod
    async def _get_chat_from_db(db_session, chat_id):
        """Helper to get chat from database with users loaded"""
        from sqlalchemy.orm import selectinload

        result = await db_session.execute(
            select(Chat)
            .options(selectinload(Chat.users))
            .where(Chat.chat_id == chat_id)
        )
        return result.scalars().first()

    @staticmethod
    async def _verify_users_created(db_session, expected_users):
        """Verify users exist in database with correct names"""
        for user_data in expected_users:
            user = await TestMessageRoutes._get_user_from_db(
                db_session, user_data["user_id"]
            )
            assert user is not None, f"User {user_data['user_id']} not found"
            expected_name = user_data["name"]
            assert user.name == expected_name, (
                f"User name: {user.name} != {expected_name}"
            )

    @staticmethod
    async def _verify_chat_created(
        db_session,
        chat_id,
        expected_name=None,
        expected_type=None,
        expected_user_count=None,
    ):
        """Verify chat exists with correct properties"""
        chat = await TestMessageRoutes._get_chat_from_db(db_session, chat_id)
        assert chat is not None, f"Chat {chat_id} not found in database"

        if expected_name is not None:
            assert chat.chat_display_name == expected_name, (
                f"Chat name: {chat.chat_display_name} != {expected_name}"
            )

        if expected_type is not None:
            assert chat.chat_type == expected_type, (
                f"Chat type: {chat.chat_type} != {expected_type}"
            )

        if expected_user_count is not None:
            actual_count = len(chat.users)
            assert actual_count == expected_user_count, (
                f"Chat user count: {actual_count} != {expected_user_count}"
            )

    @pytest.mark.asyncio
    async def test_create_message(self, async_client):
        """Test successful message creation"""
        response, data = await self._post_message(async_client)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        # assert result["message_id"] == data["message_id"]
        assert result["message_id"] == "fail here"
        assert result["text_content"] == data["text_content"]
        assert result["chat_id"] == data["chat_id"]
        assert result["status"] == MessageStatus.UNPROCESSED.value
        # Assert against the actual user_id from generated data
        expected_user_id = data["chat_members_struct"][0]["user_id"]
        assert result["user_id"] == expected_user_id
        assert result["sender_name"] == "User One"
        assert "time_received" in result

    @pytest.mark.asyncio
    async def test_create_duplicate_message(self, async_client):
        """Test handling of duplicate message IDs"""
        msg_id = str(uuid.uuid4())

        # First message succeeds
        response, _ = await self._post_message(async_client, msg_id=msg_id)
        assert response.status_code == status.HTTP_201_CREATED

        # Duplicate fails
        response, _ = await self._post_message(async_client, msg_id=msg_id)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_message_with_minimal_data(self, async_client):
        """Test message creation with only required fields"""
        response, _ = await self._post_message(async_client, chat_name=None)
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_message_reply_functionality(self, async_client):
        """Test message reply functionality using replied_to_fk"""
        # Create original
        original_response, original_data = await self._post_message(async_client)
        assert original_response.status_code == status.HTTP_201_CREATED

        # Create reply
        reply_response, _ = await self._post_message(
            async_client, replied_to_fk=original_data["message_id"]
        )
        assert reply_response.status_code == status.HTTP_201_CREATED
        assert reply_response.json()["replied_to_fk"] == original_data["message_id"]

    @pytest.mark.asyncio
    async def test_direct_message_new_chat_new_users(self, async_client, db_session):
        """Test DM in new chat with new users - verify database state"""
        chat_id = self.unique_id("dm_chat")
        user1_id = self.unique_id("dm_user1")
        user2_id = self.unique_id("dm_user2")

        members = [
            {"user_id": user1_id, "name": "Alice", "is_sender": True},
            {"user_id": user2_id, "name": "Bob", "is_sender": False},
        ]
        response, data = await self._post_message(
            async_client,
            chat_id=chat_id,
            chat_name="Alice & Bob",
            members=members,
        )

        # Verify API response
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["user_id"] == user1_id
        assert result["sender_name"] == "Alice"

        # Verify database state
        await self._verify_users_created(db_session, members)
        await self._verify_chat_created(
            db_session,
            chat_id,
            expected_name="Alice & Bob",
            expected_type=ChatType.PRIVATE,
            expected_user_count=2,
        )

    @pytest.mark.asyncio
    async def test_group_message_new_chat_new_users(self, async_client, db_session):
        """Test group message in new chat with new users - verify database state"""
        chat_id = self.unique_id("group_chat")
        user1_id = self.unique_id("group_user1")
        user2_id = self.unique_id("group_user2")
        user3_id = self.unique_id("group_user3")

        members = [
            {"user_id": user1_id, "name": "Alice", "is_sender": True},
            {"user_id": user2_id, "name": "Bob", "is_sender": False},
            {"user_id": user3_id, "name": "Charlie", "is_sender": False},
        ]
        response, _ = await self._post_message(
            async_client,
            chat_id=chat_id,
            chat_name="Team Chat",
            members=members,
        )

        # Verify API response
        assert response.status_code == status.HTTP_201_CREATED

        # Verify database state
        await self._verify_users_created(db_session, members)
        await self._verify_chat_created(
            db_session,
            chat_id,
            expected_name="Team Chat",
            expected_type=ChatType.GROUP,
            expected_user_count=3,
        )

    @pytest.mark.asyncio
    async def test_message_existing_chat_update_name(self, async_client, db_session):
        """Test message in existing chat but update chat name - verify name update"""
        chat_id = self.unique_id("rename_chat")

        # Create first message
        await self._post_message(async_client, chat_id=chat_id, chat_name="Old Name")

        # Verify initial chat state
        await self._verify_chat_created(db_session, chat_id, expected_name="Old Name")

        # Send message with new name
        response, _ = await self._post_message(
            async_client, chat_id=chat_id, chat_name="New Name"
        )
        assert response.status_code == status.HTTP_201_CREATED

        # Verify chat name was updated
        await self._verify_chat_created(db_session, chat_id, expected_name="New Name")

    @pytest.mark.asyncio
    async def test_message_existing_chat_new_users(self, async_client, db_session):
        """Test message in existing chat but new users - verify users added"""
        chat_id = self.unique_id("existing_chat")
        existing_user_id = self.unique_id("existing_user")
        new_user_id = self.unique_id("new_user")

        # Create chat with initial users
        initial_members = [
            {"user_id": existing_user_id, "name": "Existing User", "is_sender": True}
        ]
        await self._post_message(async_client, chat_id=chat_id, members=initial_members)

        # Verify initial state
        await self._verify_users_created(db_session, initial_members)
        await self._verify_chat_created(db_session, chat_id, expected_user_count=1)

        # Add new users to existing chat
        new_members = [
            {"user_id": existing_user_id, "name": "Existing User", "is_sender": False},
            {"user_id": new_user_id, "name": "New User", "is_sender": True},
        ]
        response, _ = await self._post_message(
            async_client, chat_id=chat_id, members=new_members
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["user_id"] == new_user_id

        # Verify new user was added to chat
        await self._verify_users_created(db_session, new_members)
        await self._verify_chat_created(db_session, chat_id, expected_user_count=2)

    @pytest.mark.asyncio
    async def test_message_existing_users_new_names(self, async_client, db_session):
        """Test message with existing users but updated names - verify name update"""
        user_id = self.unique_id("name_update_user")

        # Create message with original name
        original_members = [{"user_id": user_id, "name": "Old Name", "is_sender": True}]
        await self._post_message(async_client, members=original_members)

        # Verify initial user state
        await self._verify_users_created(db_session, original_members)

        # Send message with updated name
        updated_members = [{"user_id": user_id, "name": "New Name", "is_sender": True}]
        response, _ = await self._post_message(async_client, members=updated_members)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["sender_name"] == "New Name"

        # Verify user name was updated in database
        await self._verify_users_created(db_session, updated_members)
        await self._verify_users_created(db_session, updated_members)
