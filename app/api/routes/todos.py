from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api_schemas.todo import TaskCreate, TaskResponse, TaskUpdate
from app.core.database import get_db
from app.models import Task
from app.models.todo import TaskOrEvent, TaskStatus, TaskType

logger = structlog.get_logger()
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task/event item"""
    try:
        task = Task(
            task_name=task_data.task_name,
            task_context=task_data.task_context,
            task_or_event=task_data.task_or_event,
            task_type=task_data.task_type,
            event_start_time=task_data.event_start_time,
            event_end_time=task_data.event_end_time,
            task_due_time=task_data.task_due_time,
            source_message_id=task_data.source_message_id,
            created_by_agent=False,  # Manual creation
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info(
            "Task created successfully",
            task_id=str(task.task_id),
            task_name=task.task_name,
        )
        return task

    except Exception as e:
        logger.error("Failed to create task", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[TaskStatus] = Query(None),
    task_or_event_filter: Optional[TaskOrEvent] = Query(None),
    task_type_filter: Optional[TaskType] = Query(None),
    created_by_agent: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """Get tasks with optional filtering"""
    query = db.query(Task)

    if status_filter:
        query = query.filter(Task.status == status_filter)

    if task_or_event_filter:
        query = query.filter(Task.task_or_event == task_or_event_filter)

    if task_type_filter:
        query = query.filter(Task.task_type == task_type_filter)

    if created_by_agent is not None:
        query = query.filter(Task.created_by_agent == created_by_agent)

    tasks = query.offset(skip).limit(limit).order_by(Task.created_at.desc()).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)
):
    """Update a task item"""
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Update fields
    update_data = task_update.dict(exclude_unset=True)

    # Handle completion logic
    if "completed" in update_data:
        if update_data["completed"] and not task.completed:
            task.status = TaskStatus.COMPLETED
            from datetime import datetime

            task.completed_at = datetime.utcnow()
        elif not update_data["completed"] and task.completed:
            task.status = TaskStatus.PENDING
            task.completed_at = None

    # Apply updates
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    logger.info("Task updated successfully", task_id=task.task_id)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task item"""
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    db.delete(task)
    db.commit()

    logger.info("Task deleted successfully", task_id=task_id)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def mark_task_complete(task_id: int, db: Session = Depends(get_db)):
    """Mark a task as completed"""
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    task.completed = True
    task.status = TaskStatus.COMPLETED
    from datetime import datetime

    task.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    return task


@router.post("/{task_id}/reopen", response_model=TaskResponse)
async def reopen_task(task_id: int, db: Session = Depends(get_db)):
    """Reopen a completed task"""
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    task.completed = False
    task.status = TaskStatus.PENDING
    task.completed_at = None

    db.commit()
    db.refresh(task)

    return task
