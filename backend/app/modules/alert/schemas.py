from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.common.enums import AlertStatus, RiskLevel, ScopeType


class RiskWeightProfile(BaseModel):
    case_count: float = 0.30
    people_count: float = 0.20
    growth_rate: float = 0.20
    repeat_defendant_rate: float = 0.20
    total_amount: float = 0.10

    @field_validator('case_count', 'people_count', 'growth_rate', 'repeat_defendant_rate', 'total_amount')
    @classmethod
    def non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError('weight must be non-negative')
        return value

    def normalized(self) -> 'RiskWeightProfile':
        total = self.case_count + self.people_count + self.growth_rate + self.repeat_defendant_rate + self.total_amount
        if total <= 0:
            return RiskWeightProfile()
        return RiskWeightProfile(
            case_count=self.case_count / total,
            people_count=self.people_count / total,
            growth_rate=self.growth_rate / total,
            repeat_defendant_rate=self.repeat_defendant_rate / total,
            total_amount=self.total_amount / total,
        )


class RiskMetricScore(BaseModel):
    metric: str
    raw_value: float
    bucket_score: float
    weight: float
    weighted_contribution: float
    description: str = ''


class CommunityRiskProfileRead(BaseModel):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    community_id: str | None = None
    community_name: str | None = None
    street_id: str | None = None
    street_name: str | None = None
    scope_type: str = ScopeType.community.value
    scope_id: str
    scope_name: str
    risk_type: str = 'other'
    stat_window_start: date
    stat_window_end: date
    case_count: int = 0
    total_amount: float = 0.0
    people_count: int = 0
    growth_rate: float = 0.0
    repeat_defendant_rate: float = 0.0
    repeat_defendant_max_count: int = 0
    top_defendants: list[str] = Field(default_factory=list)
    top_projects: list[str] = Field(default_factory=list)
    risk_score: float = 0.0
    risk_level: str = RiskLevel.blue.value
    previous_risk_level: str | None = None
    metric_scores: list[RiskMetricScore] = Field(default_factory=list)
    triggered_rules: list[str] = Field(default_factory=list)
    extra_meta: dict = Field(default_factory=dict)

    model_config = {'from_attributes': True}


class AlertRead(BaseModel):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    community_id: str | None = None
    community_name: str | None = None
    street_id: str | None = None
    street_name: str | None = None
    scope_type: str = ScopeType.community.value
    scope_id: str
    scope_name: str
    risk_type: str = 'other'
    alert_code: str
    alert_level: str = RiskLevel.blue.value
    title: str
    trigger_reason: str
    status: str = AlertStatus.active.value
    profile_id: str | None = None
    previous_level: str | None = None
    current_level: str | None = None
    case_count: int = 0
    people_count: int = 0
    total_amount: float = 0.0
    growth_rate: float = 0.0
    repeat_defendant_rate: float = 0.0
    repeat_defendant_max_count: int = 0
    top_defendants: list[str] = Field(default_factory=list)
    dashboard_visible: bool = True
    pushed_at: datetime | None = None
    extra_meta: dict = Field(default_factory=dict)

    model_config = {'from_attributes': True}


class CommunityRiskEngineRequest(BaseModel):
    as_of_date: date | None = None
    window_days: int = Field(default=30, ge=7, le=180)
    compare_window_days: int = Field(default=30, ge=7, le=180)
    scope_type: str = Field(default=ScopeType.community.value)
    risk_types: list[str] | None = None
    community_ids: list[str] | None = None
    persist_profiles: bool = True
    generate_alerts: bool = True
    weights: RiskWeightProfile | None = None
    repeat_defendant_threshold: int | None = None
    group_people_threshold: int | None = None
    high_frequency_window_days: int = Field(default=30, ge=1, le=180)
    only_level_upgrade_alert: bool = Field(default=True)


class CommunityRiskEngineResponse(BaseModel):
    as_of_date: date
    scope_type: str
    profile_count: int = 0
    alert_count: int = 0
    profiles: list[CommunityRiskProfileRead] = Field(default_factory=list)
    alerts: list[AlertRead] = Field(default_factory=list)
    used_weights: RiskWeightProfile


class AlertListRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=200)
    status: str | None = None
    scope_type: str | None = None
    community_id: str | None = None
    risk_type: str | None = None
    dashboard_visible_only: bool = True


class AlertListResponse(BaseModel):
    items: list[AlertRead] = Field(default_factory=list)


class DashboardOverviewResponse(BaseModel):
    as_of_date: date
    total_profiles: int = 0
    total_alerts: int = 0
    red_count: int = 0
    orange_count: int = 0
    yellow_count: int = 0
    blue_count: int = 0
    top_risk_communities: list[CommunityRiskProfileRead] = Field(default_factory=list)
    latest_alerts: list[AlertRead] = Field(default_factory=list)
