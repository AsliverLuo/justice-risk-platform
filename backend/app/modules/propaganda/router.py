from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db.session import get_db
from app.modules.propaganda.schemas import (
    PropagandaArticleBatchUpsertRequest,
    PropagandaPushListRequest,
    PropagandaRecommendRequest,
)
from app.modules.propaganda.service import PropagandaService


router = APIRouter(prefix='/propaganda', tags=['propaganda'])


@router.post('/recommend')
def recommend_propaganda(payload: PropagandaRecommendRequest, db: Session = Depends(get_db)):
    service = PropagandaService(db)
    return ok(service.recommend(payload))


@router.get('/pushes')
def list_pushes(
    limit: int = Query(default=20, ge=1, le=200),
    alert_id: str | None = None,
    profile_id: str | None = None,
    scope_type: str | None = None,
    scope_id: str | None = None,
    risk_type: str | None = None,
    dashboard_visible_only: bool = True,
    db: Session = Depends(get_db),
):
    service = PropagandaService(db)
    payload = PropagandaPushListRequest(
        limit=limit,
        alert_id=alert_id,
        profile_id=profile_id,
        scope_type=scope_type,
        scope_id=scope_id,
        risk_type=risk_type,
        dashboard_visible_only=dashboard_visible_only,
    )
    return ok(service.list_pushes(payload))


@router.get('/articles')
def list_articles(limit: int = Query(default=20, ge=1, le=200), risk_type: str | None = None, db: Session = Depends(get_db)):
    service = PropagandaService(db)
    return ok(service.list_articles(limit=limit, risk_type=risk_type))


@router.post('/articles/batch-upsert')
def batch_upsert_articles(payload: PropagandaArticleBatchUpsertRequest, db: Session = Depends(get_db)):
    service = PropagandaService(db)
    return ok(service.batch_upsert_articles(payload))
