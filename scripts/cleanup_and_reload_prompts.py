#!/usr/bin/env python3
"""
Cleanup all prompts tables/collections in all databases and reload them from prompts.txt.

This script:
1. Deletes all records from selections and unique_requests tables in all backends
2. Reads prompts from prompts.txt
3. Seeds all databases with fresh prompt data
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import (
    get_db, get_postgres_pool, get_memcached_client,
    get_neo4j_driver, get_cassandra_session
)
from backend.repositories import (
    MongoSelectionRepository, MongoUniqueRequestRepository,
    InMemorySelectionRepository, InMemoryUniqueRequestRepository,
    PostgresSelectionRepository, PostgresUniqueRequestRepository,
    Neo4jSelectionRepository, Neo4jUniqueRequestRepository,
    CassandraSelectionRepository, CassandraUniqueRequestRepository,
)
from ai_algorithm_teacher import build_recommendations


async def cleanup_mongodb() -> tuple[int, int]:
    """Delete all records from MongoDB collections."""
    db = get_db()
    selections_col = db["selections"]
    unique_requests_col = db["unique_requests"]
    
    result1 = await selections_col.delete_many({})
    result2 = await unique_requests_col.delete_many({})
    
    return result1.deleted_count, result2.deleted_count


async def cleanup_postgres() -> tuple[int, int]:
    """Delete all records from PostgreSQL tables."""
    pool = await get_postgres_pool()
    
    async with pool.acquire() as conn:
        result1 = await conn.execute("DELETE FROM selections")
        result2 = await conn.execute("DELETE FROM unique_requests")
        
        selections_count = int(result1.split()[-1])
        unique_requests_count = int(result2.split()[-1])
    
    return selections_count, unique_requests_count


async def cleanup_inmemory() -> tuple[int, int]:
    """Clear in-memory repositories."""
    selection_repo = InMemorySelectionRepository.get_instance()
    unique_repo = InMemoryUniqueRequestRepository.get_instance()
    
    selections_count = len(selection_repo._items)
    unique_requests_count = len(unique_repo._items)
    
    selection_repo._items = []
    unique_repo._items = []
    
    return selections_count, unique_requests_count


async def cleanup_neo4j() -> tuple[int, int]:
    """Delete all records from Neo4j."""
    driver = await get_neo4j_driver()
    
    async with driver.session() as session:
        result1 = await session.run("MATCH (s:Selection) DETACH DELETE s RETURN count(s) as deleted")
        record1 = await result1.single()
        selections_deleted = record1["deleted"] if record1 else 0
        
        result2 = await session.run("MATCH (r:UniqueRequest) DETACH DELETE r RETURN count(r) as deleted")
        record2 = await result2.single()
        unique_requests_deleted = record2["deleted"] if record2 else 0
    
    return selections_deleted, unique_requests_deleted


async def cleanup_cassandra() -> tuple[int, int]:
    """Delete all records from Cassandra."""
    session, executor = get_cassandra_session()
    
    def delete_all():
        # Count before deletion
        count1 = len(list(session.execute("SELECT id FROM selections")))
        count2 = len(list(session.execute("SELECT prompt_normalized FROM unique_requests")))
        
        # Delete all
        session.execute("TRUNCATE selections")
        session.execute("TRUNCATE unique_requests")
        
        return count1, count2
    
    loop = asyncio.get_event_loop()
    selections_count, unique_requests_count = await loop.run_in_executor(executor, delete_all)
    
    return selections_count, unique_requests_count


async def cleanup_all_backends() -> dict:
    """Cleanup all databases."""
    results = {}
    
    backends = [
        ("inmemory", cleanup_inmemory),
        ("mongodb", cleanup_mongodb),
        ("postgres", cleanup_postgres),
        ("neo4j", cleanup_neo4j),
        ("cassandra", cleanup_cassandra),
    ]
    
    for backend_name, cleanup_func in backends:
        try:
            print(f"\n{'='*60}")
            print(f"Cleaning {backend_name} backend...")
            print('='*60)
            
            selections_deleted, unique_requests_deleted = await cleanup_func()
            total = selections_deleted + unique_requests_deleted
            
            results[backend_name] = {
                "success": True,
                "selections_deleted": selections_deleted,
                "unique_requests_deleted": unique_requests_deleted,
                "total": total
            }
            
            print(f"[OK] {backend_name}: Deleted {total} records "
                  f"({selections_deleted} selections, {unique_requests_deleted} unique_requests)")
            
        except Exception as e:
            results[backend_name] = {
                "success": False,
                "error": str(e)
            }
            print(f"[SKIP] {backend_name}: Skipped - {e}")
    
    return results


def get_algorithm_type_from_prompt(prompt: str) -> str:
    """Determine algorithm type from prompt."""
    recs = build_recommendations(prompt)
    if not recs:
        return "Classification"
    
    from backend.services import get_algorithm_type_from_algorithm
    top_algorithm = recs[0].algorithm
    return get_algorithm_type_from_algorithm(top_algorithm)


async def seed_mongodb(prompts: list[str]) -> int:
    """Seed MongoDB with prompts."""
    db = get_db()
    repo = MongoSelectionRepository(db)
    unique_repo = MongoUniqueRequestRepository(db)
    
    count = 0
    for prompt in prompts:
        recs = build_recommendations(prompt)
        if recs:
            algorithm = recs[0].algorithm
            await repo.add_selection(algorithm, prompt)
            algorithm_type = get_algorithm_type_from_prompt(prompt)
            await unique_repo.add_unique_request(prompt, algorithm_type)
            count += 1
    
    return count


async def seed_postgres(prompts: list[str]) -> int:
    """Seed PostgreSQL with prompts."""
    pool = await get_postgres_pool()
    repo = PostgresSelectionRepository(pool)
    unique_repo = PostgresUniqueRequestRepository(pool)
    
    count = 0
    for prompt in prompts:
        recs = build_recommendations(prompt)
        if recs:
            algorithm = recs[0].algorithm
            await repo.add_selection(algorithm, prompt)
            algorithm_type = get_algorithm_type_from_prompt(prompt)
            await unique_repo.add_unique_request(prompt, algorithm_type)
            count += 1
    
    return count


async def seed_inmemory(prompts: list[str]) -> int:
    """Seed in-memory repositories with prompts."""
    repo = InMemorySelectionRepository.get_instance()
    unique_repo = InMemoryUniqueRequestRepository.get_instance()
    
    count = 0
    for prompt in prompts:
        recs = build_recommendations(prompt)
        if recs:
            algorithm = recs[0].algorithm
            await repo.add_selection(algorithm, prompt)
            algorithm_type = get_algorithm_type_from_prompt(prompt)
            await unique_repo.add_unique_request(prompt, algorithm_type)
            count += 1
    
    return count


async def seed_neo4j(prompts: list[str]) -> int:
    """Seed Neo4j with prompts."""
    driver = await get_neo4j_driver()
    repo = Neo4jSelectionRepository(driver)
    unique_repo = Neo4jUniqueRequestRepository(driver)
    
    count = 0
    for prompt in prompts:
        recs = build_recommendations(prompt)
        if recs:
            algorithm = recs[0].algorithm
            await repo.add_selection(algorithm, prompt)
            algorithm_type = get_algorithm_type_from_prompt(prompt)
            await unique_repo.add_unique_request(prompt, algorithm_type)
            count += 1
    
    return count


async def seed_cassandra(prompts: list[str]) -> int:
    """Seed Cassandra with prompts."""
    session, executor = get_cassandra_session()
    repo = CassandraSelectionRepository(session, executor)
    unique_repo = CassandraUniqueRequestRepository(session, executor)
    
    count = 0
    for prompt in prompts:
        recs = build_recommendations(prompt)
        if recs:
            algorithm = recs[0].algorithm
            await repo.add_selection(algorithm, prompt)
            algorithm_type = get_algorithm_type_from_prompt(prompt)
            await unique_repo.add_unique_request(prompt, algorithm_type)
            count += 1
    
    return count


async def seed_all_backends(prompts: list[str]) -> dict:
    """Seed all databases with prompts."""
    results = {}
    
    backends = [
        ("inmemory", seed_inmemory),
        ("mongodb", seed_mongodb),
        ("postgres", seed_postgres),
        ("neo4j", seed_neo4j),
        ("cassandra", seed_cassandra),
    ]
    
    for backend_name, seed_func in backends:
        try:
            print(f"\n{'='*60}")
            print(f"Seeding {backend_name} backend...")
            print('='*60)
            
            count = await seed_func(prompts)
            
            results[backend_name] = {
                "success": True,
                "count": count
            }
            
            print(f"[OK] {backend_name}: Seeded {count} prompts")
            
        except Exception as e:
            results[backend_name] = {
                "success": False,
                "error": str(e)
            }
            print(f"[ERROR] {backend_name}: Failed - {e}")
    
    return results


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Cleanup and reload prompts in all databases"
    )
    parser.add_argument(
        "--prompts-file",
        type=str,
        default="prompts.txt",
        help="Path to prompts file (default: prompts.txt)"
    )
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Skip cleanup step (only reload)"
    )
    parser.add_argument(
        "--skip-reload",
        action="store_true",
        help="Skip reload step (only cleanup)"
    )
    
    args = parser.parse_args()
    
    prompts_file = Path(args.prompts_file)
    if not prompts_file.exists():
        print(f"[ERROR] Prompts file not found: {prompts_file}", file=sys.stderr)
        sys.exit(1)
    
    # Read prompts
    print("=" * 60)
    print("Reading prompts from file...")
    print("=" * 60)
    
    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = [line.strip() for line in f if line.strip()]
    
    print(f"Read {len(prompts)} prompts from {prompts_file}")
    
    # Cleanup
    if not args.skip_cleanup:
        print("\n" + "=" * 60)
        print("STEP 1: Cleaning all databases...")
        print("=" * 60)
        
        cleanup_results = await cleanup_all_backends()
        
        print("\n" + "=" * 60)
        print("CLEANUP SUMMARY")
        print("=" * 60)
        
        total_deleted = 0
        successful = 0
        
        for backend_name, result in cleanup_results.items():
            if result["success"]:
                total_deleted += result["total"]
                successful += 1
                print(f"{backend_name:15} [OK] {result['total']:6} records deleted")
            else:
                print(f"{backend_name:15} [ERROR] {result['error']}")
        
        print("=" * 60)
        print(f"Total deleted: {total_deleted} records")
        print(f"Successfully cleaned {successful}/{len(cleanup_results)} backends")
    else:
        print("\n[SKIP] Skipping cleanup step...")
    
    # Reload
    if not args.skip_reload:
        print("\n" + "=" * 60)
        print("STEP 2: Reloading prompts into all databases...")
        print("=" * 60)
        
        seed_results = await seed_all_backends(prompts)
        
        print("\n" + "=" * 60)
        print("RELOAD SUMMARY")
        print("=" * 60)
        
        total_seeded = 0
        successful = 0
        
        for backend_name, result in seed_results.items():
            if result["success"]:
                total_seeded += result["count"]
                successful += 1
                print(f"{backend_name:15} [OK] {result['count']:6} prompts seeded")
            else:
                print(f"{backend_name:15} [ERROR] {result['error']}")
        
        print("=" * 60)
        print(f"Total seeded: {total_seeded} prompts")
        print(f"Successfully seeded {successful}/{len(seed_results)} backends")
    else:
        print("\n[SKIP] Skipping reload step...")
    
    print("\n[OK] Process completed!")


if __name__ == "__main__":
    asyncio.run(main())

