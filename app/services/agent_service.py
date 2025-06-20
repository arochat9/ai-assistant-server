from typing import List, Optional

import structlog
from sqlalchemy.orm import Session

from app.models import AgentLog, Message, Task
from app.models.agent_log import AgentLogLevel, AgentLogType
from app.models.message import MessageStatus
from app.models.todo import TaskOrEvent, TaskType

logger = structlog.get_logger()


class AgentService:
    """Service for agentic processing of messages and task generation"""

    def __init__(self):
        pass

    # def process_pending_messages(self, session_id: str) -> int:
    #     """Process all pending messages and generate tasks"""
    #     db = AsyncSessionLocal()
    #     try:
    #         # Get pending messages
    #         pending_messages = self._get_pending_messages(db)

    #         if not pending_messages:
    #             self._log_agent_activity(
    #                 db, session_id, AgentLogType.INFO, "No pending messages to process"
    #             )
    #             return 0

    #         self._log_agent_activity(
    #             db,
    #             session_id,
    #             AgentLogType.THOUGHT,
    #             f"Found {len(pending_messages)} pending messages to process",
    #         )

    #         # Mark messages as processing
    #         self._mark_messages_processing(db, pending_messages)

    #         # Process each message
    #         processed_count = 0
    #         for message in pending_messages:
    #             try:
    #                 self._process_single_message(db, message, session_id)
    #                 processed_count += 1
    #             except Exception as e:
    #                 logger.error(
    #                     f"Failed to process message {message.message_id}", error=str(e)
    #                 )
    #                 self._log_agent_activity(
    #                     db,
    #                     session_id,
    #                     AgentLogType.ERROR,
    #                     f"Failed to process message {message.message_id}: {str(e)}",
    #                     source_message_id=message.message_id,
    #                 )

    #         # Mark successfully processed messages as processed
    #         self._mark_messages_processed(db, pending_messages)

    #         self._log_agent_activity(
    #             db,
    #             session_id,
    #             AgentLogType.DECISION,
    #             f"Successfully processed {processed_count} messages",
    #         )

    #         return processed_count

    #     except Exception as e:
    #         logger.error("Error in process_pending_messages", error=str(e))
    #         self._log_agent_activity(
    #             db,
    #             session_id,
    #             AgentLogType.ERROR,
    #             f"Critical error in message processing: {str(e)}",
    #         )
    #         db.rollback()
    #         raise
    #     finally:
    #         db.close()

    def _get_pending_messages(self, db: Session) -> List[Message]:
        """Get all pending messages from database"""
        return (
            db.query(Message)
            .filter(Message.status == MessageStatus.UNPROCESSED)
            .order_by(Message.time_received)
            .all()
        )

    def _mark_messages_processing(self, db: Session, messages: List[Message]):
        """Mark messages as processing"""
        for message in messages:
            message.status = MessageStatus.AGENT_PROCESSING
        db.commit()

    def _mark_messages_processed(self, db: Session, messages: List[Message]):
        """Mark messages as processed"""
        for message in messages:
            message.status = MessageStatus.PROCESSED
        db.commit()

    def _process_single_message(self, db: Session, message: Message, session_id: str):
        """Process a single message and generate tasks"""
        self._log_agent_activity(
            db,
            session_id,
            AgentLogType.ACTION,
            f"Processing message: {message.text_content[:100]}...",
            source_message_id=message.message_id,
        )

        # TODO: This is where the actual agentic processing would happen
        # For now, we'll create placeholder logic

        # Analyze message for task extraction (placeholder logic)
        tasks = self._extract_tasks_from_message(message, session_id)

        # Create tasks in database
        for task_data in tasks:
            task = Task(
                task_name=task_data["task_name"],
                task_context=task_data.get("task_context"),
                task_or_event=task_data.get("task_or_event", TaskOrEvent.TASK),
                task_type=task_data.get("task_type"),
                source_message_id=message.message_id,
                created_by_agent=True,
            )
            db.add(task)

            self._log_agent_activity(
                db,
                session_id,
                AgentLogType.ACTION,
                f"Created task: {task.task_name}",
                source_message_id=message.message_id,
                metadata={
                    "task_type": task.task_type.value if task.task_type else None
                },
            )

        db.commit()

    def _extract_tasks_from_message(
        self, message: Message, session_id: str
    ) -> List[dict]:
        """
        Extract task items from a message using agentic processing

        TODO: This is where you would implement the actual agentic logic:
        - Parse message text
        - Identify actionable items
        - Determine task type and due dates
        - Generate appropriate task names and descriptions
        """

        # Placeholder logic - replace with actual agentic processing
        text = message.text_content.lower()
        tasks = []

        # Simple keyword-based extraction (to be replaced with AI)
        if any(
            keyword in text
            for keyword in ["todo", "task", "remind", "need to", "should"]
        ):
            tasks.append(
                {
                    "task_name": f"Task from message: {message.text_content[:50]}...",
                    "task_context": message.text_content,
                    "task_or_event": TaskOrEvent.TASK,
                    "task_type": TaskType.CHORE,
                }
            )

        if any(keyword in text for keyword in ["meeting", "appointment", "event"]):
            tasks.append(
                {
                    "task_name": f"Event: {message.text_content[:50]}...",
                    "task_context": message.text_content,
                    "task_or_event": TaskOrEvent.EVENT,
                }
            )

        return tasks

    def _log_agent_activity(
        self,
        db: Session,
        session_id: str,
        log_type: AgentLogType,
        message: str,
        level: AgentLogLevel = AgentLogLevel.INFO,
        source_message_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """Log agent activity to database"""
        agent_log = AgentLog(
            session_id=session_id,
            log_type=log_type,
            level=level,
            message=message,
            source_message_id=source_message_id,
            metadata=metadata,
        )
        db.add(agent_log)
        db.commit()

        # Also log to structured logger
        logger.info(
            "Agent activity",
            session_id=session_id,
            log_type=log_type.value,
            agent_message=message,
            source_message_id=source_message_id,
        )
