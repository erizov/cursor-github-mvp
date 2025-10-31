#!/usr/bin/env python3
"""
Test all API endpoints to verify they accept the correct HTTP methods.

Usage:
    python scripts/test_all_endpoints.py [--base-url=http://localhost:8000]
"""

import argparse
import sys
from typing import Dict, List, Tuple
import requests


ENDPOINTS = [
    # Index endpoints
    ("GET", "/"),
    ("GET", "/index.json"),
    ("GET", "/api"),
    ("GET", "/readme"),
    ("GET", "/index.html"),
    ("GET", "/styles.css"),
    
    # Recommendations
    ("POST", "/api/recommend"),
    
    # Reports
    ("GET", "/api/reports"),
    ("GET", "/api/reports/index.json"),
    ("GET", "/api/reports/usage"),
    ("GET", "/api/reports/usage.html"),
    ("GET", "/api/reports/details"),
    ("GET", "/api/reports/details.html"),
    
    # Monitoring
    ("GET", "/api/monitoring"),
    ("GET", "/metrics"),
    ("GET", "/metrics.html"),
    
    # Tests
    ("GET", "/api/tests"),
    ("POST", "/api/tests/run"),
    ("POST", "/api/tests/unit"),
    ("POST", "/api/tests/pipeline"),
    
    # Cleanup
    ("POST", "/api/cleanup/images"),
    
    # Documentation (handled by FastAPI, but let's test them)
    ("GET", "/docs"),
    ("GET", "/redoc"),
    ("GET", "/openapi.json"),
]


def test_endpoint(base_url: str, method: str, path: str) -> Tuple[bool, str, int]:
    """Test an endpoint with the specified method."""
    url = f"{base_url}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            # For POST endpoints that don't require body
            if path in ["/api/tests/run", "/api/tests/unit", "/api/tests/pipeline", "/api/cleanup/images"]:
                response = requests.post(url, json={}, timeout=60)
            elif path == "/api/recommend":
                response = requests.post(
                    url,
                    json={"prompt": "test classification"},
                    timeout=10
                )
            else:
                response = requests.post(url, json={}, timeout=10)
        else:
            return False, f"Unsupported method: {method}", 0
        
        status = response.status_code
        
        # Accept 200, 201, 204, 400, 404 as valid (method allowed)
        # Reject 405 (Method Not Allowed)
        if status == 405:
            return False, f"Method Not Allowed", status
        elif status >= 200 and status < 500:
            return True, f"OK (status {status})", status
        else:
            return False, f"Unexpected status {status}", status
            
    except requests.exceptions.Timeout:
        return False, "Timeout", 0
    except requests.exceptions.ConnectionError:
        return False, "Connection Error (is server running?)", 0
    except Exception as e:
        return False, f"Error: {str(e)}", 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test all API endpoints to verify HTTP methods"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    args = parser.parse_args()
    
    print(f"Testing endpoints against {args.base_url}\n")
    print(f"{'Method':<8} {'Path':<40} {'Status':<20} {'Result'}")
    print("=" * 80)
    
    results: List[Tuple[str, str, bool, str, int]] = []
    
    for method, path in ENDPOINTS:
        success, message, status = test_endpoint(args.base_url, method, path)
        status_str = f"{status} {message}" if status else message
        result_str = "✓ PASS" if success else "✗ FAIL"
        results.append((method, path, success, message, status))
        print(f"{method:<8} {path:<40} {status_str:<20} {result_str}")
    
    print("\n" + "=" * 80)
    
    passed = sum(1 for _, _, s, _, _ in results if s)
    total = len(results)
    failed = total - passed
    
    print(f"\nSummary: {passed}/{total} passed, {failed} failed")
    
    if failed > 0:
        print("\nFailed endpoints:")
        for method, path, success, message, status in results:
            if not success:
                print(f"  {method} {path} - {message} (status: {status})")
        sys.exit(1)
    else:
        print("\nAll endpoints are working correctly!")
        sys.exit(0)


if __name__ == "__main__":
    main()

