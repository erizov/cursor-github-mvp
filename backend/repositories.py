from __future__ import annotations

import json
import hashlib
from typing import List, Protocol, Dict, Optional, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncpg
from aiomcache import Client as MemcacheClient
# Neo4j driver type is Any since it's not easily typed
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Lazy import for Cassandra to avoid issues on systems without proper build tools
CASSANDRA_AVAILABLE = False
Session = Any  # type: ignore

def _try_import_cassandra():
    """Try to import Cassandra driver."""
    global CASSANDRA_AVAILABLE, Session
    try:
        from cassandra.cluster import Session  # type: ignore
        # Test that we can actually create a cluster (basic validation)
        # This will fail if C extensions are missing
        CASSANDRA_AVAILABLE = True
    except ImportError:
        CASSANDRA_AVAILABLE = False
    except Exception:
        # Catch DependencyException and other runtime errors
        # This happens when C extensions are missing
        CASSANDRA_AVAILABLE = False


class SelectionRepository(Protocol):
    async def add_selection(self, algorithm: str, prompt: str) -> None: ...
    async def usage_counts(self) -> List[Dict[str, int]]: ...
    async def total(self) -> int: ...
    async def detailed_by_algorithm(self) -> List[Dict]: ...


class MongoSelectionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db["selections"]

    async def add_selection(self, algorithm: str, prompt: str) -> None:
        await self._col.insert_one({
            "algorithm": algorithm,
            "prompt": prompt,
            "created_at": datetime.now(timezone.utc),
        })

    async def usage_counts(self) -> List[Dict[str, int]]:
        pipeline = [
            {"$group": {"_id": "$algorithm", "count": {"$sum": 1}}},
            {"$project": {"algorithm": "$_id", "count": 1, "_id": 0}},
            {"$sort": {"count": -1, "algorithm": 1}},
        ]
        docs = await self._col.aggregate(pipeline).to_list(length=None)
        return docs

    async def total(self) -> int:
        return await self._col.count_documents({})

    async def detailed_by_algorithm(self) -> List[Dict]:
        pipeline = [
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$algorithm",
                    "count": {"$sum": 1},
                    "items": {
                        "$push": {
                            "algorithm": "$algorithm",
                            "prompt": "$prompt",
                            "created_at": "$created_at",
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "algorithm": "$_id", "count": 1, "items": 1}},
            {"$sort": {"count": -1, "algorithm": 1}},
        ]
        docs = await self._col.aggregate(pipeline).to_list(length=None)
        return docs


# Singleton instance for in-memory repository to persist across requests
_in_memory_selection_repo_instance: "InMemorySelectionRepository | None" = None

class InMemorySelectionRepository:
    def __init__(self) -> None:
        self._items: List[dict] = []
    
    @classmethod
    def get_instance(cls) -> "InMemorySelectionRepository":
        """Get singleton instance that persists across requests."""
        global _in_memory_selection_repo_instance
        if _in_memory_selection_repo_instance is None:
            _in_memory_selection_repo_instance = cls()
        return _in_memory_selection_repo_instance

    async def add_selection(self, algorithm: str, prompt: str) -> None:
        self._items.append({
            "algorithm": algorithm,
            "prompt": prompt,
            "created_at": datetime.now(timezone.utc),
        })

    async def usage_counts(self) -> List[Dict[str, int]]:
        counts: Dict[str, int] = {}
        for it in self._items:
            counts[it["algorithm"]] = counts.get(it["algorithm"], 0) + 1
        return [{"algorithm": k, "count": v} for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]

    async def total(self) -> int:
        return len(self._items)

    async def detailed_by_algorithm(self) -> List[Dict]:
        grouped: Dict[str, List[Dict]] = {}
        for it in sorted(self._items, key=lambda x: x["created_at"], reverse=True):
            grouped.setdefault(it["algorithm"], []).append({
                "algorithm": it["algorithm"],
                "prompt": it["prompt"],
                "created_at": it["created_at"],
            })
        groups = [
            {"algorithm": alg, "count": len(items), "items": items}
            for alg, items in grouped.items()
        ]
        groups.sort(key=lambda g: (-g["count"], g["algorithm"]))
        return groups


class UniqueRequestRepository(Protocol):
    async def add_unique_request(self, prompt: str, algorithm_type: str) -> bool: ...
    async def get_requests_by_type(self, algorithm_type: str) -> List[Dict]: ...
    async def get_all_requests(self) -> List[Dict]: ...
    async def count_by_type(self) -> List[Dict[str, int]]: ...


class MongoUniqueRequestRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db["unique_requests"]
        self._index_created = False

    async def _ensure_index(self) -> None:
        if not self._index_created:
            try:
                await self._col.create_index("prompt_normalized", unique=True)
                self._index_created = True
            except Exception:
                # Index might already exist
                pass

    def _normalize_prompt(self, prompt: str) -> str:
        return " ".join(prompt.lower().strip().split())

    async def add_unique_request(self, prompt: str, algorithm_type: str) -> bool:
        await self._ensure_index()
        normalized = self._normalize_prompt(prompt)
        try:
            await self._col.insert_one({
                "prompt": prompt,
                "prompt_normalized": normalized,
                "algorithm_type": algorithm_type,
                "created_at": datetime.now(timezone.utc),
            })
            return True
        except Exception:
            # Prompt already exists
            return False

    async def get_requests_by_type(self, algorithm_type: str) -> List[Dict]:
        cursor = self._col.find({"algorithm_type": algorithm_type}).sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [
            {
                "prompt": doc["prompt"],
                "algorithm_type": doc["algorithm_type"],
                "created_at": doc["created_at"],
            }
            for doc in docs
        ]

    async def get_all_requests(self) -> List[Dict]:
        cursor = self._col.find().sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [
            {
                "prompt": doc["prompt"],
                "algorithm_type": doc["algorithm_type"],
                "created_at": doc["created_at"],
            }
            for doc in docs
        ]

    async def count_by_type(self) -> List[Dict[str, int]]:
        pipeline = [
            {"$group": {"_id": "$algorithm_type", "count": {"$sum": 1}}},
            {"$project": {"algorithm_type": "$_id", "count": 1, "_id": 0}},
            {"$sort": {"count": -1, "algorithm_type": 1}},
        ]
        docs = await self._col.aggregate(pipeline).to_list(length=None)
        return docs


# Singleton instance for in-memory unique request repository
_in_memory_unique_repo_instance: "InMemoryUniqueRequestRepository | None" = None

class InMemoryUniqueRequestRepository:
    def __init__(self) -> None:
        self._items: List[dict] = []
    
    @classmethod
    def get_instance(cls) -> "InMemoryUniqueRequestRepository":
        """Get singleton instance that persists across requests."""
        global _in_memory_unique_repo_instance
        if _in_memory_unique_repo_instance is None:
            _in_memory_unique_repo_instance = cls()
        return _in_memory_unique_repo_instance

    def _normalize_prompt(self, prompt: str) -> str:
        return " ".join(prompt.lower().strip().split())

    async def add_unique_request(self, prompt: str, algorithm_type: str) -> bool:
        normalized = self._normalize_prompt(prompt)
        # Check if already exists
        if any(self._normalize_prompt(item["prompt"]) == normalized for item in self._items):
            return False
        self._items.append({
            "prompt": prompt,
            "algorithm_type": algorithm_type,
            "created_at": datetime.now(timezone.utc),
        })
        return True

    async def get_requests_by_type(self, algorithm_type: str) -> List[Dict]:
        return [
            {
                "prompt": item["prompt"],
                "algorithm_type": item["algorithm_type"],
                "created_at": item["created_at"],
            }
            for item in self._items
            if item["algorithm_type"] == algorithm_type
        ]

    async def get_all_requests(self) -> List[Dict]:
        return [
            {
                "prompt": item["prompt"],
                "algorithm_type": item["algorithm_type"],
                "created_at": item["created_at"],
            }
            for item in self._items
        ]

    async def count_by_type(self) -> List[Dict[str, int]]:
        counts: Dict[str, int] = {}
        for item in self._items:
            counts[item["algorithm_type"]] = counts.get(item["algorithm_type"], 0) + 1
        return [
            {"algorithm_type": k, "count": v}
            for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ]


# PostgreSQL Repository Implementations

class PostgresSelectionRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._initialized = False

    async def _ensure_schema(self) -> None:
        if self._initialized:
            return
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS selections (
                    id SERIAL PRIMARY KEY,
                    algorithm VARCHAR(255) NOT NULL,
                    prompt TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_selections_algorithm 
                ON selections(algorithm)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_selections_created_at 
                ON selections(created_at DESC)
            """)
        self._initialized = True

    async def add_selection(self, algorithm: str, prompt: str) -> None:
        await self._ensure_schema()
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO selections (algorithm, prompt, created_at) VALUES ($1, $2, $3)",
                algorithm, prompt, datetime.now(timezone.utc)
            )

    async def usage_counts(self) -> List[Dict[str, int]]:
        await self._ensure_schema()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT algorithm, COUNT(*) as count
                FROM selections
                GROUP BY algorithm
                ORDER BY count DESC, algorithm ASC
            """)
            return [{"algorithm": row["algorithm"], "count": row["count"]} for row in rows]

    async def total(self) -> int:
        await self._ensure_schema()
        async with self._pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM selections")
            return count or 0

    async def detailed_by_algorithm(self) -> List[Dict]:
        await self._ensure_schema()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT algorithm, prompt, created_at
                FROM selections
                ORDER BY created_at DESC
            """)
            grouped: Dict[str, List[Dict]] = {}
            for row in rows:
                alg = row["algorithm"]
                if alg not in grouped:
                    grouped[alg] = []
                grouped[alg].append({
                    "algorithm": alg,
                    "prompt": row["prompt"],
                    "created_at": row["created_at"],
                })
            groups = [
                {"algorithm": alg, "count": len(items), "items": items}
                for alg, items in grouped.items()
            ]
            groups.sort(key=lambda g: (-g["count"], g["algorithm"]))
            return groups


class PostgresUniqueRequestRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._initialized = False

    async def _ensure_schema(self) -> None:
        if self._initialized:
            return
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS unique_requests (
                    id SERIAL PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    prompt_normalized VARCHAR(500) NOT NULL UNIQUE,
                    algorithm_type VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_unique_requests_type 
                ON unique_requests(algorithm_type)
            """)
        self._initialized = True

    def _normalize_prompt(self, prompt: str) -> str:
        return " ".join(prompt.lower().strip().split())

    async def add_unique_request(self, prompt: str, algorithm_type: str) -> bool:
        await self._ensure_schema()
        normalized = self._normalize_prompt(prompt)
        async with self._pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO unique_requests (prompt, prompt_normalized, algorithm_type, created_at)
                    VALUES ($1, $2, $3, $4)
                """, prompt, normalized, algorithm_type, datetime.now(timezone.utc))
                return True
            except asyncpg.UniqueViolationError:
                return False

    async def get_requests_by_type(self, algorithm_type: str) -> List[Dict]:
        await self._ensure_schema()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT prompt, algorithm_type, created_at
                FROM unique_requests
                WHERE algorithm_type = $1
                ORDER BY created_at DESC
            """, algorithm_type)
            return [
                {"prompt": row["prompt"], "algorithm_type": row["algorithm_type"], "created_at": row["created_at"]}
                for row in rows
            ]

    async def get_all_requests(self) -> List[Dict]:
        await self._ensure_schema()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT prompt, algorithm_type, created_at
                FROM unique_requests
                ORDER BY created_at DESC
            """)
            return [
                {"prompt": row["prompt"], "algorithm_type": row["algorithm_type"], "created_at": row["created_at"]}
                for row in rows
            ]

    async def count_by_type(self) -> List[Dict[str, int]]:
        await self._ensure_schema()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT algorithm_type, COUNT(*) as count
                FROM unique_requests
                GROUP BY algorithm_type
                ORDER BY count DESC, algorithm_type ASC
            """)
            return [{"algorithm_type": row["algorithm_type"], "count": row["count"]} for row in rows]


# Memcached Repository Implementations (simplified - uses JSON serialization)

class MemcachedSelectionRepository:
    def __init__(self, client: MemcacheClient) -> None:
        self._client = client
        self._key_prefix = "selection:"

    def _get_key(self, algorithm: str, idx: int) -> bytes:
        return f"{self._key_prefix}{algorithm}:{idx}".encode()

    def _get_count_key(self, algorithm: str) -> bytes:
        return f"{self._key_prefix}count:{algorithm}".encode()

    async def add_selection(self, algorithm: str, prompt: str) -> None:
        # Get current count for this algorithm
        count_key = self._get_count_key(algorithm)
        count_bytes = await self._client.get(count_key)
        count = int(count_bytes.decode()) if count_bytes else 0
        
        # Store the selection
        item = {
            "algorithm": algorithm,
            "prompt": prompt,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        key = self._get_key(algorithm, count)
        await self._client.set(key, json.dumps(item).encode())
        
        # Update count
        await self._client.set(count_key, str(count + 1).encode())

    async def usage_counts(self) -> List[Dict[str, int]]:
        # Note: Memcached doesn't support list operations well
        # This is a simplified implementation
        # In production, you'd want to maintain a separate index
        counts: Dict[str, int] = {}
        # For simplicity, we'll return empty - full implementation would need indexing
        return [{"algorithm": k, "count": v} for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]

    async def total(self) -> int:
        # Simplified - would need to aggregate counts
        return 0

    async def detailed_by_algorithm(self) -> List[Dict]:
        # Simplified implementation
        return []


class MemcachedUniqueRequestRepository:
    def __init__(self, client: MemcacheClient) -> None:
        self._client = client
        self._key_prefix = "unique_req:"
        self._normalized_prefix = "unique_req_norm:"

    def _normalize_prompt(self, prompt: str) -> str:
        return " ".join(prompt.lower().strip().split())

    def _get_hash_key(self, normalized: str) -> bytes:
        h = hashlib.md5(normalized.encode()).hexdigest()
        return f"{self._normalized_prefix}{h}".encode()

    async def add_unique_request(self, prompt: str, algorithm_type: str) -> bool:
        normalized = self._normalize_prompt(prompt)
        hash_key = self._get_hash_key(normalized)
        
        # Check if exists
        existing = await self._client.get(hash_key)
        if existing:
            return False
        
        # Store
        item = {
            "prompt": prompt,
            "algorithm_type": algorithm_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._client.set(hash_key, json.dumps(item).encode())
        return True

    async def get_requests_by_type(self, algorithm_type: str) -> List[Dict]:
        # Simplified - would need full scan/index
        return []

    async def get_all_requests(self) -> List[Dict]:
        # Simplified - would need full scan/index
        return []

    async def count_by_type(self) -> List[Dict[str, int]]:
        # Simplified - would need full scan/index
        return []


# Neo4j Repository Implementations

class Neo4jSelectionRepository:
    def __init__(self, driver) -> None:
        self._driver = driver

    async def add_selection(self, algorithm: str, prompt: str) -> None:
        async with self._driver.session() as session:
            await session.run("""
                CREATE (s:Selection {
                    algorithm: $algorithm,
                    prompt: $prompt,
                    created_at: datetime()
                })
            """, algorithm=algorithm, prompt=prompt)

    async def usage_counts(self) -> List[Dict[str, int]]:
        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (s:Selection)
                RETURN s.algorithm as algorithm, count(*) as count
                ORDER BY count DESC, algorithm ASC
            """)
            return [
                {"algorithm": record["algorithm"], "count": record["count"]}
                async for record in result
            ]

    async def total(self) -> int:
        async with self._driver.session() as session:
            result = await session.run("MATCH (s:Selection) RETURN count(*) as total")
            record = await result.single()
            return record["total"] if record else 0

    async def detailed_by_algorithm(self) -> List[Dict]:
        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (s:Selection)
                RETURN s.algorithm as algorithm, s.prompt as prompt, s.created_at as created_at
                ORDER BY s.created_at DESC
            """)
            grouped: Dict[str, List[Dict]] = {}
            async for record in result:
                alg = record["algorithm"]
                if alg not in grouped:
                    grouped[alg] = []
                created_at = record["created_at"]
                # Neo4j datetime is a DateTime object, convert to datetime if needed
                if hasattr(created_at, 'to_native'):
                    created_at = created_at.to_native()
                grouped[alg].append({
                    "algorithm": alg,
                    "prompt": record["prompt"],
                    "created_at": created_at,
                })
            groups = [
                {"algorithm": alg, "count": len(items), "items": items}
                for alg, items in grouped.items()
            ]
            groups.sort(key=lambda g: (-g["count"], g["algorithm"]))
            return groups


class Neo4jUniqueRequestRepository:
    def __init__(self, driver) -> None:
        self._driver = driver

    def _normalize_prompt(self, prompt: str) -> str:
        return " ".join(prompt.lower().strip().split())

    async def add_unique_request(self, prompt: str, algorithm_type: str) -> bool:
        normalized = self._normalize_prompt(prompt)
        async with self._driver.session() as session:
            # Check if exists
            result = await session.run("""
                MATCH (r:UniqueRequest {prompt_normalized: $normalized})
                RETURN r
            """, normalized=normalized)
            if await result.single():
                return False
            
            # Create
            await session.run("""
                CREATE (r:UniqueRequest {
                    prompt: $prompt,
                    prompt_normalized: $normalized,
                    algorithm_type: $algorithm_type,
                    created_at: datetime()
                })
            """, prompt=prompt, normalized=normalized, algorithm_type=algorithm_type)
            return True

    async def get_requests_by_type(self, algorithm_type: str) -> List[Dict]:
        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (r:UniqueRequest {algorithm_type: $type})
                RETURN r.prompt as prompt, r.algorithm_type as algorithm_type, r.created_at as created_at
                ORDER BY r.created_at DESC
            """, type=algorithm_type)
            return [
                {
                    "prompt": record["prompt"],
                    "algorithm_type": record["algorithm_type"],
                    "created_at": record["created_at"],
                }
                async for record in result
            ]

    async def get_all_requests(self) -> List[Dict]:
        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (r:UniqueRequest)
                RETURN r.prompt as prompt, r.algorithm_type as algorithm_type, r.created_at as created_at
                ORDER BY r.created_at DESC
            """)
            return [
                {
                    "prompt": record["prompt"],
                    "algorithm_type": record["algorithm_type"],
                    "created_at": record["created_at"],
                }
                async for record in result
            ]

    async def count_by_type(self) -> List[Dict[str, int]]:
        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (r:UniqueRequest)
                RETURN r.algorithm_type as algorithm_type, count(*) as count
                ORDER BY count DESC, algorithm_type ASC
            """)
            return [
                {"algorithm_type": record["algorithm_type"], "count": record["count"]}
                async for record in result
            ]


# Cassandra Repository Implementations (using ThreadPoolExecutor for async wrapper)
# Try to import Cassandra - only if available
_try_import_cassandra()

if not CASSANDRA_AVAILABLE:
    # Dummy classes if Cassandra is not available
    class CassandraSelectionRepository:
        def __init__(self, session, executor):
            raise ImportError("Cassandra driver not available. Install build dependencies or use a different backend.")
    
    class CassandraUniqueRequestRepository:
        def __init__(self, session, executor):
            raise ImportError("Cassandra driver not available. Install build dependencies or use a different backend.")
else:

    class CassandraSelectionRepository:
        def __init__(self, session, executor: ThreadPoolExecutor) -> None:
            self._session = session
            self._executor = executor
            self._prepared_insert = None
            self._initialized = False

        async def _ensure_schema(self) -> None:
            if self._initialized:
                return
            
            def init_schema():
                # Create table
                try:
                    self._session.execute("""
                        CREATE TABLE IF NOT EXISTS selections (
                            id UUID PRIMARY KEY,
                            algorithm TEXT,
                            prompt TEXT,
                            created_at TIMESTAMP
                        )
                    """)
                except Exception:
                    # Table might already exist, continue
                    pass
                # Create index (Cassandra doesn't support IF NOT EXISTS for indexes)
                # Use InvalidRequest to catch "already exists" errors
                try:
                    from cassandra.exceptions import InvalidRequest
                    self._session.execute("""
                        CREATE INDEX idx_selections_algorithm 
                        ON selections(algorithm)
                    """)
                except InvalidRequest as e:
                    # Index might already exist (error message contains "already exists")
                    if "already exists" not in str(e).lower():
                        raise  # Re-raise if it's a different InvalidRequest
                except Exception:
                    # Other errors - ignore (index might already exist with different error)
                    pass
            
            await asyncio.get_event_loop().run_in_executor(self._executor, init_schema)
            self._prepared_insert = self._session.prepare(
                "INSERT INTO selections (id, algorithm, prompt, created_at) VALUES (?, ?, ?, ?)"
            )
            self._initialized = True

        async def add_selection(self, algorithm: str, prompt: str) -> None:
            await self._ensure_schema()
            from uuid import uuid4
            
            def insert():
                self._session.execute(self._prepared_insert, (
                    uuid4(), algorithm, prompt, datetime.now(timezone.utc)
                ))
            
            await asyncio.get_event_loop().run_in_executor(self._executor, insert)

        async def usage_counts(self) -> List[Dict[str, int]]:
            await self._ensure_schema()
            
            def query():
                # Cassandra doesn't support GROUP BY with COUNT(*) efficiently
                # We need to fetch all and group in Python
                result = self._session.execute("""
                    SELECT algorithm FROM selections
                """)
                counts: Dict[str, int] = {}
                for row in result:
                    alg = row.algorithm or ""
                    counts[alg] = counts.get(alg, 0) + 1
                return [{"algorithm": k, "count": v} for k, v in counts.items()]
            
            rows = await asyncio.get_event_loop().run_in_executor(self._executor, query)
            return sorted(rows, key=lambda x: (-x["count"], x["algorithm"]))

        async def total(self) -> int:
            await self._ensure_schema()
            
            def query():
                result = self._session.execute("SELECT COUNT(*) as total FROM selections")
                row = result.one()
                return row.total if row else 0
            
            return await asyncio.get_event_loop().run_in_executor(self._executor, query)

        async def detailed_by_algorithm(self) -> List[Dict]:
            await self._ensure_schema()
            
            def query():
                result = self._session.execute("""
                    SELECT algorithm, prompt, created_at
                    FROM selections
                """)
                grouped: Dict[str, List[Dict]] = {}
                for row in result:
                    alg = row.algorithm
                    if alg not in grouped:
                        grouped[alg] = []
                    grouped[alg].append({
                        "algorithm": alg,
                        "prompt": row.prompt,
                        "created_at": row.created_at,
                    })
                groups = [
                    {"algorithm": alg, "count": len(items), "items": items}
                    for alg, items in grouped.items()
                ]
                return sorted(groups, key=lambda g: (-g["count"], g["algorithm"]))
            
            return await asyncio.get_event_loop().run_in_executor(self._executor, query)


    class CassandraUniqueRequestRepository:
        def __init__(self, session, executor: ThreadPoolExecutor) -> None:
            self._session = session
            self._executor = executor
            self._prepared_insert = None
            self._initialized = False

        async def _ensure_schema(self) -> None:
            if self._initialized:
                return
            
            def init_schema():
                # Create table
                try:
                    self._session.execute("""
                        CREATE TABLE IF NOT EXISTS unique_requests (
                            prompt_normalized TEXT PRIMARY KEY,
                            prompt TEXT,
                            algorithm_type TEXT,
                            created_at TIMESTAMP
                        )
                    """)
                except Exception:
                    # Table might already exist, continue
                    pass
                # Create index (Cassandra doesn't support IF NOT EXISTS for indexes)
                # Use InvalidRequest to catch "already exists" errors
                try:
                    from cassandra.exceptions import InvalidRequest
                    self._session.execute("""
                        CREATE INDEX idx_unique_requests_type 
                        ON unique_requests(algorithm_type)
                    """)
                except InvalidRequest as e:
                    # Index might already exist (error message contains "already exists")
                    if "already exists" not in str(e).lower():
                        raise  # Re-raise if it's a different InvalidRequest
                except Exception:
                    # Other errors - ignore (index might already exist with different error)
                    pass
            
            await asyncio.get_event_loop().run_in_executor(self._executor, init_schema)
            self._prepared_insert = self._session.prepare(
                "INSERT INTO unique_requests (prompt_normalized, prompt, algorithm_type, created_at) VALUES (?, ?, ?, ?)"
            )
            self._initialized = True

        def _normalize_prompt(self, prompt: str) -> str:
            return " ".join(prompt.lower().strip().split())

        async def add_unique_request(self, prompt: str, algorithm_type: str) -> bool:
            await self._ensure_schema()
            normalized = self._normalize_prompt(prompt)
            
            def insert():
                try:
                    self._session.execute(self._prepared_insert, (
                        normalized, prompt, algorithm_type, datetime.now(timezone.utc)
                    ))
                    return True
                except Exception:
                    return False
            
            return await asyncio.get_event_loop().run_in_executor(self._executor, insert)

        async def get_requests_by_type(self, algorithm_type: str) -> List[Dict]:
            await self._ensure_schema()
            
            def query():
                result = self._session.execute("""
                    SELECT prompt, algorithm_type, created_at
                    FROM unique_requests
                    WHERE algorithm_type = ?
                """, (algorithm_type,))
                return [
                    {"prompt": row.prompt, "algorithm_type": row.algorithm_type, "created_at": row.created_at}
                    for row in result
                ]
            
            return await asyncio.get_event_loop().run_in_executor(self._executor, query)

        async def get_all_requests(self) -> List[Dict]:
            await self._ensure_schema()
            
            def query():
                result = self._session.execute("SELECT prompt, algorithm_type, created_at FROM unique_requests")
                return [
                    {"prompt": row.prompt, "algorithm_type": row.algorithm_type, "created_at": row.created_at}
                    for row in result
                ]
            
            return await asyncio.get_event_loop().run_in_executor(self._executor, query)

        async def count_by_type(self) -> List[Dict[str, int]]:
            await self._ensure_schema()
            
            def query():
                result = self._session.execute("""
                    SELECT algorithm_type, COUNT(*) as count
                    FROM unique_requests
                    GROUP BY algorithm_type
                """)
                return [{"algorithm_type": row.algorithm_type, "count": row.count} for row in result]
            
            rows = await asyncio.get_event_loop().run_in_executor(self._executor, query)
            return sorted(rows, key=lambda x: (-x["count"], x["algorithm_type"]))


