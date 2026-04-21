from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.propaganda.schemas import PropagandaRecommendRequest
from app.modules.propaganda.service import PropagandaService


def run_propaganda_recommendation(db: Session, payload: PropagandaRecommendRequest):
    service = PropagandaService(db)
    return service.recommend(payload)
