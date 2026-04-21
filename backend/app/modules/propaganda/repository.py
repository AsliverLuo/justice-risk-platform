from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.modules.alert.models import AlertEvent, CommunityRiskProfile
from app.modules.analysis.models import CaseCorpus
from app.modules.propaganda.models import PropagandaArticle, PropagandaPushRecord


class PropagandaRepository:
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
                current_scope_id = meta.get('community_id') or meta.get('community_name')
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

    def upsert_article(self, payload: dict) -> PropagandaArticle:
        existing = None
        article_id = payload.get('id')
        article_code = payload.get('article_code')
        if article_id:
            existing = self.db.get(PropagandaArticle, article_id)
        if existing is None and article_code:
            stmt = select(PropagandaArticle).where(PropagandaArticle.article_code == article_code).limit(1)
            existing = self.db.scalar(stmt)
        if existing:
            for key, value in payload.items():
                if key == 'id':
                    continue
                setattr(existing, key, value)
            obj = existing
        else:
            payload = {k: v for k, v in payload.items() if k != 'id'}
            obj = PropagandaArticle(**payload)
            self.db.add(obj)
        self.db.flush()
        return obj

    def list_articles(self, *, limit: int = 50, enabled_only: bool = True, publish_status: str | None = 'published', risk_type: str | None = None) -> list[PropagandaArticle]:
        stmt = select(PropagandaArticle).order_by(desc(PropagandaArticle.priority), desc(PropagandaArticle.hot_score), desc(PropagandaArticle.updated_at))
        if enabled_only:
            stmt = stmt.where(PropagandaArticle.enabled.is_(True))
        if publish_status:
            stmt = stmt.where(PropagandaArticle.publish_status == publish_status)
        records = list(self.db.scalars(stmt.limit(max(limit * 5, 50))).all())
        if not risk_type:
            return records[:limit]
        matched = []
        for item in records:
            if not item.risk_types or risk_type in (item.risk_types or []) or 'other' in (item.risk_types or []):
                matched.append(item)
            if len(matched) >= limit:
                break
        return matched

    def upsert_push(self, payload: dict) -> PropagandaPushRecord:
        stmt = select(PropagandaPushRecord)
        if payload.get('alert_id'):
            stmt = stmt.where(
                PropagandaPushRecord.alert_id == payload['alert_id'],
                PropagandaPushRecord.article_id == payload['article_id'],
            )
        elif payload.get('profile_id'):
            stmt = stmt.where(
                PropagandaPushRecord.profile_id == payload['profile_id'],
                PropagandaPushRecord.article_id == payload['article_id'],
            )
        else:
            stmt = stmt.where(
                PropagandaPushRecord.scope_type == payload.get('scope_type'),
                PropagandaPushRecord.scope_id == payload.get('scope_id'),
                PropagandaPushRecord.risk_type == payload.get('risk_type'),
                PropagandaPushRecord.article_id == payload.get('article_id'),
            )
        existing = self.db.scalar(stmt.limit(1))
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            obj = existing
        else:
            obj = PropagandaPushRecord(**payload)
            self.db.add(obj)
        self.db.flush()
        return obj

    def list_pushes(self, *, limit: int = 20, alert_id: str | None = None, profile_id: str | None = None, scope_type: str | None = None, scope_id: str | None = None, risk_type: str | None = None, dashboard_visible_only: bool = True) -> list[PropagandaPushRecord]:
        stmt = select(PropagandaPushRecord).order_by(desc(PropagandaPushRecord.created_at), desc(PropagandaPushRecord.recommendation_score))
        if alert_id:
            stmt = stmt.where(PropagandaPushRecord.alert_id == alert_id)
        if profile_id:
            stmt = stmt.where(PropagandaPushRecord.profile_id == profile_id)
        if scope_type:
            stmt = stmt.where(PropagandaPushRecord.scope_type == scope_type)
        if scope_id:
            stmt = stmt.where(PropagandaPushRecord.scope_id == scope_id)
        if risk_type:
            stmt = stmt.where(PropagandaPushRecord.risk_type == risk_type)
        if dashboard_visible_only:
            stmt = stmt.where(PropagandaPushRecord.dashboard_visible.is_(True))
        stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())
