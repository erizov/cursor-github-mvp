#!/usr/bin/env python3
"""
Performance test script to benchmark different backends.

Usage:
    python scripts/performance_test.py --backend=inmemory --requests=100
    python scripts/performance_test.py --backend=mongodb --requests=100
    python scripts/performance_test.py --backend=sqlite --requests=100
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, List
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests


def test_backend(base_url: str, backend: str, num_requests: int = 100) -> Dict:
    """Test a backend by sending requests and measuring performance."""
    results = {
        "backend": backend,
        "num_requests": num_requests,
        "total_time": 0,
        "requests_per_second": 0,
        "min_response_time": float("inf"),
        "max_response_time": 0,
        "avg_response_time": 0,
        "response_times": [],
        "success_count": 0,
        "error_count": 0,
        "errors": [],
    }
    
    test_prompts = [
        "Classify customer reviews by sentiment",
        "Predict house prices from features",
        "Cluster data into groups",
        "Detect anomalies in data",
        "Recommend items to users",
    ]
    
    start_time = time.time()
    response_times = []
    
    for i in range(num_requests):
        prompt = test_prompts[i % len(test_prompts)]
        request_start = time.time()
        
        try:
            response = requests.post(
                f"{base_url}/api/recommend",
                json={"prompt": prompt},
                timeout=10,
            )
            request_time = time.time() - request_start
            
            if response.status_code == 200:
                results["success_count"] += 1
                response_times.append(request_time)
                results["min_response_time"] = min(results["min_response_time"], request_time)
                results["max_response_time"] = max(results["max_response_time"], request_time)
            else:
                results["error_count"] += 1
                results["errors"].append(f"Status {response.status_code}")
        except Exception as e:
            results["error_count"] += 1
            results["errors"].append(str(e))
    
    results["total_time"] = time.time() - start_time
    
    if response_times:
        results["response_times"] = response_times
        results["avg_response_time"] = sum(response_times) / len(response_times)
        results["requests_per_second"] = len(response_times) / results["total_time"] if results["total_time"] > 0 else 0
        if results["min_response_time"] == float("inf"):
            results["min_response_time"] = 0
    
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Performance test for backends")
    parser.add_argument("--backend", type=str, required=True, choices=["inmemory", "mongodb", "sqlite"], help="Backend to test")
    parser.add_argument("--requests", type=int, default=500, help="Number of requests to send")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="Base URL of API")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    args = parser.parse_args()
    
    print(f"Testing {args.backend} backend with {args.requests} requests...")
    results = test_backend(args.base_url, args.backend, args.requests)
    
    print(f"\nResults:")
    print(f"  Backend: {results['backend']}")
    print(f"  Requests: {results['num_requests']}")
    print(f"  Success: {results['success_count']}")
    print(f"  Errors: {results['error_count']}")
    print(f"  Total Time: {results['total_time']:.2f}s")
    print(f"  Requests/sec: {results['requests_per_second']:.2f}")
    print(f"  Avg Response Time: {results['avg_response_time']*1000:.2f}ms")
    print(f"  Min Response Time: {results['min_response_time']*1000:.2f}ms")
    print(f"  Max Response Time: {results['max_response_time']*1000:.2f}ms")
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    sys.exit(0 if results["error_count"] == 0 else 1)


if __name__ == "__main__":
    main()

