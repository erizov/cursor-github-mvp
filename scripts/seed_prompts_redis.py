#!/usr/bin/env python3
"""
Seed prompts into Redis under keys:
  - prompts:list (LPUSH) of prompt strings
  - prompts:hash  (HSET) mapping prompt -> algorithm_type

Env:
  REDIS_URL (default: redis://localhost:6379/0)
"""

import os
import sys
from pathlib import Path
import redis
from redis.exceptions import ConnectionError as RedisConnectionError

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_FILE = ROOT / "prompts.txt"


def main() -> None:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = redis.from_url(url)
        # Test connection
        r.ping()
    except RedisConnectionError as e:
        print(
            f"Error: Cannot connect to Redis at {url}\n"
            f"Please ensure Redis is running and accessible.\n"
            f"Details: {e}",
            file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(
            f"Error connecting to Redis: {e}",
            file=sys.stderr
        )
        sys.exit(1)
    
    # Clear existing
    r.delete("prompts:list")
    r.delete("prompts:hash")
    count = 0
    pipe = r.pipeline()
    with PROMPTS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            prompt, algo = line.split("|", 1)
            pipe.lpush("prompts:list", prompt)
            pipe.hset("prompts:hash", prompt, algo)
            count += 1
            if count % 1000 == 0:
                pipe.execute()
    pipe.execute()
    print(f"Seeded {count} prompts into Redis {url}")


if __name__ == "__main__":
    main()


