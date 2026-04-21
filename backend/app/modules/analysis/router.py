from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db.session import get_db
from app.modules.analysis.schemas import (
    CaseCorpusBatchUpsertRequest,
    CaseTextAnalyzeRequest,
    CorpusSearchRequest,
    RiskScoreRequest,
)
from app.modules.analysis.service import AnalysisService


router = APIRouter(prefix='/analysis', tags=['analysis'])


@router.post('/corpus/batch-upsert')
def batch_upsert_corpus(payload: CaseCorpusBatchUpsertRequest, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    result = service.batch_upsert_corpus(payload)
    return ok(data=result, message='case corpus batch upsert success')


@router.post('/corpus/search')
def search_corpus(payload: CorpusSearchRequest, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    result = service.search_corpus(payload)
    return ok(data=result, message='case corpus search success')


@router.get('/corpus/{case_id}')
def get_corpus(case_id: str, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    result = service.get_case(case_id)
    if not result:
        raise HTTPException(status_code=404, detail='case corpus item not found')
    return ok(data=result, message='case corpus get success')


@router.post('/text')
def analyze_case_text(payload: CaseTextAnalyzeRequest, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    result = service.analyze_text(payload)
    return ok(data=result, message='case text analyze success')


@router.post('/risk-score')
def score_risk(payload: RiskScoreRequest, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    result = service.score_risk(payload)
    return ok(data=result, message='risk score success')
