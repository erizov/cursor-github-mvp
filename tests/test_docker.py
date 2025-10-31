import subprocess
import time
import requests
from datetime import datetime
from pathlib import Path


def get_image_name(tag: str = "") -> str:
    """Generate timestamped image name: alg-teach-yyyymmdd-hhmmss"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"alg-teach-{timestamp}"


def test_docker_build():
    """Test that Docker image builds successfully."""
    project_root = Path(__file__).resolve().parents[1]
    image_name = get_image_name()
    result = subprocess.run(
        ["docker", "build", "-t", image_name, "."],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"
    # Docker Desktop outputs to stderr, traditional Docker outputs to stdout
    output = result.stdout + result.stderr
    assert ("Successfully tagged" in output or 
            f"naming to docker.io/library/{image_name}" in output or
            image_name in output)


def test_docker_run():
    """Test that Docker container runs and responds to requests."""
    project_root = Path(__file__).resolve().parents[1]
    image_name = get_image_name()
    
    # Build first
    build_result = subprocess.run(
        ["docker", "build", "-t", image_name, "."],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert build_result.returncode == 0
    
    # Run container
    container_name = "test-algorithm-teacher"
    try:
        run_result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "-p",
                "8001:8000",
                image_name,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        assert run_result.returncode == 0, f"Failed to start container: {run_result.stderr}"
        
        # Wait for container to be ready with retries
        max_wait = 30
        wait_interval = 2
        for i in range(max_wait // wait_interval):
            time.sleep(wait_interval)
            try:
                response = requests.get("http://localhost:8001/", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if i == (max_wait // wait_interval) - 1:
                    # Get container logs for debugging
                    logs = subprocess.run(
                        ["docker", "logs", container_name],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    raise AssertionError(f"Container not ready after {max_wait}s. Logs: {logs.stdout}")
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8001/", timeout=10)
            assert response.status_code == 200
        finally:
            # Cleanup
            subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True,
                timeout=10,
            )
    except Exception as e:
        # Ensure cleanup on error
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        subprocess.run(["docker", "rm", container_name], capture_output=True)
        raise


def test_docker_api_endpoints():
    """Test that API endpoints work in Docker container."""
    project_root = Path(__file__).resolve().parents[1]
    container_name = "test-api-container"
    mongo_container = "test-mongo-api"
    port = 8002
    
    network_name = "test-network-api"
    try:
        # Clean up any leftover containers from previous runs
        subprocess.run(
            ["docker", "rm", "-f", container_name, mongo_container],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        subprocess.run(
            ["docker", "network", "rm", network_name],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        
        # Create Docker network
        subprocess.run(
            ["docker", "network", "create", network_name],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        
        # Build and start MongoDB (with longer timeout for image pull)
        mongo_result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                mongo_container,
                "--network",
                network_name,
                "-p",
                "27018:27017",
                "mongo:7",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        # Check if container already exists or other error
        if mongo_result.returncode != 0 and "already in use" not in mongo_result.stderr.lower():
            # Clean up and try again
            subprocess.run(
                ["docker", "rm", "-f", mongo_container],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
        
        # Wait for MongoDB to be ready
        time.sleep(3)
        
        # Build and run app container
        image_name = get_image_name()
        subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=str(project_root),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "--network",
                network_name,
                "-p",
                f"{port}:8000",
                "-e",
                "USE_IN_MEMORY=0",
                "-e",
                f"MONGODB_URI=mongodb://{mongo_container}:27017",
                "-e",
                "MONGODB_DB=test_db",
                image_name,
            ],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        base_url = f"http://localhost:{port}"
        
        # Wait for container to be ready with retries
        max_wait = 30
        wait_interval = 2
        for i in range(max_wait // wait_interval):
            time.sleep(wait_interval)
            try:
                response = requests.get(f"{base_url}/", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if i == (max_wait // wait_interval) - 1:
                    logs = subprocess.run(
                        ["docker", "logs", container_name],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    raise AssertionError(f"Container not ready after {max_wait}s. Logs: {logs.stdout}")
        
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=10)
        assert response.status_code == 200
        
        # Test API index
        response = requests.get(f"{base_url}/api", timeout=10)
        assert response.status_code == 200
        
        # Test recommend endpoint
        response = requests.post(
            f"{base_url}/api/recommend",
            json={"prompt": "Classify customer reviews"},
            timeout=10,
        )
        if response.status_code != 200:
            # Get container logs for debugging
            logs = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            print(f"Container logs: {logs.stdout}")
        assert response.status_code == 200, f"POST failed with {response.status_code}: {response.text}"
        assert "recommendations" in response.json()
        
        # Test usage report
        response = requests.get(f"{base_url}/api/reports/usage", timeout=10)
        assert response.status_code == 200
        assert "total" in response.json()
    finally:
        subprocess.run(
            ["docker", "stop", container_name],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        subprocess.run(
            ["docker", "rm", container_name],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        subprocess.run(
            ["docker", "stop", mongo_container],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        subprocess.run(
            ["docker", "rm", mongo_container],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        subprocess.run(
            ["docker", "network", "rm", network_name],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )


def test_docker_e2e_full_workflow():
    """Full e2e test: build Docker image, start container, run multiple prompts, verify reports."""
    project_root = Path(__file__).resolve().parents[1]
    container_name = "test-e2e-container"
    mongo_container = "test-mongo-e2e"
    network_name = "test-network-e2e"
    port = 8003
    base_url = f"http://localhost:{port}"
    
    try:
        # Clean up any leftover containers from previous runs
        subprocess.run(
            ["docker", "rm", "-f", container_name, mongo_container],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        subprocess.run(
            ["docker", "network", "rm", network_name],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        
        # Build Docker image
        print("Building Docker image...")
        image_name = get_image_name()
        build_result = subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        assert build_result.returncode == 0, f"Build failed: {build_result.stderr}"
        # Docker Desktop outputs to stderr, traditional Docker outputs to stdout
        output = build_result.stdout + build_result.stderr
        assert ("Successfully tagged" in output or 
                f"naming to docker.io/library/{image_name}" in output or
                image_name in output)
        
        # Create Docker network
        network_result = subprocess.run(
            ["docker", "network", "create", network_name],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        # Network might already exist, that's OK
        
        # Start MongoDB (with longer timeout for image pull)
        print("Starting MongoDB container...")
        mongo_result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                mongo_container,
                "--network",
                network_name,
                "-p",
                "27019:27017",
                "mongo:7",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        # Check if container already exists
        if mongo_result.returncode != 0 and "already in use" not in mongo_result.stderr.lower():
            # Clean up and try again
            subprocess.run(
                ["docker", "rm", "-f", mongo_container],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            mongo_result = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    mongo_container,
                    "--network",
                    network_name,
                    "-p",
                    "27019:27017",
                    "mongo:7",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
        assert mongo_result.returncode == 0, f"Failed to start MongoDB: {mongo_result.stderr}"
        
        # Wait for MongoDB to be ready
        time.sleep(3)
        
        # Start app container
        print("Starting app container...")
        run_result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "--network",
                network_name,
                "-p",
                f"{port}:8000",
                "-e",
                "USE_IN_MEMORY=0",
                "-e",
                f"MONGODB_URI=mongodb://{mongo_container}:27017",
                "-e",
                "MONGODB_DB=test_db",
                image_name,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        assert run_result.returncode == 0, f"Failed to start container: {run_result.stderr}"
        
        # Wait for container to be ready
        print("Waiting for container to be ready...")
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(f"{base_url}/", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if i < max_retries - 1:
                    time.sleep(2)
                else:
                    # Get container logs for debugging
                    logs = subprocess.run(
                        ["docker", "logs", container_name],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    raise AssertionError(f"Container not ready after {max_retries * 2} seconds. Logs: {logs.stdout}")
        
        # Run e2e scenarios
        prompts = [
            "Classify customer reviews by sentiment with a small labeled dataset",
            "Predict house prices from numerical features",
            "Cluster customers into segments based on transactions",
            "Forecast monthly demand with trend and seasonality",
            "Detect anomalies in server metrics with rare spikes",
            "Recommend items to users based on interaction history",
        ]
        
        print(f"Running {len(prompts)} recommendation requests...")
        for prompt in prompts:
            response = requests.post(
                f"{base_url}/api/recommend",
                json={"prompt": prompt},
                timeout=10,
            )
            assert response.status_code == 200, f"Recommendation failed for: {prompt}"
            body = response.json()
            assert "recommendations" in body, f"No recommendations in response: {body}"
            assert len(body["recommendations"]) > 0, "Empty recommendations list"
        
        # Verify usage report
        print("Verifying usage report...")
        response = requests.get(f"{base_url}/api/reports/usage", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == len(prompts), f"Expected {len(prompts)} total, got {data['total']}"
        assert sum(c["count"] for c in data["counts"]) == len(prompts)
        assert len(data["counts"]) >= 1, "No algorithm counts found"
        
        # Verify detailed report
        print("Verifying detailed report...")
        response = requests.get(f"{base_url}/api/reports/details", timeout=10)
        assert response.status_code == 200
        details = response.json()
        assert details["total"] == len(prompts)
        assert len(details["groups"]) >= 1, "No algorithm groups found"
        
        # Verify metrics endpoint
        print("Verifying metrics endpoint...")
        response = requests.get(f"{base_url}/metrics", timeout=10)
        assert response.status_code == 200
        assert "recommendations_total" in response.text
        
        print("All e2e tests passed!")
        
    finally:
        # Cleanup
        print("Cleaning up containers...")
        subprocess.run(
            ["docker", "stop", container_name],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        subprocess.run(
            ["docker", "rm", container_name],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        subprocess.run(
            ["docker", "stop", mongo_container],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        subprocess.run(
            ["docker", "rm", mongo_container],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        # Network cleanup
        subprocess.run(
            ["docker", "network", "rm", network_name],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )

