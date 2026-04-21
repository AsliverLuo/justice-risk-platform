from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


WORKFLOW_STAGES = {"discovered", "alerted", "assigned", "handling", "feedback", "evaluated"}


class WorkflowTaskCreate(BaseModel):
    task_name: str = Field(min_length=1, max_length=255)
    alert_id: str | None = None
    alert_title: str | None = None
    street: str = Field(min_length=1, max_length=255)
    risk_level: str = "blue"
    case_type: str = "其他"
    main_unit: str = Field(min_length=1, max_length=255)
    deadline: str = ""
    actions: list[str] = Field(default_factory=list)
    description: str = ""
    stage: str = "assigned"
    extra_meta: dict = Field(default_factory=dict)

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, value: str) -> str:
        return value if value in WORKFLOW_STAGES else "assigned"


class WorkflowTaskRead(WorkflowTaskCreate):
    id: str
    feedback: str | None = None
    evaluation: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowTaskListResponse(BaseModel):
    stage: str
    stage_label: str
    stage_options: list[dict]
    total: int
    items: list[WorkflowTaskRead]


class WorkflowTaskStageUpdate(BaseModel):
    stage: str
    feedback: str | None = None
    evaluation: str | None = None

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, value: str) -> str:
        if value not in WORKFLOW_STAGES:
            raise ValueError("invalid workflow stage")
        return value
