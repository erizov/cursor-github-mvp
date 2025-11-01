import os
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import asyncpg
from aiomcache import Client as MemcacheClient
from neo4j import AsyncGraphDatabase
# Lazy import for Cassandra
try:
    from cassandra.cluster import Cluster
    CASSANDRA_AVAILABLE = True
except Exception:
    CASSANDRA_AVAILABLE = False
    Cluster = None  # type: ignore

from concurrent.futures import ThreadPoolExecutor
import asyncio


# MongoDB connections
_mongo_client: Optional[AsyncIOMotorClient] = None


def get_mongo_uri() -> str:
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017")


def get_db_name() -> str:
    return os.getenv("MONGODB_DB", "ai_algo_teacher")


def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(
            get_mongo_uri(),
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=5000,
        )
    return _mongo_client


def get_db() -> AsyncIOMotorDatabase:
    return get_mongo_client()[get_db_name()]


# PostgreSQL connections
_postgres_pool: Optional[asyncpg.Pool] = None


def get_postgres_uri() -> str:
    return os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/ai_algo_teacher")


async def get_postgres_pool() -> asyncpg.Pool:
    global _postgres_pool
    if _postgres_pool is None:
        uri = get_postgres_uri()
        # Parse URI and create pool
        if uri.startswith("postgresql://"):
            uri = uri.replace("postgresql://", "postgres://", 1)
        _postgres_pool = await asyncpg.create_pool(
            uri,
            min_size=2,
            max_size=10,
        )
    return _postgres_pool


# Memcached connections
_memcached_client: Optional[MemcacheClient] = None


def get_memcached_host() -> str:
    return os.getenv("MEMCACHED_HOST", "localhost")


def get_memcached_port() -> int:
    return int(os.getenv("MEMCACHED_PORT", "11211"))


async def get_memcached_client() -> MemcacheClient:
    global _memcached_client
    if _memcached_client is None:
        host = get_memcached_host()
        port = get_memcached_port()
        _memcached_client = MemcacheClient(host, port)
    return _memcached_client


# Neo4j connections
_neo4j_driver: Optional[Any] = None


def get_neo4j_uri() -> str:
    return os.getenv("NEO4J_URI", "bolt://localhost:7688")  # Updated for docker-compose port mapping


def get_neo4j_user() -> str:
    return os.getenv("NEO4J_USER", "neo4j")


def get_neo4j_password() -> str:
    return os.getenv("NEO4J_PASSWORD", "password")


async def get_neo4j_driver() -> Any:
    global _neo4j_driver
    if _neo4j_driver is None:
        uri = get_neo4j_uri()
        user = get_neo4j_user()
        password = get_neo4j_password()
        _neo4j_driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    return _neo4j_driver


# Cassandra connections
_cassandra_session: Optional[Any] = None
_cassandra_executor: Optional[ThreadPoolExecutor] = None


def get_cassandra_hosts() -> list[str]:
    hosts_str = os.getenv("CASSANDRA_HOSTS", "localhost")
    return [h.strip() for h in hosts_str.split(",")]


def get_cassandra_keyspace() -> str:
    return os.getenv("CASSANDRA_KEYSPACE", "ai_algo_teacher")


def get_cassandra_session() -> tuple[Any, ThreadPoolExecutor]:
    global _cassandra_session, _cassandra_executor
    if not CASSANDRA_AVAILABLE or Cluster is None:
        raise ImportError("Cassandra driver not available. Install build dependencies or use a different backend.")
    if _cassandra_session is None:
        try:
            from cassandra.exceptions import InvalidRequest
            hosts = get_cassandra_hosts()
            keyspace = get_cassandra_keyspace()
            # For Python 3.12+, use eventlet or gevent event loop (avoid asyncore)
            # This works even without C extensions
            import sys
            if sys.version_info >= (3, 12):
                # Use eventlet event loop for Python 3.12+
                try:
                    cluster = Cluster(hosts, protocol_version=4)
                except Exception:
                    # Fallback: try with default settings
                    cluster = Cluster(hosts)
            else:
                cluster = Cluster(hosts)
            session = cluster.connect()
            # Create keyspace if not exists
            try:
                session.execute(f"""
                    CREATE KEYSPACE IF NOT EXISTS {keyspace}
                    WITH REPLICATION = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
                """)
            except InvalidRequest as e:
                # Keyspace might already exist
                if "already exists" not in str(e).lower():
                    raise  # Re-raise if it's a different error
            except Exception:
                # If keyspace creation fails, still try to use it (might already exist)
                pass
            session.set_keyspace(keyspace)
            _cassandra_session = session
            _cassandra_executor = ThreadPoolExecutor(max_workers=4)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Cassandra: {e}")
    return _cassandra_session, _cassandra_executor
