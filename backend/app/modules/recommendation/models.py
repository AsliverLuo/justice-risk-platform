from __future__ import annotations

from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RecommendationTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'recommendation_templates'

    template_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    risk_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    alert_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    scope_type: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    applicable_levels: Mapped[list[str]] = mapped_column(JSON, default=list)
    scenario_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    departments: Mapped[list[str]] = mapped_column(JSON, default=list)
    suggested_actions: Mapped[list[str]] = mapped_column(JSON, default=list)
    narrative_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(default=50, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)


class GovernanceRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'governance_recommendations'

    profile_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    alert_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    community_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    community_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    street_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    street_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    scope_type: Mapped[str] = mapped_column(String(32), index=True)
    scope_id: Mapped[str] = mapped_column(String(128), index=True)
    scope_name: Mapped[str] = mapped_column(String(255), index=True)
    risk_type: Mapped[str] = mapped_column(String(64), default='other', index=True)
    recommendation_level: Mapped[str] = mapped_column(String(32), default='medium', index=True)

    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    action_items: Mapped[list[str]] = mapped_column(JSON, default=list)
    departments: Mapped[list[str]] = mapped_column(JSON, default=list)
    follow_up_metrics: Mapped[list[str]] = mapped_column(JSON, default=list)
    related_laws: Mapped[list[dict]] = mapped_column(JSON, default=list)
    case_snapshots: Mapped[list[dict]] = mapped_column(JSON, default=list)
    matched_template_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_mode: Mapped[str] = mapped_column(String(32), default='template', index=True)
    dashboard_visible: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default='active', index=True)
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)
