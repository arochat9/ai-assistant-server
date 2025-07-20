#!/usr/bin/env python3
import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.message import Message, MessageStatus
from app.services.agent_service import AgentService
from app.services.message_processor import MessageProcessor


async def worker_loop(
    test_database_session=None, override_debounce_seconds: Optional[int] = None
):
    # Exit early during testing
    if os.getenv("PYTEST_RUNNING") and not test_database_session:
        return

    processor = MessageProcessor(test_processing_time=0.2)
    agent = AgentService(test_processing_time=0.2)

    while True:

        async def process_messages(db):
            # Process unprocessed messages
            unprocessed = await db.execute(
                select(Message).where(Message.status == MessageStatus.UNPROCESSED)
            )
            for message in unprocessed.scalars():
                await processor.process_message(str(message.message_id), db)

            # Run agent on ready messages if no recent activity
            cutoff = datetime.now() - timedelta(
                seconds=override_debounce_seconds or settings.DEBOUNCE_SECONDS
            )
            recent_messages = await db.execute(
                select(Message).where(Message.time_received > cutoff)
            )
            if not recent_messages.scalars().first():
                await agent.process_batch(db)

        if test_database_session:
            await process_messages(test_database_session)
        else:
            async with AsyncSessionLocal() as db:
                await process_messages(db)

        if test_database_session:
            break

        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(worker_loop())
