import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api_schemas.message import MessageCreate, MessageResponse
from app.core.database import get_db
from app.models import Chat, Message, User
from app.models.chat import ChatType
from app.models.message import MessageStatus
from app.services.debounce_service import DebounceService

logger = structlog.get_logger()
router = APIRouter(prefix="/messages", tags=["messages"])

# Global debounce service instance
debounce_service = DebounceService()


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate, db: AsyncSession = Depends(get_db)
):
    """
    Receive a text message, store it in database, and trigger debounced agent processing
    """
    try:
        # Calculate character count
        text_character_count = len(message_data.text_content)

        # Extract sender_name and user_id from chat_members_struct
        sender_name = None
        user_id = None
        for member in message_data.chat_members_struct:
            if member.is_sender:
                sender_name = member.name
                user_id = member.user_id
                break

        # Ensure users exist or create them, and update name if changed
        users = await get_or_create_users(db, message_data.chat_members_struct)
        chat_type = ChatType.GROUP if len(users) > 2 else ChatType.PRIVATE
        await get_or_create_chat(
            db,
            message_data.chat_id,
            message_data.chat_display_name,
            chat_type,
            users,
        )

        # Convert ChatMember models to dicts for JSON storage
        chat_members_struct = [
            member.model_dump() for member in message_data.chat_members_struct
        ]

        # Create message in database
        message = Message(
            message_id=message_data.message_id,
            text_content=message_data.text_content,
            text_character_count=text_character_count,
            status=MessageStatus.UNPROCESSED,
            user_id=user_id,
            chat_id=message_data.chat_id,
            chat_members_struct=chat_members_struct,
            sender_name=sender_name,
            is_spam=message_data.is_spam or False,
            replied_to_fk=message_data.replied_to_fk,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        # Trigger debounced agent processing
        debounce_service.start_or_reset_timer()

        logger.info(
            "Message created successfully",
            message_id=message.message_id,
            text_length=text_character_count,
        )

        return message

    except IntegrityError as e:
        db_error = str(e.orig)  # Get the original database error
        logger.error(
            "Database integrity error",
            message_id=message_data.message_id,
            error_type=type(e.orig).__name__,
            error=db_error,
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {db_error}",
        )
    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to create message", error=error_msg)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {error_msg}",
        )


async def get_or_create_users(db: AsyncSession, chat_members_struct):
    user_ids = {member.user_id for member in chat_members_struct}
    existing_users = await db.execute(select(User).where(User.user_id.in_(user_ids)))
    existing_user_dict = {user.user_id: user for user in existing_users.scalars()}

    users = {}
    for member in chat_members_struct:
        user = existing_user_dict.get(
            member.user_id, User(user_id=member.user_id, name=member.name)
        )
        # Update name if it changed
        if user.user_id in existing_user_dict and user.name != member.name:
            user.name = member.name
        db.add(user)
        users[member.user_id] = user

    return users


async def get_or_create_chat(
    db: AsyncSession, chat_id, chat_display_name, chat_type, users
):
    # Fetch chat with users relationship loaded
    result = await db.execute(
        select(Chat).options(selectinload(Chat.users)).where(Chat.chat_id == chat_id)
    )
    chat = result.scalars().first()
    # If chat does not exist, create a new one
    if not chat:
        chat = Chat(
            chat_id=chat_id,
            chat_display_name=chat_display_name,
            chat_type=chat_type,
            users=list(users.values()),
        )
    else:
        # Update chat name if it has changed
        if (
            chat_display_name is not None
            and chat.chat_display_name != chat_display_name
        ):
            chat.chat_display_name = chat_display_name
        # Add new users to the chat if they are not already present
        existing_user_ids = {user.user_id for user in chat.users}
        for user in users.values():
            if user.user_id not in existing_user_ids:
                chat.users.append(user)
    db.add(chat)
    return chat
