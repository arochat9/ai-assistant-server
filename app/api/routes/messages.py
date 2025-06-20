import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_schemas.message import MessageCreate, MessageResponse
from app.core.database import get_db
from app.models import Message
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

        # Create message in database
        message = Message(
            message_id=message_data.message_id,
            text_content=message_data.text_content,
            text_character_count=text_character_count,
            status=MessageStatus.UNPROCESSED,
            user_id=message_data.user_id,
            chat_id=message_data.chat_id,
            user_info_struct=message_data.user_info_struct,
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
