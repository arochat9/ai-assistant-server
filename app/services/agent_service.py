import asyncio
import threading
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
        self.agent_lock = threading.Lock()
        self.agent_running = False
        self.pending_retry = False
        self.test_processing_time = test_processing_time

    def process_ready_messages(self):
        """Process all messages ready for agent (batch processing)"""
        with self.agent_lock:
            if self.agent_running:
                self.pending_retry = True
                logger.info("Agent already running, will retry after completion")
                return
            self.agent_running = True

        try:
            # Process messages in a loop to handle retries
            while True:
                self.pending_retry = False
                asyncio.run(self.process_batch())

                # Check if we need to retry
                with self.agent_lock:
                    if not self.pending_retry:
                        break
                    logger.info("Processing retry batch")

        except Exception as e:
            logger.error("Error in agent processing", error=str(e))
        finally:
            self.agent_running = False

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
