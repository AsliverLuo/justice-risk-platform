from fastapi import APIRouter

from app.modules.alert.router import router as alert_router
from app.modules.analysis.router import router as analysis_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.document_gen.router import router as document_gen_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.propaganda.router import router as propaganda_router
from app.modules.recommendation.router import router as recommendation_router
from app.modules.support_prosecution.router import router as support_prosecution_router
from app.modules.workflow.router import router as workflow_router


api_router = APIRouter()
api_router.include_router(knowledge_router)
api_router.include_router(analysis_router)
api_router.include_router(alert_router)
api_router.include_router(dashboard_router)
api_router.include_router(recommendation_router)
api_router.include_router(propaganda_router)
api_router.include_router(support_prosecution_router)
api_router.include_router(document_gen_router)
api_router.include_router(workflow_router)
