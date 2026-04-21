from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db.session import get_db
from app.modules.knowledge.schemas import (
    KnowledgeBatchUpsertRequest,
    KnowledgeSearchRequest,
)
from app.modules.knowledge.service import LegalKnowledgeService


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/batch-upsert")
def batch_upsert_knowledge(
    payload: KnowledgeBatchUpsertRequest,
    db: Session = Depends(get_db),
):
    service = LegalKnowledgeService(db)
    result = service.batch_upsert(payload)
    return ok(data=result, message="legal knowledge batch upsert success")


@router.post("/search")
def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
):
    service = LegalKnowledgeService(db)
    result = service.search(payload)
    return ok(data=result, message="legal knowledge search success")


@router.get("/{knowledge_id}")
def get_knowledge(
    knowledge_id: str,
    db: Session = Depends(get_db),
):
    service = LegalKnowledgeService(db)
    result = service.get(knowledge_id)
    if not result:
        raise HTTPException(status_code=404, detail="knowledge item not found")
    return ok(data=result, message="legal knowledge get success")
