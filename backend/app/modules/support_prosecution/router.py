from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db.session import get_db
from app.modules.support_prosecution.schemas import CaseCreate
from app.modules.support_prosecution.service import SupportProsecutionService


router = APIRouter(prefix="/support-prosecution", tags=["support-prosecution"])


@router.post("/cases")
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    service = SupportProsecutionService(db)
    return ok(service.create_case(payload), message="support prosecution case create success")


@router.get("/cases/{case_id}")
def get_case_detail(case_id: int, db: Session = Depends(get_db)):
    service = SupportProsecutionService(db)
    return ok(service.get_case_detail(case_id), message="support prosecution case get success")


@router.get("/cases/{case_id}/complaint-context")
def get_complaint_context(case_id: int, db: Session = Depends(get_db)):
    service = SupportProsecutionService(db)
    return ok(service.get_complaint_context(case_id), message="complaint context get success")
