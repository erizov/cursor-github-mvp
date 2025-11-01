#!/usr/bin/env python3
"""
Remove all database records where algorithm is "Other" or algorithm_type is "Other".

This script deletes records from:
- selections table/collection: where algorithm == "Other" (case-insensitive)
- unique_requests table/collection: where algorithm_type == "Other" (case-insensitive)

Supported backends: MongoDB, PostgreSQL, in-memory, Neo4j, Cassandra, Memcached, Redis
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


async def remove_other_from_mongodb() -> tuple[int, int]:
    """Remove 'Other' records from MongoDB."""
    from backend.services import get_algorithm_type_from_algorithm
    
    db = get_db()
    selections_col = db["selections"]
    unique_requests_col = db["unique_requests"]
    
    # Get all unique algorithm names and check which ones classify as "Other"
    pipeline = [{"$group": {"_id": "$algorithm"}}]
    unique_algorithms = await selections_col.aggregate(pipeline).to_list(None)
    
    # Find algorithms that classify as "Other" or are literally "Other"
    algorithms_to_delete = []
    for doc in unique_algorithms:
        alg_name = doc["_id"]
        if alg_name and isinstance(alg_name, str):
            alg_name_clean = alg_name.strip()
            # Check if literally "Other" or if classification would be "Other"
            # Note: get_algorithm_type_from_algorithm now returns "Classification" instead of "Other"
            # So we only delete if the name is literally "Other"
            if alg_name_clean.lower() == "other":
                algorithms_to_delete.append(alg_name)
    
    # Delete records with those algorithm names
    if algorithms_to_delete:
        result1 = await selections_col.delete_many({
            "algorithm": {"$in": algorithms_to_delete}
        })
        selections_deleted = result1.deleted_count
    else:
        selections_deleted = 0
    
    # Remove from unique_requests where algorithm_type is "Other" (case-insensitive)
    result2 = await unique_requests_col.delete_many({
        "algorithm_type": {"$regex": "^Other$", "$options": "i"}
    })
    unique_requests_deleted = result2.deleted_count
    
    return selections_deleted, unique_requests_deleted


async def remove_other_from_postgres() -> tuple[int, int]:
    """Remove 'Other' records from PostgreSQL."""
    pool = await get_postgres_pool()
    
    async with pool.acquire() as conn:
        # Remove from selections
        selections_deleted = await conn.execute("""
            DELETE FROM selections
            WHERE LOWER(TRIM(algorithm)) = 'other'
        """)
        selections_count = int(selections_deleted.split()[-1])
        
        # Remove from unique_requests
        unique_requests_deleted = await conn.execute("""
            DELETE FROM unique_requests
            WHERE LOWER(TRIM(algorithm_type)) = 'other'
        """)
        unique_requests_count = int(unique_requests_deleted.split()[-1])
    
    return selections_count, unique_requests_count


async def remove_other_from_inmemory() -> tuple[int, int]:
    """Remove 'Other' records from in-memory repositories."""
    selection_repo = InMemorySelectionRepository.get_instance()
    unique_repo = InMemoryUniqueRequestRepository.get_instance()
    
    # Remove from selections
    original_count = len(selection_repo._items)
    selection_repo._items = [
        item for item in selection_repo._items
        if item["algorithm"].strip().lower() != "other"
    ]
    selections_deleted = original_count - len(selection_repo._items)
    
    # Remove from unique_requests
    original_unique_count = len(unique_repo._items)
    unique_repo._items = [
        item for item in unique_repo._items
        if item["algorithm_type"].strip().lower() != "other"
    ]
    unique_requests_deleted = original_unique_count - len(unique_repo._items)
    
    return selections_deleted, unique_requests_deleted


async def remove_other_from_neo4j() -> tuple[int, int]:
    """Remove 'Other' records from Neo4j."""
    driver = await get_neo4j_driver()
    
    async with driver.session() as session:
        # Remove Selection nodes where algorithm is "Other" (case-insensitive)
        result1 = await session.run("""
            MATCH (s:Selection)
            WHERE toLower(trim(s.algorithm)) = 'other'
            DETACH DELETE s
            RETURN count(s) as deleted
        """)
        record1 = await result1.single()
        selections_deleted = record1["deleted"] if record1 else 0
        
        # Remove UniqueRequest nodes where algorithm_type is "Other" (case-insensitive)
        result2 = await session.run("""
            MATCH (r:UniqueRequest)
            WHERE toLower(trim(r.algorithm_type)) = 'other'
            DETACH DELETE r
            RETURN count(r) as deleted
        """)
        record2 = await result2.single()
        unique_requests_deleted = record2["deleted"] if record2 else 0
    
    return selections_deleted, unique_requests_deleted


async def remove_other_from_cassandra() -> tuple[int, int]:
    """Remove 'Other' records from Cassandra."""
    session, executor = get_cassandra_session()
    
    def delete_selections():
        result = session.execute("""
            SELECT id FROM selections
            WHERE algorithm = 'Other' ALLOW FILTERING
        """)
        ids = [row.id for row in result]
        if ids:
            for id_val in ids:
                session.execute(
                    "DELETE FROM selections WHERE id = ?",
                    [id_val]
                )
        return len(ids)
    
    def delete_unique_requests():
        result = session.execute("""
            SELECT prompt_normalized FROM unique_requests
            WHERE algorithm_type = 'Other' ALLOW FILTERING
        """)
        keys = [row.prompt_normalized for row in result]
        if keys:
            for key in keys:
                session.execute(
                    "DELETE FROM unique_requests WHERE prompt_normalized = ?",
                    [key]
                )
        return len(keys)
    
    loop = asyncio.get_event_loop()
    selections_deleted = await loop.run_in_executor(executor, delete_selections)
    unique_requests_deleted = await loop.run_in_executor(executor, delete_unique_requests)
    
    return selections_deleted, unique_requests_deleted


async def remove_other_from_all_backends() -> dict:
    """Remove 'Other' records from all available backends."""
    results = {}
    
    # List of backends to try
    backends = [
        ("inmemory", remove_other_from_inmemory),
        ("mongodb", remove_other_from_mongodb),
        ("postgres", remove_other_from_postgres),
        ("neo4j", remove_other_from_neo4j),
        ("cassandra", remove_other_from_cassandra),
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
            
            print(f"✅ {backend_name}: Removed {total} records "
                  f"({selections_deleted} selections, {unique_requests_deleted} unique_requests)")
            
        except Exception as e:
            results[backend_name] = {
                "success": False,
                "error": str(e)
            }
            print(f"⚠️  {backend_name}: Skipped - {e}")
    
    return results


async def main():
    """Main function to remove 'Other' records from all backends."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Remove records with algorithm_type='other' from databases"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean all backends (default: clean only current BACKEND_TYPE)"
    )
    parser.add_argument(
        "--backend",
        type=str,
        help="Clean specific backend (inmemory, mongodb, postgres, neo4j, cassandra)"
    )
    
    args = parser.parse_args()
    
    if args.all:
        # Clean all backends
        print("=" * 60)
        print("Removing 'Other' records from ALL backends")
        print("=" * 60)
        
        results = await remove_other_from_all_backends()
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        total_selections = 0
        total_unique_requests = 0
        successful = 0
        
        for backend_name, result in results.items():
            if result["success"]:
                total_selections += result["selections_deleted"]
                total_unique_requests += result["unique_requests_deleted"]
                successful += 1
                print(f"{backend_name:15} ✅ {result['total']:6} records removed")
            else:
                print(f"{backend_name:15} ❌ Error: {result['error']}")
        
        print("=" * 60)
        print(f"Total: {total_selections + total_unique_requests} records removed "
              f"({total_selections} selections, {total_unique_requests} unique_requests)")
        print(f"Successfully cleaned {successful}/{len(results)} backends")
        
    elif args.backend:
        # Clean specific backend
        backend_type = args.backend.lower()
        
        print("=" * 60)
        print(f"Removing 'Other' records from {backend_type} backend")
        print("=" * 60)
        
        try:
            if backend_type == "mongodb":
                selections_deleted, unique_requests_deleted = await remove_other_from_mongodb()
            elif backend_type in ["postgres", "postgresql"]:
                selections_deleted, unique_requests_deleted = await remove_other_from_postgres()
            elif backend_type == "inmemory":
                selections_deleted, unique_requests_deleted = await remove_other_from_inmemory()
            elif backend_type == "neo4j":
                selections_deleted, unique_requests_deleted = await remove_other_from_neo4j()
            elif backend_type == "cassandra":
                selections_deleted, unique_requests_deleted = await remove_other_from_cassandra()
            else:
                print(f"Error: Backend type '{backend_type}' is not supported.")
                print("Supported backends: mongodb, postgres, inmemory, neo4j, cassandra")
                sys.exit(1)
            
            print(f"\n✅ Cleanup completed:")
            print(f"  - Removed {selections_deleted} records from selections")
            print(f"  - Removed {unique_requests_deleted} records from unique_requests")
            print(f"  - Total removed: {selections_deleted + unique_requests_deleted} records")
            
        except Exception as e:
            print(f"\n❌ Error during cleanup: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Clean current backend (from BACKEND_TYPE env var)
        backend_type = os.getenv("BACKEND_TYPE", "inmemory").lower()
        
        print("=" * 60)
        print(f"Removing 'Other' records from {backend_type} backend")
        print("=" * 60)
        print("(Use --all to clean all backends, or --backend <name> for specific backend)")
        print("=" * 60)
        
        try:
            if backend_type == "mongodb":
                selections_deleted, unique_requests_deleted = await remove_other_from_mongodb()
            elif backend_type in ["postgres", "postgresql"]:
                selections_deleted, unique_requests_deleted = await remove_other_from_postgres()
            elif backend_type == "inmemory":
                selections_deleted, unique_requests_deleted = await remove_other_from_inmemory()
            elif backend_type == "neo4j":
                selections_deleted, unique_requests_deleted = await remove_other_from_neo4j()
            elif backend_type == "cassandra":
                selections_deleted, unique_requests_deleted = await remove_other_from_cassandra()
            else:
                print(f"Error: Backend type '{backend_type}' is not supported.")
                print("Supported backends: mongodb, postgres, inmemory, neo4j, cassandra")
                sys.exit(1)
            
            print(f"\n✅ Cleanup completed:")
            print(f"  - Removed {selections_deleted} records from selections")
            print(f"  - Removed {unique_requests_deleted} records from unique_requests")
            print(f"  - Total removed: {selections_deleted + unique_requests_deleted} records")
            
        except Exception as e:
            print(f"\n❌ Error during cleanup: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

