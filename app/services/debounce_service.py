import threading
import uuid
from typing import Optional

import structlog

from app.core.config import settings
from app.services.agent_service import AgentService

logger = structlog.get_logger()


class DebounceService:
    """Service to handle debounced agent processing"""

    def __init__(self):
        self.debounce_timer: Optional[threading.Timer] = None
        self.debounce_lock = threading.Lock()
        self.agent_running = False
        self.run_again = False
        self.agent_service = AgentService()

    def start_or_reset_timer(self):
        """Start or reset the debounce timer"""
        with self.debounce_lock:
            if self.debounce_timer:
                self.debounce_timer.cancel()
                logger.debug("Cancelled existing debounce timer")

            self.debounce_timer = threading.Timer(
                settings.DEBOUNCE_SECONDS, self._try_run_agentic_process
            )
            self.debounce_timer.start()
            logger.info(
                f"Started debounce timer for {settings.DEBOUNCE_SECONDS} seconds"
            )

    def _try_run_agentic_process(self):
        """Try to run the agentic process, respecting concurrency limits"""
        with self.debounce_lock:
            if self.agent_running:
                self.run_again = True
                logger.info("Agent already running, will run again after completion")
                return
            self.agent_running = True

        # Generate session ID for this agent run
        session_id = str(uuid.uuid4())
        logger.info("Starting agentic process", session_id=session_id)

        # Spawn agentic process in background thread
        threading.Thread(
            target=self._agentic_process, args=(session_id,), daemon=True
        ).start()

    def _agentic_process(self, session_id: str):
        """Main agentic process loop. commenting out until i build this later"""
        # try:
        #     while True:
        #         self.run_again = False

        #         # Process pending messages
        #         processed_count = self.agent_service.process_pending_messages(
        #             session_id
        #         )

        #         with self.debounce_lock:
        #             if self.run_again:
        #                 logger.info(
        #                     "New messages arrived, processing again",
        #                     session_id=session_id,
        #                 )
        #                 continue  # New messages arrived while processing
        #             else:
        #                 self.agent_running = False
        #                 logger.info(
        #                     "Agentic process completed",
        #                     session_id=session_id,
        #                     processed_count=processed_count,
        #                 )
        #                 break

        # except Exception as e:
        #     logger.error(
        #         "Error in agentic process", session_id=session_id, error=str(e)
        #     )
        #     with self.debounce_lock:
        #         self.agent_running = False

    def shutdown(self):
        """Clean shutdown of debounce service"""
        with self.debounce_lock:
            if self.debounce_timer:
                self.debounce_timer.cancel()
                logger.info("Debounce service shutdown complete")
