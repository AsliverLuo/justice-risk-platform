from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db.session import get_db
from app.modules.recommendation.schemas import (
    RecommendationGenerateRequest,
    RecommendationListRequest,
    RecommendationTemplateBatchUpsertRequest,
)
from app.modules.recommendation.service import RecommendationService


router = APIRouter(prefix='/recommendations', tags=['recommendations'])


@router.post('/generate')
def generate_recommendation(payload: RecommendationGenerateRequest, db: Session = Depends(get_db)):
    service = RecommendationService(db)
    return ok(service.generate(payload))


@router.get('')
def list_recommendations(
    limit: int = Query(default=20, ge=1, le=200),
    alert_id: str | None = None,
    profile_id: str | None = None,
    scope_type: str | None = None,
    scope_id: str | None = None,
    risk_type: str | None = None,
    dashboard_visible_only: bool = True,
    db: Session = Depends(get_db),
):
    service = RecommendationService(db)
    payload = RecommendationListRequest(
        limit=limit,
        alert_id=alert_id,
        profile_id=profile_id,
        scope_type=scope_type,
        scope_id=scope_id,
        risk_type=risk_type,
        dashboard_visible_only=dashboard_visible_only,
    )
    return ok(service.list_recommendations(payload))


@router.get('/templates')
def list_templates(
    risk_type: str | None = None,
    alert_code: str | None = None,
    scope_type: str | None = None,
    current_level: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = RecommendationService(db)
    return ok(service.list_templates(
        risk_type=risk_type,
        alert_code=alert_code,
        scope_type=scope_type,
        current_level=current_level,
        limit=limit,
    ))


@router.post('/templates/batch-upsert')
def batch_upsert_templates(payload: RecommendationTemplateBatchUpsertRequest, db: Session = Depends(get_db)):
    service = RecommendationService(db)
    return ok(service.batch_upsert_templates(payload))
