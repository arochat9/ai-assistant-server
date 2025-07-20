import asyncio

import pytest

from app.models.message import MessageStatus
from app.worker import worker_loop
from tests.integration.integration_utils import (
    post_and_get_message,
)

pytestmark = pytest.mark.serial


@pytest.mark.asyncio
async def test_worker_status_transitions(async_client, db_session):
    message = await post_and_get_message(async_client, db_session)
    assert message.status == MessageStatus.UNPROCESSED

    # 1st worker: UNPROCESSED -> READY_FOR_AGENT
    await worker_loop(test_worker=True, override_debounce_seconds=5)
    await db_session.refresh(message)
    assert message.status == MessageStatus.READY_FOR_AGENT

    # Just wait a little longer than the debounce window
    await asyncio.sleep(1.1)

    # 2nd worker: READY_FOR_AGENT -> PROCESSED
    await worker_loop(test_worker=True, override_debounce_seconds=1)
    await db_session.refresh(message)
    assert message.status == MessageStatus.PROCESSED


@pytest.mark.asyncio
async def test_staggered_batch_agent_processing(async_client, db_session):
    # 1. Create msg1, run worker, assert READY_FOR_AGENT
    msg1 = await post_and_get_message(async_client, db_session)
    await worker_loop(test_worker=True, override_debounce_seconds=5)
    await db_session.refresh(msg1)
    assert msg1.status == MessageStatus.READY_FOR_AGENT

    # 2. Create msg2, run worker, assert both READY_FOR_AGENT
    msg2 = await post_and_get_message(async_client, db_session)
    await worker_loop(test_worker=True, override_debounce_seconds=5)
    await db_session.refresh(msg1)
    await db_session.refresh(msg2)
    assert msg1.status == msg2.status == MessageStatus.READY_FOR_AGENT

    # 3. Create msg3, wait a second, run worker, assert all PROCESSED
    msg3 = await post_and_get_message(async_client, db_session)
    await asyncio.sleep(1.1)
    await worker_loop(test_worker=True, override_debounce_seconds=1)
    for m in (msg1, msg2, msg3):
        await db_session.refresh(m)
        assert m.status == MessageStatus.PROCESSED
