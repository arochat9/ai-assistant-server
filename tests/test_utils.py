"""Test utilities for DRY testing across test files"""

import uuid


def create_message_data(
    text="Test message",
    message_id=None,
    chat_id=None,
    chat_name="Test Chat",
    members=None,
    **kwargs,
):
    """Create test message data with defaults and flexibility"""
    if members is None:
        members = [
            {"user_id": str(uuid.uuid4()), "name": "User One", "is_sender": True}
        ]

    return {
        "message_id": message_id or str(uuid.uuid4()),
        "text_content": text,
        "chat_id": chat_id or str(uuid.uuid4()),
        "chat_display_name": chat_name,
        "chat_members_struct": members,
        **kwargs,
    }


async def post_message(client, **kwargs):
    """Post a test message to the API"""
    data = create_message_data(**kwargs)
    return await client.post("/api/v1/messages/", json=data)


async def post_message_with_data(client, **kwargs):
    """Post a test message and return both response and data"""
    data = create_message_data(**kwargs)
    response = await client.post("/api/v1/messages/", json=data)
    return response, data
