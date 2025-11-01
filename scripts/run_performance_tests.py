#!/usr/bin/env python3
"""
Run performance tests for all backends and generate a report.

Usage:
    python scripts/run_performance_tests.py [--base-url=http://localhost:8000] [--requests=100]
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx


BACKENDS = ["inmemory", "mongodb", "postgres", "memcached", "neo4j", "cassandra"]
BASE_URL = "http://localhost:8000"


def test_performance_all(base_url: str, num_requests: int = 100) -> dict:
    """Run performance tests for all backends."""
    print("="*60)
    print("Running Performance Tests for All Backends")
    print("="*60)
    print(f"Base URL: {base_url}")
    print(f"Requests per backend: {num_requests}")
    print()
    
    try:
        response = httpx.post(
            f"{base_url}/api/performance/test-all",
            json={"num_requests": num_requests},
            timeout=600.0,  # 10 minutes timeout
        )
        response.raise_for_status()
        data = response.json()
        return data
    except httpx.HTTPError as e:
        print(f"Error: HTTP request failed: {e}")
        return {}
    except Exception as e:
        print(f"Error: {e}")
        return {}


def print_summary(results: dict):
    """Print a summary of performance test results."""
    if not results or "backends" not in results:
        print("No results to display")
        return
    
    print("\n" + "="*60)
    print("Performance Test Summary")
    print("="*60)
    
    backends = results.get("backends", {})
    backend_labels = {
        "inmemory": "In-Memory",
        "mongodb": "MongoDB",
        "postgres": "PostgreSQL",
        "memcached": "Memcached",
        "neo4j": "Neo4j",
        "cassandra": "Cassandra"
    }
    
    print(f"\n{'Backend':<15} {'Success':<10} {'Errors':<10} {'Inserts':<10} {'Updates':<10} {'Deletes':<10} {'Total Ops/s':<12}")
    print("-"*90)
    
    for backend in BACKENDS:
        result = backends.get(backend, {})
        if "error" in result:
            print(f"{backend_labels.get(backend, backend):<15} {'ERROR':<10} {result.get('error', 'Unknown')[:8]:<10}")
            continue
        
        success = result.get("success_count", 0)
        errors = result.get("error_count", 0)
        insert_count = result.get("insert_count", 0)
        update_count = result.get("update_count", 0)
        delete_count = result.get("delete_count", 0)
        total_ops_per_sec = result.get("db_operations_per_second", 0)
        
        print(f"{backend_labels.get(backend, backend):<15} {success:<10} {errors:<10} {insert_count:<10} {update_count:<10} {delete_count:<10} {total_ops_per_sec:<12.2f}")
    
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Run performance tests for all backends")
    parser.add_argument("--base-url", type=str, default=BASE_URL, help="Base URL of the API")
    parser.add_argument("--requests", type=int, default=100, help="Number of requests per backend")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    args = parser.parse_args()
    
    # Run tests
    results = test_performance_all(args.base_url, args.requests)
    
    if results:
        print_summary(results)
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to {args.output}")
    else:
        print("\n[ERROR] Failed to run performance tests")
        sys.exit(1)


if __name__ == "__main__":
    main()

