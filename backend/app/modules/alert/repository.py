from __future__ import annotations

from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.common.enums import AlertStatus
from app.modules.alert.models import AlertEvent, CommunityRiskProfile
from app.modules.analysis.models import CaseCorpus


class AlertRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all_cases(self) -> list[CaseCorpus]:
        stmt = select(CaseCorpus).order_by(desc(CaseCorpus.created_at))
        return list(self.db.scalars(stmt).all())

    def get_latest_profile(
        self,
        *,
        scope_type: str,
        scope_id: str,
        risk_type: str,
        before_date: date | None = None,
    ) -> CommunityRiskProfile | None:
        stmt = select(CommunityRiskProfile).where(
            CommunityRiskProfile.scope_type == scope_type,
            CommunityRiskProfile.scope_id == scope_id,
            CommunityRiskProfile.risk_type == risk_type,
        )
        if before_date is not None:
            stmt = stmt.where(CommunityRiskProfile.stat_window_end < before_date)
        stmt = stmt.order_by(desc(CommunityRiskProfile.stat_window_end), desc(CommunityRiskProfile.created_at)).limit(1)
        return self.db.scalar(stmt)

    def upsert_profile(
        self,
        *,
        scope_type: str,
        scope_id: str,
        risk_type: str,
        stat_window_start: date,
        stat_window_end: date,
        payload: dict,
    ) -> CommunityRiskProfile:
        stmt = select(CommunityRiskProfile).where(
            CommunityRiskProfile.scope_type == scope_type,
            CommunityRiskProfile.scope_id == scope_id,
            CommunityRiskProfile.risk_type == risk_type,
            CommunityRiskProfile.stat_window_start == stat_window_start,
            CommunityRiskProfile.stat_window_end == stat_window_end,
        )
        existing = self.db.scalar(stmt)
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            obj = existing
        else:
            obj = CommunityRiskProfile(**payload)
            self.db.add(obj)
        self.db.flush()
        return obj

    def create_alert(self, payload: dict) -> AlertEvent:
        stmt = select(AlertEvent).where(
            AlertEvent.scope_type == payload.get('scope_type'),
            AlertEvent.scope_id == payload.get('scope_id'),
            AlertEvent.risk_type == payload.get('risk_type'),
            AlertEvent.alert_code == payload.get('alert_code'),
            AlertEvent.current_level == payload.get('current_level'),
            AlertEvent.status == payload.get('status', AlertStatus.active.value),
        )
        profile_id = payload.get('profile_id')
        if profile_id:
            stmt = stmt.where(AlertEvent.profile_id == profile_id)
        existing = self.db.scalar(stmt.limit(1))
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            obj = existing
        else:
            obj = AlertEvent(**payload)
            self.db.add(obj)
        self.db.flush()
        return obj

    def list_alerts(
        self,
        *,
        limit: int = 20,
        status: str | None = None,
        scope_type: str | None = None,
        community_id: str | None = None,
        risk_type: str | None = None,
        dashboard_visible_only: bool = True,
    ) -> list[AlertEvent]:
        stmt = select(AlertEvent).order_by(desc(AlertEvent.created_at))
        if status:
            stmt = stmt.where(AlertEvent.status == status)
        if scope_type:
            stmt = stmt.where(AlertEvent.scope_type == scope_type)
        if community_id:
            stmt = stmt.where(AlertEvent.community_id == community_id)
        if risk_type:
            stmt = stmt.where(AlertEvent.risk_type == risk_type)
        if dashboard_visible_only:
            stmt = stmt.where(AlertEvent.dashboard_visible.is_(True))
        stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_profiles(self, *, limit: int = 100, scope_type: str | None = None, community_id: str | None = None) -> list[CommunityRiskProfile]:
        stmt = select(CommunityRiskProfile).order_by(desc(CommunityRiskProfile.stat_window_end), desc(CommunityRiskProfile.risk_score))
        if scope_type:
            stmt = stmt.where(CommunityRiskProfile.scope_type == scope_type)
        if community_id:
            stmt = stmt.where(CommunityRiskProfile.community_id == community_id)
        stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_latest_profiles_by_scope(self, *, scope_type: str, limit: int = 100) -> list[CommunityRiskProfile]:
        # 演示版：直接按时间倒序取较新 profile，再由 service 侧去重
        stmt = (
            select(CommunityRiskProfile)
            .where(CommunityRiskProfile.scope_type == scope_type)
            .order_by(desc(CommunityRiskProfile.stat_window_end), desc(CommunityRiskProfile.risk_score), desc(CommunityRiskProfile.created_at))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def deactivate_alert(self, alert_id: str) -> AlertEvent | None:
        alert = self.db.get(AlertEvent, alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.closed.value
        self.db.flush()
        return alert
