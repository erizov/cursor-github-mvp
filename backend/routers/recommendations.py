from fastapi import APIRouter, Depends
from backend.models import RecommendRequest, RecommendResponse
from backend.repositories import MongoSelectionRepository, MongoUniqueRequestRepository
from backend.services import RecommendationService
from backend.db import get_db
from backend.monitoring import RECOMMENDATIONS_TOTAL
from backend.logging_config import get_logger


router = APIRouter(tags=["recommendations"])


async def get_service():
    db = get_db()
    repo = MongoSelectionRepository(db)
    unique_repo = MongoUniqueRequestRepository(db)
    return RecommendationService(repo, unique_repo)


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(body: RecommendRequest, svc: RecommendationService = Depends(get_service)):
    log = get_logger("recommend")
    RECOMMENDATIONS_TOTAL.inc()
    # Avoid logging full prompt; log hash length only
    prompt_len = len(body.prompt)
    log.info("recommend_request", prompt_length=prompt_len)
    items = await svc.recommend(body.prompt)
    return RecommendResponse(recommendations=items)


