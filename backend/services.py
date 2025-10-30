from __future__ import annotations

from typing import List
from backend.repositories import SelectionRepository
from backend.models import RecommendationItem
from ai_algorithm_teacher import build_recommendations
from backend.monitoring import ALGORITHM_TOP_SELECTIONS
from backend.logging_config import get_logger


class RecommendationService:
    def __init__(self, repo: SelectionRepository) -> None:
        self._repo = repo

    async def recommend(self, prompt: str) -> List[RecommendationItem]:
        log = get_logger("service")
        recs = build_recommendations(prompt)
        # Persist the top algorithm as the selected usage for reporting
        if recs:
            top = recs[0]
            await self._repo.add_selection(top.algorithm, prompt)
            ALGORITHM_TOP_SELECTIONS.labels(algorithm=top.algorithm).inc()
            log.info("top_recommendation", algorithm=top.algorithm, score=top.score)
        # Convert to DTOs
        items: List[RecommendationItem] = [
            RecommendationItem(
                algorithm=r.algorithm,
                score=r.score,
                rationale=r.rationale,
                when_to_use=r.when_to_use,
                pros=r.pros,
                cons=r.cons,
                typical_steps=r.typical_steps,
                resources=r.resources,
            )
            for r in recs
        ]
        return items


