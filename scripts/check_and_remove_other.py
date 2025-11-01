#!/usr/bin/env python3
"""Quick script to check and remove 'Other' records from MongoDB."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.db import get_db


async def main():
    db = get_db()
    selections_col = db["selections"]
    
    # Check what algorithms exist
    print("Checking algorithm names in database...")
    pipeline = [
        {"$group": {"_id": "$algorithm", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    docs = await selections_col.aggregate(pipeline).to_list(10)
    
    print("\nTop 10 algorithm names:")
    for doc in docs:
        print(f"  {doc['_id']}: {doc['count']}")
    
    # Check for "Other" specifically
    other_count = await selections_col.count_documents({
        "algorithm": {"$regex": "^Other$", "$options": "i"}
    })
    print(f"\nRecords with algorithm='Other': {other_count}")
    
    # Also check case variations
    import re
    all_docs = await selections_col.find({}, {"algorithm": 1}).to_list(1000)
    other_variants = set()
    for doc in all_docs:
        alg = str(doc.get("algorithm", "")).strip().lower()
        if "other" in alg:
            other_variants.add(doc.get("algorithm"))
    
    print(f"Algorithm names containing 'other': {list(other_variants)}")
    
    # Delete all "Other" variants
    if other_variants:
        result = await selections_col.delete_many({
            "algorithm": {"$in": list(other_variants)}
        })
        print(f"\n✅ Deleted {result.deleted_count} records with 'Other' algorithm names")
    else:
        print("\n✅ No records with 'Other' algorithm names found")


if __name__ == "__main__":
    asyncio.run(main())

