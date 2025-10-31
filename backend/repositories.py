from __future__ import annotations

from typing import List, Protocol, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase


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


class InMemorySelectionRepository:
    def __init__(self) -> None:
        self._items: List[dict] = []

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


class InMemoryUniqueRequestRepository:
    def __init__(self) -> None:
        self._items: List[dict] = []

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


