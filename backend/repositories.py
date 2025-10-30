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


