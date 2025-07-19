import asyncio
import threading
import time
from typing import Optional

import structlog

from app.core.config import settings
from app.services.agent_service import AgentService
from app.services.message_processor import MessageProcessor

logger = structlog.get_logger()


class DebounceService:
    """Service to handle debounced agent processing"""

    def __init__(
        self,
        debounce_seconds: Optional[float] = None,
        test_processing_time: Optional[float] = None,
        test_agent_time: Optional[float] = None,
    ):
        self.debounce_timer: Optional[threading.Timer] = None
        self.lock = threading.Lock()
        self.shutdown_requested = False
        self.agent_service = AgentService(test_processing_time=test_agent_time)
        self.message_processor = MessageProcessor(
            test_processing_time=test_processing_time
        )
        self.debounce_seconds = debounce_seconds or settings.DEBOUNCE_SECONDS
        self.processing_messages = set()  # Track messages being processed

    def start_or_reset_timer(self, message_id: str):
        """Start or reset the debounce timer and process the message"""
        if self.debounce_seconds < 0:
            logger.debug("Debounce disabled (negative seconds)")
            return
        if self.shutdown_requested:
            return

        # Process message immediately in background thread
        self.process_message_async(message_id)

        with self.lock:
            if self.debounce_timer:
                self.debounce_timer.cancel()
            self.debounce_timer = threading.Timer(self.debounce_seconds, self.run_agent)
            self.debounce_timer.start()
            logger.info(f"Started debounce timer for {self.debounce_seconds}s")

    def process_message_async(self, message_id: str):
        """Process a message asynchronously in a background thread"""

        def process():
            with self.lock:
                self.processing_messages.add(message_id)

            try:
                asyncio.run(self.message_processor.process_message(message_id))
            except Exception as e:
                logger.error(
                    "Error processing message", message_id=message_id, error=str(e)
                )
            finally:
                with self.lock:
                    self.processing_messages.discard(message_id)

        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()

    def run_agent(self):
        """Run the agent process, waiting for all message processing to complete"""
        if self.shutdown_requested:
            return

        # Wait for all message processing to complete
        while True:
            with self.lock:
                if not self.processing_messages:
                    break
            logger.info(
                f"Waiting for {len(self.processing_messages)} messages to finish"
            )
            time.sleep(1)

        logger.info("Debounce timer expired, running agent")
        try:
            self.agent_service.process_ready_messages()
        except Exception as e:
            logger.error("Error running agent", error=str(e))

    def shutdown(self):
        """Clean shutdown"""
        logger.info("Starting debounce service shutdown")
        with self.lock:
            self.shutdown_requested = True
            if self.debounce_timer:
                self.debounce_timer.cancel()
                logger.debug("Cancelled debounce timer")
        logger.info("Debounce service shutdown complete")
