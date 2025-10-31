#!/usr/bin/env python3
"""
Seed prompts into a local SQLite database at storage/prompts.db
with table prompts(id INTEGER PRIMARY KEY, prompt TEXT, algorithm_type TEXT).
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = ROOT / "storage"
DB_PATH = STORAGE_DIR / "prompts.db"
PROMPTS_FILE = ROOT / "prompts.txt"


def main() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                algorithm_type TEXT NOT NULL
            )
            """
        )
        cur.execute("DELETE FROM prompts")
        batch = []
        with PROMPTS_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if "|" not in line:
                    continue
                prompt, algo = line.split("|", 1)
                batch.append((prompt, algo))
        cur.executemany("INSERT INTO prompts(prompt, algorithm_type) VALUES(?, ?)", batch)
        conn.commit()
        print(f"Seeded {len(batch)} prompts into {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


