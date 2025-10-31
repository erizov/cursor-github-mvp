#!/usr/bin/env python3
"""
Seed prompts into MongoDB collection `prompts` from prompts.txt.

Env:
  MONGODB_URI (default: mongodb://localhost:27017)
  MONGODB_DB  (default: ai_algo_teacher)
"""

import os
from pathlib import Path
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_FILE = ROOT / "prompts.txt"


def main() -> None:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    dbname = os.getenv("MONGODB_DB", "ai_algo_teacher")
    client = MongoClient(uri, serverSelectionTimeoutMS=2000)
    db = client[dbname]
    col = db["prompts"]
    col.drop()
    batch = []
    with PROMPTS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            prompt, algo = line.split("|", 1)
            batch.append({"prompt": prompt, "algorithm_type": algo})
    if batch:
        col.insert_many(batch)
    print(f"Seeded {len(batch)} prompts into MongoDB {dbname}.prompts")


if __name__ == "__main__":
    main()


