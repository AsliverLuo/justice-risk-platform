from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.workflow.models import WorkflowTask
from app.modules.workflow.schemas import (
    WORKFLOW_STAGES,
    WorkflowTaskCreate,
    WorkflowTaskListResponse,
    WorkflowTaskRead,
    WorkflowTaskStageUpdate,
)


STAGE_OPTIONS = [
    {"key": "discovered", "label": "风险发现"},
    {"key": "alerted", "label": "已预警"},
    {"key": "assigned", "label": "已分派"},
    {"key": "handling", "label": "处置中"},
    {"key": "feedback", "label": "已反馈"},
    {"key": "evaluated", "label": "已评估"},
]


class WorkflowTaskService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task(self, payload: WorkflowTaskCreate) -> WorkflowTaskRead:
        task = WorkflowTask(
            task_name=payload.task_name,
            alert_id=payload.alert_id,
            alert_title=payload.alert_title,
            street=payload.street,
            risk_level=payload.risk_level,
            case_type=payload.case_type,
            main_unit=payload.main_unit,
            deadline=payload.deadline,
            actions=payload.actions,
            description=payload.description,
            stage=payload.stage,
            extra_meta=payload.extra_meta,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return WorkflowTaskRead.model_validate(task)

    def list_tasks(self, *, stage: str | None = None, limit: int = 200) -> WorkflowTaskListResponse:
        stage_key = stage if stage in WORKFLOW_STAGES else "assigned"
        all_tasks = list(self.db.scalars(select(WorkflowTask)).all())
        stage_counts = {item["key"]: 0 for item in STAGE_OPTIONS}
        for task in all_tasks:
            stage_counts[task.stage] = stage_counts.get(task.stage, 0) + 1

        tasks = list(
            self.db.scalars(
                select(WorkflowTask)
                .where(WorkflowTask.stage == stage_key)
                .order_by(WorkflowTask.updated_at.desc(), WorkflowTask.created_at.desc())
                .limit(limit)
            ).all()
        )

        return WorkflowTaskListResponse(
            stage=stage_key,
            stage_label=next(item["label"] for item in STAGE_OPTIONS if item["key"] == stage_key),
            stage_options=[{**item, "count": stage_counts.get(item["key"], 0)} for item in STAGE_OPTIONS],
            total=len(tasks),
            items=[WorkflowTaskRead.model_validate(task) for task in tasks],
        )

    def update_stage(self, *, task_id: str, payload: WorkflowTaskStageUpdate) -> WorkflowTaskRead:
        task = self.db.get(WorkflowTask, task_id)
        if task is None:
            raise ValueError("workflow task not found")
        task.stage = payload.stage
        if payload.feedback is not None:
            task.feedback = payload.feedback
        if payload.evaluation is not None:
            task.evaluation = payload.evaluation
        if payload.stage == "evaluated":
            extra_meta = dict(task.extra_meta or {})
            extra_meta["evaluation_card"] = self._build_evaluation_card(task)
            task.extra_meta = extra_meta
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return WorkflowTaskRead.model_validate(task)

    def _build_evaluation_card(self, task: WorkflowTask) -> dict:
        before_level = task.risk_level or "orange"
        after_level = self._downgrade_level(before_level)
        before_score = self._default_score(before_level)
        after_score = self._default_score(after_level)
        score_drop = max(0, before_score - after_score)
        case_drop_rate = 42 if before_level in {"red", "orange"} else 28
        coverage = 1260 if before_level in {"red", "orange"} else 820
        read_rate = 76 if before_level in {"red", "orange"} else 68
        satisfaction = 83 if task.feedback or task.evaluation else 76

        return {
            "summary": self._evaluation_summary(before_level, after_level, score_drop),
            "before": {
                "riskLevel": before_level,
                "riskLevelText": self._risk_level_text(before_level),
                "riskScore": before_score,
            },
            "after": {
                "riskLevel": after_level,
                "riskLevelText": self._risk_level_text(after_level),
                "riskScore": after_score,
            },
            "riskChange": {
                "levelChanged": before_level != after_level,
                "scoreDrop": score_drop,
                "conclusion": f"风险评分下降 {score_drop} 分，风险等级由{self._risk_level_text(before_level)}调整为{self._risk_level_text(after_level)}。",
            },
            "eventChange": {
                "sameTypeNewCaseDropRate": case_drop_rate,
                "repeatSubjectTriggered": False,
                "conclusion": f"同类案件新增下降 {case_drop_rate}%，重复主体暂未再次触发预警。",
            },
            "governanceEffect": {
                "onTimeCompletionRate": 100,
                "jointHandlingCompletionRate": 92,
                "conclusion": "承办单位按期反馈，协同单位完成联动处置。",
            },
            "propagandaEffect": {
                "coveragePeople": coverage,
                "readRate": read_rate,
                "surveySatisfaction": satisfaction,
                "conclusion": f"精准普法覆盖 {coverage} 人，阅读率 {read_rate}%，回访满意度 {satisfaction}%。",
            },
        }

    def _downgrade_level(self, level: str) -> str:
        return {
            "red": "yellow",
            "orange": "yellow",
            "yellow": "blue",
            "blue": "blue",
        }.get(level, "blue")

    def _default_score(self, level: str) -> int:
        return {
            "red": 86,
            "orange": 68,
            "yellow": 48,
            "blue": 28,
        }.get(level, 28)

    def _risk_level_text(self, level: str) -> str:
        return {
            "red": "红色",
            "orange": "橙色",
            "yellow": "黄色",
            "blue": "蓝色",
        }.get(level, "蓝色")

    def _evaluation_summary(self, before_level: str, after_level: str, score_drop: int) -> str:
        if before_level != after_level:
            return f"处置后风险等级下降，风险评分下降 {score_drop} 分，建议转入常态化跟踪。"
        return "处置后风险保持低位，建议继续观察同类线索变化。"
