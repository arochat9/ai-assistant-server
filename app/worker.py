#!/usr/bin/env python3
import asyncio
from datetime import datetime, timedelta

from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.message import Message, MessageStatus
from app.services.agent_service import AgentService
from app.services.message_processor import MessageProcessor


async def worker_loop():
    processor = MessageProcessor(test_processing_time=2)  # 2 sec test
    agent = AgentService(test_processing_time=5)  # 5 sec test

    while True:
        async with AsyncSessionLocal() as db:
            # Process unprocessed messages
            unprocessed = await db.execute(
                select(Message).where(Message.status == MessageStatus.UNPROCESSED)
            )
            for message in unprocessed.scalars():
                await processor.process_message(str(message.message_id))

            # Run agent on ready messages if no recent activity
            cutoff = datetime.utcnow() - timedelta(seconds=settings.DEBOUNCE_SECONDS)
            recent_messages = await db.execute(
                select(Message).where(Message.created_at > cutoff)
            )
            if not recent_messages.scalars().first():
                await agent.process_batch()

        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(worker_loop())
