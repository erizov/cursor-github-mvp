import os

from fastapi import APIRouter, Depends
from backend.models import RecommendRequest, RecommendResponse
from backend.repositories import (
    MongoSelectionRepository,
    MongoUniqueRequestRepository,
    InMemorySelectionRepository,
    InMemoryUniqueRequestRepository,
    PostgresSelectionRepository,
    PostgresUniqueRequestRepository,
    MemcachedSelectionRepository,
    MemcachedUniqueRequestRepository,
    Neo4jSelectionRepository,
    Neo4jUniqueRequestRepository,
    CassandraSelectionRepository,
    CassandraUniqueRequestRepository,
)
from backend.services import RecommendationService
from backend.db import (
    get_db, get_postgres_pool, get_memcached_client,
    get_neo4j_driver, get_cassandra_session
)
from backend.monitoring import RECOMMENDATIONS_TOTAL
from backend.logging_config import get_logger


router = APIRouter(tags=["recommendations"])


async def get_service():
    backend_type = os.getenv("BACKEND_TYPE", "inmemory").lower()
    
    if backend_type == "inmemory":
        repo = InMemorySelectionRepository.get_instance()
        unique_repo = InMemoryUniqueRequestRepository.get_instance()
        return RecommendationService(repo, unique_repo)
    elif backend_type == "mongodb":
        db = get_db()
        repo = MongoSelectionRepository(db)
        unique_repo = MongoUniqueRequestRepository(db)
        return RecommendationService(repo, unique_repo)
    elif backend_type == "postgres" or backend_type == "postgresql":
        pool = await get_postgres_pool()
        repo = PostgresSelectionRepository(pool)
        unique_repo = PostgresUniqueRequestRepository(pool)
        return RecommendationService(repo, unique_repo)
    elif backend_type == "memcached":
        client = await get_memcached_client()
        repo = MemcachedSelectionRepository(client)
        unique_repo = MemcachedUniqueRequestRepository(client)
        return RecommendationService(repo, unique_repo)
    elif backend_type == "neo4j":
        driver = await get_neo4j_driver()
        repo = Neo4jSelectionRepository(driver)
        unique_repo = Neo4jUniqueRequestRepository(driver)
        return RecommendationService(repo, unique_repo)
    elif backend_type == "cassandra":
        session, executor = get_cassandra_session()
        repo = CassandraSelectionRepository(session, executor)
        unique_repo = CassandraUniqueRequestRepository(session, executor)
        return RecommendationService(repo, unique_repo)
    else:
        # Default to in-memory
        repo = InMemorySelectionRepository.get_instance()
        unique_repo = InMemoryUniqueRequestRepository.get_instance()
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


