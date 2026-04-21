from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db.session import get_db
from app.modules.dashboard.service import DashboardService


router = APIRouter(prefix='/dashboard', tags=['dashboard'])


@router.get('/overview')
def dashboard_overview(
    scope_type: str = Query(default='community'),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return ok(service.overview(scope_type=scope_type, limit=limit))


@router.get('/risk-map')
def dashboard_risk_map(limit: int = Query(default=500, ge=1, le=2000), db: Session = Depends(get_db)):
    service = DashboardService(db)
    return ok(service.risk_map(limit=limit))


@router.get('/workflow-cases')
def dashboard_workflow_cases(
    stage: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return ok(service.workflow_cases(stage=stage, limit=limit))


@router.get('/defendant-cases')
def dashboard_defendant_cases(
    defendant: str,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return ok(service.defendant_cases(defendant=defendant, limit=limit))


@router.get('/community-streets')
def dashboard_community_streets(
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return ok(service.community_streets(limit=limit))


@router.get('/street-cases')
def dashboard_street_cases(
    street: str,
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return ok(service.street_cases(street=street, limit=limit))


@router.get('/street-profile')
def dashboard_street_profile(
    street: str,
    prefer_llm: bool = Query(default=True),
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return ok(service.street_profile(street=street, prefer_llm=prefer_llm, limit=limit))


@router.get('/alerts/realtime')
def dashboard_realtime_alerts(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    service = DashboardService(db)
    overview = service.overview(limit=limit)
    return ok({'latest_alerts': overview.latest_alerts})


@router.get('/recommendations/latest')
def dashboard_latest_recommendations(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    service = DashboardService(db)
    return ok({'latest_recommendations': service.latest_recommendations(limit=limit)})


@router.get('/propaganda/latest')
def dashboard_latest_propaganda(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    service = DashboardService(db)
    return ok({'latest_propaganda': service.latest_propaganda(limit=limit)})
