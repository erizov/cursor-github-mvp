#!/usr/bin/env python3
"""
Seed MongoDB with 1000 unique AI/ML prompts from generate_prompts.py.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import get_db
from backend.repositories import MongoUniqueRequestRepository
from ai_algorithm_teacher import build_recommendations


def get_algorithm_type_from_prompt(prompt: str) -> str:
    """Determine algorithm type from prompt using recommendation engine."""
    recs = build_recommendations(prompt)
    if not recs:
        return "Other"
    
    top_algorithm = recs[0].algorithm
    alg_lower = top_algorithm.lower()
    
    # Map algorithm to type
    if any(x in alg_lower for x in ["logistic", "svm", "random forest (classification)", "naive bayes", "knn"]) and "regression" not in alg_lower:
        return "Classification"
    elif any(x in alg_lower for x in ["linear regression", "random forest (regression)"]):
        return "Regression"
    elif any(x in alg_lower for x in ["k-means", "dbscan"]):
        return "Clustering"
    elif any(x in alg_lower for x in ["pca", "t-sne", "umap"]):
        return "Dimensionality Reduction"
    elif any(x in alg_lower for x in ["arima", "prophet"]):
        return "Time Series"
    elif any(x in alg_lower for x in ["lstm", "temporal cnn"]):
        return "Sequence Models"
    elif any(x in alg_lower for x in ["bert", "roberta", "text"]):
        return "NLP"
    elif any(x in alg_lower for x in ["object detection", "yolo", "faster r-cnn"]):
        return "Computer Vision Detection"
    elif any(x in alg_lower for x in ["cnn", "vision"]) and "detection" not in alg_lower:
        return "Vision"
    elif any(x in alg_lower for x in ["anomaly", "isolation forest", "one-class"]):
        return "Anomaly Detection"
    elif any(x in alg_lower for x in ["recsys", "recommend", "matrix factorization", "two-tower"]):
        return "Recommender Systems"
    elif any(x in alg_lower for x in ["reinforcement", "dqn", "ppo"]):
        return "Reinforcement Learning"
    elif any(x in alg_lower for x in ["causal", "dowhy", "ate"]):
        return "Causal Inference"
    elif "gradient boosting" in alg_lower or "xgboost" in alg_lower or "lightgbm" in alg_lower or "catboost" in alg_lower:
        return "Ensemble Methods"
    elif any(x in alg_lower for x in ["optimization", "genetic", "simulated annealing"]):
        return "Optimization"
    elif any(x in alg_lower for x in ["graph", "gnn", "graph neural"]):
        return "Graph Algorithms"
    elif any(x in alg_lower for x in ["transfer", "fine-tun", "pretrain"]):
        return "Transfer Learning"
    elif any(x in alg_lower for x in ["gan", "vae", "generative", "diffusion"]):
        return "Generative Models"
    elif any(x in alg_lower for x in ["generation", "summariz", "text generation"]):
        return "Natural Language Generation"
    else:
        return "Other"


async def seed_database():
    """Seed database with prompts from generate_prompts.py."""
    # Import generate_prompts
    from scripts.generate_prompts import generate_all_prompts
    
    db = get_db()
    repo = MongoUniqueRequestRepository(db)
    
    prompts = generate_all_prompts()
    
    added = 0
    skipped = 0
    
    print(f"Seeding database with {len(prompts)} prompts...")
    
    for prompt, algo_type in prompts:
        # Use the algorithm type from the generator, but verify with recommendation engine
        # If different, use the one from recommendation engine for accuracy
        detected_type = get_algorithm_type_from_prompt(prompt)
        final_type = detected_type if detected_type != "Other" else algo_type
        
        success = await repo.add_unique_request(prompt, final_type)
        if success:
            added += 1
            if added % 100 == 0:
                print(f"Added {added} prompts...")
        else:
            skipped += 1
    
    print(f"\nSeeding complete!")
    print(f"Added: {added}")
    print(f"Skipped (duplicates): {skipped}")
    
    # Show counts by type
    counts = await repo.count_by_type()
    print(f"\nCounts by algorithm type:")
    for item in counts:
        print(f"  {item['algorithm_type']}: {item['count']}")


if __name__ == "__main__":
    asyncio.run(seed_database())

