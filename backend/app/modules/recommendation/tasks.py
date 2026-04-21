from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.recommendation.schemas import RecommendationGenerateRequest
from app.modules.recommendation.service import RecommendationService


def generate_recommendation_task(db: Session, payload: RecommendationGenerateRequest):
    service = RecommendationService(db)
    return service.generate(payload)
