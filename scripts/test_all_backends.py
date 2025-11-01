#!/usr/bin/env python3
"""
Test all backends and generate reports.

Usage:
    python scripts/test_all_backends.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx


BACKENDS = ["inmemory", "mongodb", "postgres", "memcached", "neo4j", "cassandra"]
BASE_URL = "http://localhost:8000"
TEST_PROMPTS = [
    "Classify customer reviews by sentiment",
    "Predict house prices from features",
    "Cluster data into groups",
    "Detect anomalies in data",
    "Recommend items to users",
]


async def test_backend(backend: str, base_url: str) -> dict:
    """Test a specific backend."""
    print(f"\n{'='*60}")
    print(f"Testing backend: {backend.upper()}")
    print(f"{'='*60}")
    
    # Set backend type via environment variable
    # Note: This won't work for a running server, so we'll use the API
    results = {
        "backend": backend,
        "success_count": 0,
        "error_count": 0,
        "errors": [],
        "responses": [],
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test recommendation endpoint
        for i, prompt in enumerate(TEST_PROMPTS):
            try:
                response = await client.post(
                    f"{base_url}/api/recommend",
                    json={"prompt": prompt},
                )
                if response.status_code == 200:
                    data = response.json()
                    results["success_count"] += 1
                    if data.get("recommendations"):
                        top_rec = data["recommendations"][0]
                        results["responses"].append({
                            "prompt": prompt,
                            "algorithm": top_rec.get("algorithm", "N/A"),
                            "score": top_rec.get("score", 0),
                        })
                        print(f"  [OK] Prompt {i+1}: {top_rec.get('algorithm', 'N/A')[:50]}")
                    else:
                        print(f"  [WARN] Prompt {i+1}: No recommendations")
                else:
                    results["error_count"] += 1
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                    results["errors"].append(error_msg)
                    print(f"  [ERROR] Prompt {i+1}: {error_msg}")
            except Exception as e:
                results["error_count"] += 1
                error_msg = str(e)
                results["errors"].append(error_msg)
                print(f"  [ERROR] Prompt {i+1}: {error_msg}")
        
        # Test reports endpoint
        try:
            print(f"\n  Testing reports endpoint...")
            response = await client.get(f"{base_url}/reports/usage")
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                print(f"  [OK] Usage report: {total} total selections")
            else:
                print(f"  [WARN] Usage report: HTTP {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] Usage report: {e}")
    
    return results


async def main():
    """Main test function."""
    print("="*60)
    print("Testing All Backends")
    print("="*60)
    print(f"\nNote: Make sure the server is running with BACKEND_TYPE set")
    print(f"      We'll test the current backend configuration")
    print(f"      To test different backends, restart the server with different BACKEND_TYPE")
    
    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code != 200:
                print(f"\n[ERROR] Server is not responding correctly at {BASE_URL}")
                print("  Please start the server first:")
                print("    uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000")
                return
    except Exception as e:
        print(f"\n[ERROR] Cannot connect to server at {BASE_URL}")
        print(f"  Error: {e}")
        print("  Please start the server first:")
        print("    uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000")
        return
    
    print(f"\n[OK] Server is running at {BASE_URL}")
    
    # Get current backend type
    current_backend = os.getenv("BACKEND_TYPE", "inmemory")
    print(f"  Current BACKEND_TYPE: {current_backend}")
    
    # Test current backend
    results = await test_backend(current_backend, BASE_URL)
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"Backend: {results['backend']}")
    print(f"Success: {results['success_count']}/{len(TEST_PROMPTS)}")
    print(f"Errors: {results['error_count']}")
    if results['errors']:
        print("\nErrors:")
        for err in results['errors']:
            print(f"  - {err}")
    
    print(f"\n{'='*60}")
    print("To test other backends:")
    print("  1. Stop the server (Ctrl+C)")
    print("  2. Set BACKEND_TYPE environment variable:")
    for backend in BACKENDS:
        if backend != current_backend:
            print(f"     $env:BACKEND_TYPE='{backend}'")
    print("  3. Restart the server")
    print("  4. Run this script again")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())

