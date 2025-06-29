import asyncio

import pytest

from tests.integration.integration_utils import post_message


class TestDebounceService:
    """Test debounce service timer behavior"""

    @pytest.mark.asyncio
    async def test_timer_starts_on_message(self, async_client_with_debounce):
        """Test that timer starts when message is created"""
        client, debounce_service = async_client_with_debounce

        await post_message(client)

        # Timer should be active
        assert debounce_service.debounce_timer is not None
        assert debounce_service.debounce_timer.is_alive()

    @pytest.mark.asyncio
    async def test_timer_resets_on_new_message(self, async_client_with_debounce):
        """Test that new message cancels old timer and starts new one"""
        client, debounce_service = async_client_with_debounce

        # Send first message
        await post_message(client, text="First message")
        first_timer = debounce_service.debounce_timer

        # Wait a bit then send second message
        await asyncio.sleep(0.1)
        await post_message(client, text="Second message")
        second_timer = debounce_service.debounce_timer

        # Should be different timer objects
        assert first_timer is not second_timer
        assert second_timer.is_alive()
