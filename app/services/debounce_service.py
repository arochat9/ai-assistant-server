import threading
from typing import Optional

import structlog

from app.core.config import settings
from app.services.agent_service import AgentService

logger = structlog.get_logger()


class DebounceService:
    """Service to handle debounced agent processing"""

    def __init__(self, debounce_seconds: Optional[float] = None):
        self.debounce_timer: Optional[threading.Timer] = None
        self.lock = threading.Lock()
        self.agent_running = False
        self.run_again = False
        self.shutdown_requested = False
        self.agent_service = AgentService()
        self.debounce_seconds = debounce_seconds or settings.DEBOUNCE_SECONDS

    def start_or_reset_timer(self):
        """Start or reset the debounce timer"""
        if self.debounce_seconds < 0:
            logger.debug("Debounce disabled (negative seconds)")
            return
        if self.shutdown_requested:
            return  # Silent return - service is shutting down

        with self.lock:
            if self.debounce_timer:
                self.debounce_timer.cancel()
            self.debounce_timer = threading.Timer(
                self.debounce_seconds, self._run_agent
            )
            self.debounce_timer.start()
            logger.info(f"Started debounce timer for {self.debounce_seconds}s")

    def _run_agent(self):
        """Run the agent process if not already running"""
        with self.lock:
            if self.shutdown_requested:
                logger.debug("Shutdown requested, not starting agent")
                return
            if self.agent_running:
                self.run_again = True
                logger.info("Agent already running, will run again after completion")
                return
            self.agent_running = True

        logger.info("Starting agent worker thread")
        threading.Thread(target=self._agent_worker, daemon=True).start()

    def _agent_worker(self):
        """Agent worker thread with auto-cleanup"""
        logger.info("Agent worker started")
        try:
            while not self.shutdown_requested:
                self.run_again = False
                # TODO: Process messages here
                # self.agent_service.process_pending_messages()

                with self.lock:
                    if not self.run_again:
                        logger.info("Agent worker completed")
                        break
                    logger.info("New messages arrived, processing again")
        except Exception as e:
            logger.error("Error in agent worker", error=str(e))
        finally:
            with self.lock:
                self.agent_running = False
            logger.info("Agent worker cleanup completed")

    def shutdown(self):
        """Clean shutdown"""
        logger.info("Starting debounce service shutdown")
        with self.lock:
            self.shutdown_requested = True
            if self.debounce_timer:
                self.debounce_timer.cancel()
                logger.debug("Cancelled debounce timer")
        logger.info("Debounce service shutdown complete")

    # # OLD AGENT PROCESS DO NOT TOUCH:
    # def _agentic_process(self, session_id: str):
    #     # """Main agentic process loop. commenting out until i build this later"""
    #     try:
    #         while True:
    #             self.run_again = False

    #             # Process pending messages
    #             processed_count = self.agent_service.process_pending_messages(
    #                 session_id
    #             )

    #             with self.debounce_lock:
    #                 if self.run_again:
    #                     logger.info(
    #                         "New messages arrived, processing again",
    #                         session_id=session_id,
    #                     )
    #                     continue  # New messages arrived while processing
    #                 else:
    #                     self.agent_running = False
    #                     logger.info(
    #                         "Agentic process completed",
    #                         session_id=session_id,
    #                         processed_count=processed_count,
    #                     )
    #                     break

    #     except Exception as e:
    #         logger.error(
    #             "Error in agentic process", session_id=session_id, error=str(e)
    #         )
    #         with self.debounce_lock:
    #             self.agent_running = False
