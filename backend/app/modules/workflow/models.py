from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_tasks"

    task_name: Mapped[str] = mapped_column(String(255), index=True)
    alert_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    alert_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    street: Mapped[str] = mapped_column(String(255), index=True)
    risk_level: Mapped[str] = mapped_column(String(16), index=True)
    case_type: Mapped[str] = mapped_column(String(64), index=True)
    main_unit: Mapped[str] = mapped_column(String(255), index=True)
    deadline: Mapped[str] = mapped_column(String(64), default="")
    actions: Mapped[list[str]] = mapped_column(JSON, default=list)
    description: Mapped[str] = mapped_column(Text, default="")
    stage: Mapped[str] = mapped_column(String(32), default="assigned", index=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)
