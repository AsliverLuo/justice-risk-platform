from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db.session import get_db
from app.modules.document_gen.schemas import DocumentGenerateRequest
from app.modules.document_gen.service import DocumentGenerationService


router = APIRouter(prefix="/document-gen", tags=["document-gen"])


@router.post("/support-prosecution/cases/{case_id}")
def generate_support_prosecution_documents(
    case_id: int,
    payload: DocumentGenerateRequest,
    db: Session = Depends(get_db),
):
    service = DocumentGenerationService(db)
    return ok(service.generate(case_id, payload.document_types), message="documents generated")
