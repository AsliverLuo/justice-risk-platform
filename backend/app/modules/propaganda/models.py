from __future__ import annotations

from sqlalchemy import Boolean, JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PropagandaArticle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'propaganda_articles'

    article_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    risk_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    scenario_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    related_law_names: Mapped[list[str]] = mapped_column(JSON, default=list)
    applicable_scope_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    hot_score: Mapped[float] = mapped_column(Float, default=50.0, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=50, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    publish_status: Mapped[str] = mapped_column(String(32), default='published', index=True)
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)


class PropagandaPushRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'propaganda_push_records'

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

    article_id: Mapped[str] = mapped_column(String(64), index=True)
    article_code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    matched_risk_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    matched_scenario_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    related_law_names: Mapped[list[str]] = mapped_column(JSON, default=list)
    match_reason: Mapped[str] = mapped_column(Text, default='')
    source_mode: Mapped[str] = mapped_column(String(32), default='rule_rank', index=True)
    dashboard_visible: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default='active', index=True)
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)
