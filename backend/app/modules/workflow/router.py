from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db.session import get_db
from app.modules.workflow.schemas import WorkflowTaskCreate, WorkflowTaskStageUpdate
from app.modules.workflow.service import WorkflowTaskService


router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/tasks")
def create_workflow_task(payload: WorkflowTaskCreate, db: Session = Depends(get_db)):
    service = WorkflowTaskService(db)
    return ok(service.create_task(payload))


@router.get("/tasks")
def list_workflow_tasks(
    stage: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    service = WorkflowTaskService(db)
    return ok(service.list_tasks(stage=stage, limit=limit))


@router.patch("/tasks/{task_id}/stage")
def update_workflow_task_stage(
    task_id: str,
    payload: WorkflowTaskStageUpdate,
    db: Session = Depends(get_db),
):
    service = WorkflowTaskService(db)
    try:
        return ok(service.update_stage(task_id=task_id, payload=payload))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
