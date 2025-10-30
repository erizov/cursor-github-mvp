import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


_client: Optional[AsyncIOMotorClient] = None


def get_mongo_uri() -> str:
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017")


def get_db_name() -> str:
    return os.getenv("MONGODB_DB", "ai_algo_teacher")


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(get_mongo_uri())
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[get_db_name()]


