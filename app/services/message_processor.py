import asyncio
from typing import Optional

import structlog
from sqlalchemy import update

from app.core.database import AsyncSessionLocal
from app.models.message import Message, MessageStatus

logger = structlog.get_logger()


class MessageProcessor:
    """Service for processing individual messages"""

    def __init__(self, test_processing_time: Optional[float] = None):
        self.test_processing_time = test_processing_time

    async def process_message(self, message_id: str):
        """Process a single message and mark it as ready for agent"""
        logger.info("Processing message", message_id=message_id)

        async with AsyncSessionLocal() as db:
            if self.test_processing_time is not None:
                # Test mode - just sleep for the specified time
                await asyncio.sleep(self.test_processing_time)
            else:
                # TODO: Implement actual message processing logic here
                # This is where you would do NLP, entity extraction, etc.
                pass

            # Mark as ready for agent
            await db.execute(
                update(Message)
                .where(Message.message_id == message_id)
                .values(status=MessageStatus.READY_FOR_AGENT)
            )
            await db.commit()

            logger.info("Message ready for agent", message_id=message_id)
