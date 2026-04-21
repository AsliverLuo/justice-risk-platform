from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.enums import ScopeType
from app.core.logger import get_logger
from app.modules.propaganda.repository import PropagandaRepository
from app.modules.propaganda.rules import expand_context_tags, score_article_match
from app.modules.propaganda.schemas import (
    PropagandaArticleBatchUpsertRequest,
    PropagandaArticleListResponse,
    PropagandaArticleRead,
    PropagandaPushListRequest,
    PropagandaPushListResponse,
    PropagandaPushRead,
    PropagandaRecommendRequest,
    PropagandaRecommendResponse,
)

logger = get_logger(__name__)


class PropagandaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PropagandaRepository(db)

    def batch_upsert_articles(self, payload: PropagandaArticleBatchUpsertRequest) -> PropagandaArticleListResponse:
        items = [PropagandaArticleRead.model_validate(self.repo.upsert_article(item.model_dump())) for item in payload.items]
        self.db.commit()
        return PropagandaArticleListResponse(items=items)

    def list_articles(self, *, limit: int = 20, risk_type: str | None = None) -> PropagandaArticleListResponse:
        records = self.repo.list_articles(limit=limit, risk_type=risk_type)
        return PropagandaArticleListResponse(items=[PropagandaArticleRead.model_validate(item) for item in records])

    def list_pushes(self, payload: PropagandaPushListRequest) -> PropagandaPushListResponse:
        records = self.repo.list_pushes(
            limit=payload.limit,
            alert_id=payload.alert_id,
            profile_id=payload.profile_id,
            scope_type=payload.scope_type,
            scope_id=payload.scope_id,
            risk_type=payload.risk_type,
            dashboard_visible_only=payload.dashboard_visible_only,
        )
        return PropagandaPushListResponse(items=[PropagandaPushRead.model_validate(item) for item in records])

    def recommend(self, payload: PropagandaRecommendRequest) -> PropagandaRecommendResponse:
        alert = self.repo.get_alert(payload.alert_id) if payload.alert_id else None
        profile = self.repo.get_profile(payload.profile_id) if payload.profile_id else None
        if profile is None and payload.scope_type and payload.scope_id:
            profile = self.repo.get_latest_profile_by_scope(
                scope_type=payload.scope_type,
                scope_id=payload.scope_id,
                risk_type=payload.risk_type,
            )
        if profile is None and alert is not None:
            profile = self.repo.get_latest_profile_by_scope(
                scope_type=alert.scope_type,
                scope_id=alert.scope_id,
                risk_type=alert.risk_type,
            )

        resolved_scope_type = (profile.scope_type if profile else None) or (alert.scope_type if alert else None) or payload.scope_type or ScopeType.community.value
        resolved_scope_id = (profile.scope_id if profile else None) or (alert.scope_id if alert else None) or payload.scope_id or 'unknown-scope'
        resolved_scope_name = (profile.scope_name if profile else None) or (alert.scope_name if alert else None) or resolved_scope_id
        resolved_risk_type = (profile.risk_type if profile else None) or (alert.risk_type if alert else None) or payload.risk_type or 'other'

        context_tags = expand_context_tags(
            risk_type=resolved_risk_type,
            context_tags=payload.context_tags + (profile.triggered_rules if profile else []) + ([alert.alert_code] if alert else []),
            alert_code=alert.alert_code if alert else None,
        )
        related_law_names = []
        for item in payload.related_law_names:
            item = str(item).strip()
            if item and item not in related_law_names:
                related_law_names.append(item)

        recent_cases = self.repo.list_recent_cases(
            scope_type=resolved_scope_type,
            scope_id=resolved_scope_id,
            risk_type=resolved_risk_type,
            limit=5,
        )
        for case in recent_cases:
            meta = case.extra_meta or {}
            for key in ['scenario_tags', 'risk_tags']:
                for tag in meta.get(key, []) or []:
                    tag = str(tag).strip()
                    if tag and tag not in context_tags:
                        context_tags.append(tag)

        articles = self.repo.list_articles(limit=max(payload.limit * 6, 30), risk_type=resolved_risk_type)
        ranked: list[tuple[float, dict, object]] = []
        for article in articles:
            ranking = score_article_match(
                article,
                risk_type=resolved_risk_type,
                context_tags=context_tags,
                related_law_names=related_law_names,
                scope_type=resolved_scope_type,
            )
            if ranking['score'] <= 0:
                continue
            ranked.append((ranking['score'], ranking, article))

        ranked.sort(key=lambda item: (item[0], getattr(item[2], 'hot_score', 0.0), getattr(item[2], 'priority', 0)), reverse=True)
        selected = ranked[: payload.limit]

        push_items = []
        article_items = []
        for _, ranking, article in selected:
            article_read = PropagandaArticleRead.model_validate(article)
            article_items.append(article_read)
            record_payload = {
                'profile_id': profile.id if profile else payload.profile_id,
                'alert_id': alert.id if alert else payload.alert_id,
                'community_id': getattr(profile, 'community_id', None) or getattr(alert, 'community_id', None),
                'community_name': getattr(profile, 'community_name', None) or getattr(alert, 'community_name', None),
                'street_id': getattr(profile, 'street_id', None) or getattr(alert, 'street_id', None),
                'street_name': getattr(profile, 'street_name', None) or getattr(alert, 'street_name', None),
                'scope_type': resolved_scope_type,
                'scope_id': resolved_scope_id,
                'scope_name': resolved_scope_name,
                'risk_type': resolved_risk_type,
                'article_id': article.id,
                'article_code': article.article_code,
                'title': article.title,
                'summary': article.summary,
                'recommendation_score': ranking['score'],
                'matched_risk_types': ranking['matched_risk_types'],
                'matched_scenario_tags': ranking['matched_scenario_tags'],
                'related_law_names': article.related_law_names or [],
                'match_reason': ranking['match_reason'],
                'source_mode': 'rule_rank',
                'dashboard_visible': payload.dashboard_visible,
                'status': 'active',
                'extra_meta': {
                    'used_context_tags': context_tags,
                    'used_related_law_names': related_law_names,
                },
            }
            if payload.persist:
                record = self.repo.upsert_push(record_payload)
                push_items.append(PropagandaPushRead.model_validate(record))
            else:
                push_items.append(PropagandaPushRead(id=f'temp:{resolved_scope_id}:{article.article_code}', **record_payload))

        if payload.persist:
            self.db.commit()
        else:
            self.db.rollback()

        return PropagandaRecommendResponse(
            items=push_items,
            articles=article_items,
            resolved_scope_type=resolved_scope_type,
            resolved_scope_id=resolved_scope_id,
            resolved_scope_name=resolved_scope_name,
            resolved_risk_type=resolved_risk_type,
            used_context_tags=context_tags,
            used_related_law_names=related_law_names,
            source_mode='rule_rank',
        )
