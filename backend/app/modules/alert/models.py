from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import AlertStatus, RiskLevel, ScopeType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CommunityRiskProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'community_risk_profiles'

    community_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    community_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    street_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    street_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    scope_type: Mapped[str] = mapped_column(String(32), default=ScopeType.community.value, index=True)
    scope_id: Mapped[str] = mapped_column(String(128), index=True)
    scope_name: Mapped[str] = mapped_column(String(255), index=True)
    risk_type: Mapped[str] = mapped_column(String(64), default='other', index=True)

    stat_window_start: Mapped[date] = mapped_column(Date, index=True)
    stat_window_end: Mapped[date] = mapped_column(Date, index=True)

    case_count: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    people_count: Mapped[int] = mapped_column(Integer, default=0)
    growth_rate: Mapped[float] = mapped_column(Float, default=0.0)
    repeat_defendant_rate: Mapped[float] = mapped_column(Float, default=0.0)
    repeat_defendant_max_count: Mapped[int] = mapped_column(Integer, default=0)

    top_defendants: Mapped[list[str]] = mapped_column(JSON, default=list)
    top_projects: Mapped[list[str]] = mapped_column(JSON, default=list)
    metric_scores: Mapped[list[dict]] = mapped_column(JSON, default=list)
    triggered_rules: Mapped[list[str]] = mapped_column(JSON, default=list)

    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(16), default=RiskLevel.blue.value, index=True)
    previous_risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)


class AlertEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'alerts'

    community_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    community_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    street_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    street_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    scope_type: Mapped[str] = mapped_column(String(32), default=ScopeType.community.value, index=True)
    scope_id: Mapped[str] = mapped_column(String(128), index=True)
    scope_name: Mapped[str] = mapped_column(String(255), index=True)
    risk_type: Mapped[str] = mapped_column(String(64), default='other', index=True)

    alert_code: Mapped[str] = mapped_column(String(64), index=True)
    alert_level: Mapped[str] = mapped_column(String(16), default=RiskLevel.blue.value, index=True)
    title: Mapped[str] = mapped_column(String(255))
    trigger_reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=AlertStatus.active.value, index=True)

    profile_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    previous_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    current_level: Mapped[str | None] = mapped_column(String(16), nullable=True)

    case_count: Mapped[int] = mapped_column(Integer, default=0)
    people_count: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    growth_rate: Mapped[float] = mapped_column(Float, default=0.0)
    repeat_defendant_rate: Mapped[float] = mapped_column(Float, default=0.0)
    repeat_defendant_max_count: Mapped[int] = mapped_column(Integer, default=0)
    top_defendants: Mapped[list[str]] = mapped_column(JSON, default=list)

    dashboard_visible: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)
