#!/usr/bin/env python3
"""
Test the test execution endpoints to verify they run without permission errors.

Usage:
    python scripts/test_test_endpoints.py [--base-url=http://localhost:8000]
"""

import argparse
import sys
import requests
import json


def test_endpoint(base_url: str, endpoint: str, method: str = "POST") -> dict:
    """Test a test endpoint and return results."""
    url = f"{base_url}{endpoint}"
    
    try:
        if method == "POST":
            response = requests.post(url, json={}, timeout=120)
        else:
            response = requests.get(url, timeout=10)
        
        data = response.json()
        status = response.status_code
        
        # Check for permission errors in stderr
        stderr = data.get("stderr", "")
        has_permission_error = (
            "permission denied" in stderr.lower() or
            "access denied" in stderr.lower() or
            "permission" in stderr.lower() and "error" in stderr.lower()
        )
        
        # Check returncode
        returncode = data.get("returncode", -1)
        passed = data.get("passed", False)
        
        return {
            "endpoint": endpoint,
            "status_code": status,
            "returncode": returncode,
            "passed": passed,
            "has_permission_error": has_permission_error,
            "stderr_preview": stderr[:200] if stderr else "",
            "stdout_preview": data.get("stdout", "")[:100] if data.get("stdout") else "",
            "error": data.get("error"),
        }
    except requests.exceptions.Timeout:
        return {
            "endpoint": endpoint,
            "status_code": 0,
            "error": "Timeout",
            "has_permission_error": False,
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "status_code": 0,
            "error": str(e),
            "has_permission_error": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test test execution endpoints for permission errors"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    args = parser.parse_args()
    
    print(f"Testing test endpoints against {args.base_url}\n")
    print("=" * 80)
    
    endpoints = [
        ("POST", "/api/tests/run"),
        ("POST", "/api/tests/unit"),
        ("POST", "/api/tests/pipeline"),
    ]
    
    results = []
    for method, endpoint in endpoints:
        print(f"\nTesting {method} {endpoint}...")
        result = test_endpoint(args.base_url, endpoint, method)
        results.append(result)
        
        # Print summary
        if result.get("error"):
            print(f"  ❌ Error: {result['error']}")
        elif result.get("has_permission_error"):
            print(f"  ⚠️  PERMISSION ERROR DETECTED in stderr!")
            print(f"     Status: {result['status_code']}")
            print(f"     Returncode: {result.get('returncode', 'N/A')}")
            print(f"     Stderr preview: {result['stderr_preview']}")
        elif result.get("status_code") == 405:
            print(f"  ❌ Method Not Allowed")
        elif result.get("passed"):
            print(f"  ✅ PASSED - Returncode: {result.get('returncode', 0)}")
            print(f"     Stdout preview: {result.get('stdout_preview', '')}")
        else:
            print(f"  ⚠️  FAILED - Returncode: {result.get('returncode', -1)}")
            if result.get("stderr_preview"):
                print(f"     Stderr preview: {result['stderr_preview']}")
    
    print("\n" + "=" * 80)
    print("\nSummary:")
    
    passed = sum(1 for r in results if r.get("passed") and not r.get("has_permission_error") and not r.get("error"))
    failed = sum(1 for r in results if not r.get("passed") and not r.get("error") and r.get("status_code") != 405)
    errors = sum(1 for r in results if r.get("error"))
    permission_errors = sum(1 for r in results if r.get("has_permission_error"))
    
    print(f"  ✅ Passed: {passed}/{len(results)}")
    if failed > 0:
        print(f"  ❌ Failed: {failed}")
    if errors > 0:
        print(f"  ⚠️  Errors: {errors}")
    if permission_errors > 0:
        print(f"  🚨 Permission Errors: {permission_errors}")
    
    if permission_errors > 0:
        print("\n🚨 PERMISSION ERRORS FOUND:")
        for r in results:
            if r.get("has_permission_error"):
                print(f"  - {r['endpoint']}")
                print(f"    {r['stderr_preview']}")
        sys.exit(1)
    elif passed == len(results):
        print("\n✅ All endpoints work correctly without permission errors!")
        sys.exit(0)
    else:
        print("\n⚠️  Some endpoints have issues (but no permission errors)")
        sys.exit(1)


if __name__ == "__main__":
    main()

