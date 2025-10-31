from __future__ import annotations

from typing import List, Optional
from backend.repositories import SelectionRepository, UniqueRequestRepository
from backend.models import RecommendationItem
from ai_algorithm_teacher import build_recommendations
from backend.monitoring import ALGORITHM_TOP_SELECTIONS
from backend.logging_config import get_logger


def get_algorithm_type_from_algorithm(algorithm: str) -> str:
    """Map algorithm name to algorithm type category."""
    alg_lower = algorithm.lower()
    if any(x in alg_lower for x in ["logistic", "svm", "random forest (classification)", "naive bayes", "knn"]):
        return "Classification"
    elif "bert" in alg_lower or "roberta" in alg_lower or "text" in alg_lower:
        return "NLP"
    elif any(x in alg_lower for x in ["linear regression", "random forest (regression)", "gradient boosting"]):
        return "Regression"
    elif any(x in alg_lower for x in ["k-means", "dbscan"]):
        return "Clustering"
    elif any(x in alg_lower for x in ["pca", "t-sne", "umap"]):
        return "Dimensionality Reduction"
    elif any(x in alg_lower for x in ["arima", "prophet", "lstm", "temporal"]):
        return "Time Series"
    elif any(x in alg_lower for x in ["cnn", "vision", "object detection", "yolo"]):
        return "Vision"
    elif any(x in alg_lower for x in ["anomaly", "isolation forest", "one-class"]):
        return "Anomaly Detection"
    elif any(x in alg_lower for x in ["recsys", "recommend", "matrix factorization"]):
        return "Recommender Systems"
    elif any(x in alg_lower for x in ["reinforcement", "dqn", "ppo"]):
        return "Reinforcement Learning"
    elif any(x in alg_lower for x in ["causal", "dowhy", "ate"]):
        return "Causal Inference"
    else:
        return "Other"


class RecommendationService:
    def __init__(self, repo: SelectionRepository, unique_repo: Optional[UniqueRequestRepository] = None) -> None:
        self._repo = repo
        self._unique_repo = unique_repo

    async def recommend(self, prompt: str) -> List[RecommendationItem]:
        log = get_logger("service")
        recs = build_recommendations(prompt)
        # Persist the top algorithm as the selected usage for reporting
        if recs:
            top = recs[0]
            await self._repo.add_selection(top.algorithm, prompt)
            ALGORITHM_TOP_SELECTIONS.labels(algorithm=top.algorithm).inc()
            log.info("top_recommendation", algorithm=top.algorithm, score=top.score)
            
            # Store unique request if unique_repo is provided
            if self._unique_repo:
                algorithm_type = get_algorithm_type_from_algorithm(top.algorithm)
                await self._unique_repo.add_unique_request(prompt, algorithm_type)
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


