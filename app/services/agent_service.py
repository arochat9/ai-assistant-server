import asyncio
from typing import Optional

import structlog
from sqlalchemy import update
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.models.message import Message, MessageStatus

logger = structlog.get_logger()


class AgentService:
    """Service for batch processing of messages ready for agent"""

    def __init__(self, test_processing_time: Optional[float] = None):
        self.test_processing_time = test_processing_time

    async def process_batch(self):
        """Process batch of ready messages"""
        async with AsyncSessionLocal() as db:
            # Get ready messages
            result = await db.execute(
                select(Message).where(Message.status == MessageStatus.READY_FOR_AGENT)
            )
            ready_messages = result.scalars().all()

            if not ready_messages:
                logger.info("No messages ready for agent")
                return

            message_ids = [msg.message_id for msg in ready_messages]
            logger.info(f"Processing {len(ready_messages)} ready messages")

            # Mark as processing
            await db.execute(
                update(Message)
                .where(Message.message_id.in_(message_ids))
                .values(status=MessageStatus.AGENT_PROCESSING)
            )
            await db.commit()

            if self.test_processing_time is not None:
                # Test mode - just sleep for the specified time
                await asyncio.sleep(self.test_processing_time)
            else:
                # TODO: Implement actual agent processing logic here
                # This is where you would do task extraction, etc.
                pass

            # Mark as processed
            await db.execute(
                update(Message)
                .where(Message.message_id.in_(message_ids))
                .values(status=MessageStatus.PROCESSED)
            )
            await db.commit()

            logger.info(f"Processed {len(ready_messages)} messages")
