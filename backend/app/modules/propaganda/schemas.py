from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PropagandaArticleBase(BaseModel):
    article_code: str
    title: str
    summary: str | None = None
    content: str
    risk_types: list[str] = Field(default_factory=list)
    scenario_tags: list[str] = Field(default_factory=list)
    related_law_names: list[str] = Field(default_factory=list)
    applicable_scope_types: list[str] = Field(default_factory=list)
    hot_score: float = Field(default=50.0, ge=0.0, le=100.0)
    priority: int = Field(default=50, ge=0, le=100)
    enabled: bool = True
    publish_status: str = 'published'
    extra_meta: dict = Field(default_factory=dict)


class PropagandaArticleUpsertItem(PropagandaArticleBase):
    id: str | None = None


class PropagandaArticleBatchUpsertRequest(BaseModel):
    items: list[PropagandaArticleUpsertItem]


class PropagandaArticleRead(PropagandaArticleBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {'from_attributes': True}


class PropagandaArticleListResponse(BaseModel):
    items: list[PropagandaArticleRead] = Field(default_factory=list)


class PropagandaRecommendRequest(BaseModel):
    alert_id: str | None = None
    profile_id: str | None = None
    scope_type: str | None = None
    scope_id: str | None = None
    risk_type: str | None = None
    context_tags: list[str] = Field(default_factory=list)
    related_law_names: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=20)
    persist: bool = True
    dashboard_visible: bool = True


class PropagandaPushRead(BaseModel):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    profile_id: str | None = None
    alert_id: str | None = None
    community_id: str | None = None
    community_name: str | None = None
    street_id: str | None = None
    street_name: str | None = None
    scope_type: str
    scope_id: str
    scope_name: str
    risk_type: str = 'other'
    article_id: str
    article_code: str
    title: str
    summary: str | None = None
    recommendation_score: float = 0.0
    matched_risk_types: list[str] = Field(default_factory=list)
    matched_scenario_tags: list[str] = Field(default_factory=list)
    related_law_names: list[str] = Field(default_factory=list)
    match_reason: str = ''
    source_mode: str = 'rule_rank'
    dashboard_visible: bool = True
    status: str = 'active'
    extra_meta: dict = Field(default_factory=dict)

    model_config = {'from_attributes': True}


class PropagandaRecommendResponse(BaseModel):
    items: list[PropagandaPushRead] = Field(default_factory=list)
    articles: list[PropagandaArticleRead] = Field(default_factory=list)
    resolved_scope_type: str
    resolved_scope_id: str
    resolved_scope_name: str
    resolved_risk_type: str
    used_context_tags: list[str] = Field(default_factory=list)
    used_related_law_names: list[str] = Field(default_factory=list)
    source_mode: str = 'rule_rank'


class PropagandaPushListRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=200)
    alert_id: str | None = None
    profile_id: str | None = None
    scope_type: str | None = None
    scope_id: str | None = None
    risk_type: str | None = None
    dashboard_visible_only: bool = True


class PropagandaPushListResponse(BaseModel):
    items: list[PropagandaPushRead] = Field(default_factory=list)
