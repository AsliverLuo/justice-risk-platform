from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RecommendationTemplateBase(BaseModel):
    template_code: str
    title: str
    risk_type: str | None = None
    alert_code: str | None = None
    scope_type: str | None = None
    applicable_levels: list[str] = Field(default_factory=list)
    scenario_tags: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    narrative_hint: str | None = None
    priority: int = Field(default=50, ge=0, le=100)
    enabled: bool = True
    extra_meta: dict = Field(default_factory=dict)


class RecommendationTemplateUpsertItem(RecommendationTemplateBase):
    id: str | None = None


class RecommendationTemplateBatchUpsertRequest(BaseModel):
    items: list[RecommendationTemplateUpsertItem]


class RecommendationTemplateRead(RecommendationTemplateBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {'from_attributes': True}


class RecommendationTemplateListResponse(BaseModel):
    items: list[RecommendationTemplateRead] = Field(default_factory=list)


class RecommendationLawReference(BaseModel):
    id: str | None = None
    article_no: str | None = None
    law_name: str
    title: str | None = None
    content: str
    score: float = 0.0


class RecommendationCaseSnapshot(BaseModel):
    case_id: str
    title: str
    case_type: str = 'other'
    judgment_date: str | None = None
    defendant_summary: str | None = None
    claim_summary: str | None = None
    summary: str | None = None
    people_count: int = 0
    total_amount: float = 0.0


class RecommendationGenerateRequest(BaseModel):
    alert_id: str | None = None
    profile_id: str | None = None
    scope_type: str | None = None
    scope_id: str | None = None
    risk_type: str | None = None
    context_summary: str | None = None
    case_summaries: list[str] = Field(default_factory=list)
    template_limit: int = Field(default=3, ge=0, le=10)
    case_limit: int = Field(default=5, ge=0, le=10)
    law_top_k: int = Field(default=5, ge=1, le=10)
    prefer_llm: bool = True
    persist: bool = True
    dashboard_visible: bool = True


class GovernanceRecommendationRead(BaseModel):
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
    recommendation_level: str = 'medium'
    title: str
    summary: str
    action_items: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    follow_up_metrics: list[str] = Field(default_factory=list)
    related_laws: list[RecommendationLawReference] = Field(default_factory=list)
    case_snapshots: list[RecommendationCaseSnapshot] = Field(default_factory=list)
    matched_template_codes: list[str] = Field(default_factory=list)
    source_mode: str = 'template'
    dashboard_visible: bool = True
    status: str = 'active'
    extra_meta: dict = Field(default_factory=dict)

    model_config = {'from_attributes': True}


class RecommendationGenerateResponse(BaseModel):
    recommendation: GovernanceRecommendationRead
    used_templates: list[RecommendationTemplateRead] = Field(default_factory=list)
    related_laws: list[RecommendationLawReference] = Field(default_factory=list)
    case_snapshots: list[RecommendationCaseSnapshot] = Field(default_factory=list)
    mode: str = 'template'


class RecommendationListRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=200)
    alert_id: str | None = None
    profile_id: str | None = None
    scope_type: str | None = None
    scope_id: str | None = None
    risk_type: str | None = None
    dashboard_visible_only: bool = True


class RecommendationListResponse(BaseModel):
    items: list[GovernanceRecommendationRead] = Field(default_factory=list)
