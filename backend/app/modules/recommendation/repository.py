from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.modules.alert.models import AlertEvent, CommunityRiskProfile
from app.modules.analysis.models import CaseCorpus
from app.modules.recommendation.models import GovernanceRecommendation, RecommendationTemplate


class RecommendationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_alert(self, alert_id: str) -> AlertEvent | None:
        return self.db.get(AlertEvent, alert_id)

    def get_profile(self, profile_id: str) -> CommunityRiskProfile | None:
        return self.db.get(CommunityRiskProfile, profile_id)

    def get_latest_profile_by_scope(self, *, scope_type: str, scope_id: str, risk_type: str | None = None) -> CommunityRiskProfile | None:
        stmt = select(CommunityRiskProfile).where(
            CommunityRiskProfile.scope_type == scope_type,
            CommunityRiskProfile.scope_id == scope_id,
        )
        if risk_type:
            stmt = stmt.where(CommunityRiskProfile.risk_type == risk_type)
        stmt = stmt.order_by(desc(CommunityRiskProfile.stat_window_end), desc(CommunityRiskProfile.created_at)).limit(1)
        return self.db.scalar(stmt)

    def list_recent_cases(self, *, scope_type: str, scope_id: str, risk_type: str | None = None, limit: int = 5) -> list[CaseCorpus]:
        stmt = select(CaseCorpus).order_by(desc(CaseCorpus.judgment_date), desc(CaseCorpus.created_at)).limit(300)
        records = list(self.db.scalars(stmt).all())
        matched: list[CaseCorpus] = []
        for record in records:
            meta = record.extra_meta or {}
            current_scope_id = None
            if scope_type == 'community':
                current_scope_id = meta.get('community_id')
            elif scope_type == 'street':
                current_scope_id = meta.get('street_id') or meta.get('street_name')
            elif scope_type == 'project':
                current_scope_id = meta.get('project_id') or meta.get('project_name')
            if scope_id and current_scope_id != scope_id:
                continue
            if risk_type and (meta.get('risk_type') or record.case_type) != risk_type:
                continue
            matched.append(record)
            if len(matched) >= limit:
                break
        return matched

    def list_templates(
        self,
        *,
        risk_type: str | None = None,
        alert_code: str | None = None,
        scope_type: str | None = None,
        current_level: str | None = None,
        enabled_only: bool = True,
        limit: int = 20,
    ) -> list[RecommendationTemplate]:
        stmt = select(RecommendationTemplate).order_by(desc(RecommendationTemplate.priority), desc(RecommendationTemplate.updated_at))
        if enabled_only:
            stmt = stmt.where(RecommendationTemplate.enabled.is_(True))
        records = list(self.db.scalars(stmt.limit(max(limit * 3, 30))).all())
        matched: list[RecommendationTemplate] = []
        for record in records:
            if risk_type and record.risk_type and record.risk_type != risk_type:
                continue
            if alert_code and record.alert_code and record.alert_code != alert_code:
                continue
            if scope_type and record.scope_type and record.scope_type != scope_type:
                continue
            if current_level and record.applicable_levels and current_level not in (record.applicable_levels or []):
                continue
            matched.append(record)
            if len(matched) >= limit:
                break
        return matched

    def upsert_template(self, payload: dict) -> RecommendationTemplate:
        existing = None
        template_id = payload.get('id')
        template_code = payload.get('template_code')
        if template_id:
            existing = self.db.get(RecommendationTemplate, template_id)
        if existing is None and template_code:
            stmt = select(RecommendationTemplate).where(RecommendationTemplate.template_code == template_code).limit(1)
            existing = self.db.scalar(stmt)
        if existing:
            for key, value in payload.items():
                if key == 'id':
                    continue
                setattr(existing, key, value)
            obj = existing
        else:
            payload = {k: v for k, v in payload.items() if k != 'id'}
            obj = RecommendationTemplate(**payload)
            self.db.add(obj)
        self.db.flush()
        return obj

    def get_recommendation(self, recommendation_id: str) -> GovernanceRecommendation | None:
        return self.db.get(GovernanceRecommendation, recommendation_id)

    def upsert_recommendation(self, payload: dict) -> GovernanceRecommendation:
        stmt = select(GovernanceRecommendation)
        if payload.get('alert_id'):
            stmt = stmt.where(GovernanceRecommendation.alert_id == payload['alert_id'])
        elif payload.get('profile_id'):
            stmt = stmt.where(GovernanceRecommendation.profile_id == payload['profile_id'])
        else:
            stmt = stmt.where(
                GovernanceRecommendation.scope_type == payload.get('scope_type'),
                GovernanceRecommendation.scope_id == payload.get('scope_id'),
                GovernanceRecommendation.risk_type == payload.get('risk_type'),
                GovernanceRecommendation.title == payload.get('title'),
            )
        existing = self.db.scalar(stmt.limit(1))
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            obj = existing
        else:
            obj = GovernanceRecommendation(**payload)
            self.db.add(obj)
        self.db.flush()
        return obj

    def list_recommendations(
        self,
        *,
        limit: int = 20,
        alert_id: str | None = None,
        profile_id: str | None = None,
        scope_type: str | None = None,
        scope_id: str | None = None,
        risk_type: str | None = None,
        dashboard_visible_only: bool = True,
    ) -> list[GovernanceRecommendation]:
        stmt = select(GovernanceRecommendation).order_by(desc(GovernanceRecommendation.created_at))
        if alert_id:
            stmt = stmt.where(GovernanceRecommendation.alert_id == alert_id)
        if profile_id:
            stmt = stmt.where(GovernanceRecommendation.profile_id == profile_id)
        if scope_type:
            stmt = stmt.where(GovernanceRecommendation.scope_type == scope_type)
        if scope_id:
            stmt = stmt.where(GovernanceRecommendation.scope_id == scope_id)
        if risk_type:
            stmt = stmt.where(GovernanceRecommendation.risk_type == risk_type)
        if dashboard_visible_only:
            stmt = stmt.where(GovernanceRecommendation.dashboard_visible.is_(True))
        stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())
