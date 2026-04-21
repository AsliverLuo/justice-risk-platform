from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db.session import get_db
from app.modules.alert.schemas import AlertListRequest, CommunityRiskEngineRequest
from app.modules.alert.service import AlertService


router = APIRouter(prefix='/alerts', tags=['alerts'])


@router.post('/engine/run')
def run_alert_engine(payload: CommunityRiskEngineRequest, db: Session = Depends(get_db)):
    service = AlertService(db)
    return ok(service.run_engine(payload))


@router.get('')
def list_alerts(
    limit: int = Query(default=20, ge=1, le=200),
    status: str | None = None,
    scope_type: str | None = None,
    community_id: str | None = None,
    risk_type: str | None = None,
    dashboard_visible_only: bool = True,
    db: Session = Depends(get_db),
):
    service = AlertService(db)
    payload = AlertListRequest(
        limit=limit,
        status=status,
        scope_type=scope_type,
        community_id=community_id,
        risk_type=risk_type,
        dashboard_visible_only=dashboard_visible_only,
    )
    return ok(service.list_alerts(payload))


@router.get('/profiles')
def list_profiles(
    limit: int = Query(default=100, ge=1, le=500),
    scope_type: str | None = None,
    community_id: str | None = None,
    db: Session = Depends(get_db),
):
    service = AlertService(db)
    return ok(service.list_profiles(limit=limit, scope_type=scope_type, community_id=community_id))
