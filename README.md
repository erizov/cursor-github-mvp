AI Algorithm Teacher

A simple rules-based tool that suggests AI/ML algorithms from a natural-language description, with explanations, next steps, and learning resources. It includes a FastAPI backend, MongoDB persistence, Prometheus metrics, and a minimal React report UI.

## Project structure

```
E:\Python\Cursor\4
├─ backend
│  ├─ __init__.py
│  ├─ app.py
│  ├─ db.py
│  ├─ logging_config.py
│  ├─ models.py
│  ├─ monitoring.py
│  ├─ repositories.py
│  ├─ services.py
│  └─ routers
│     ├─ __init__.py
│     ├─ index.py
│     ├─ recommendations.py
│     └─ reports.py
├─ frontend
│  ├─ index.html
│  └─ styles.css
├─ tests
│  ├─ conftest.py
│  ├─ test_api.py
│  ├─ test_e2e.py
│  ├─ test_metrics.py
│  └─ test_docker.py
├─ .github
│  └─ workflows
│     └─ ci.yml
├─ scripts
│  ├─ generate_prompts.py
│  └─ seed_unique_requests.py
├─ ai_algorithm_teacher.py
├─ Dockerfile
├─ docker-compose.yml
├─ .dockerignore
├─ README.md
└─ requirements.txt
```

## Usage

### CLI

- Inline prompt:

```
python ai_algorithm_teacher.py "Forecast weekly demand with seasonality and promotions; low latency not required"
```

- Interactive prompt:

```
python ai_algorithm_teacher.py
```

- Example prompts:
  - "Classify customer reviews by sentiment with a small labeled dataset and need interpretability"
  - "Cluster customers into segments using transaction and behavior features"
  - "Detect anomalies in streaming metrics with few labeled examples"
  - "Forecast monthly sales with trend and yearly seasonality"
  - "Build a recommendation system for users and items"

### API

- Run server:

```
uvicorn backend.app:app --reload
```

- Get recommendations:

```
curl -X POST http://localhost:8000/api/recommend -H "Content-Type: application/json" -d '{"prompt":"Classify reviews by sentiment"}'
```

- Usage report:

```
curl http://localhost:8000/api/reports/usage
```

### Reports & Analytics

The API provides multiple endpoints for viewing usage statistics and detailed reports.

#### Usage Report (JSON)

Get algorithm usage counts as JSON:

```bash
curl http://localhost:8000/api/reports/usage
```

Response format:
```json
{
  "total": 10,
  "counts": [
    {"algorithm": "Random Forest", "count": 3},
    {"algorithm": "XGBoost", "count": 2},
    ...
  ]
}
```

#### Usage Report (HTML)

Get a styled HTML report with colored bars:

```bash
curl http://localhost:8000/api/reports/usage.html
```

Or visit in browser: `http://localhost:8000/api/reports/usage.html`

Features:
- Color-coded algorithm bars
- Total usage count
- Percentage breakdowns
- Responsive design

#### Detailed Report (JSON)

Get detailed report with user prompts and timestamps, grouped by algorithm:

```bash
curl http://localhost:8000/api/reports/details
```

Response format:
```json
{
  "total": 10,
  "groups": [
    {
      "algorithm": "Random Forest",
      "count": 3,
      "items": [
        {
          "algorithm": "Random Forest",
          "prompt": "Classify customer reviews...",
          "created_at": "2025-10-30T12:00:00Z"
        },
        ...
      ]
    },
    ...
  ]
}
```

Groups are sorted by:
1. Algorithm type (ascending)
2. Within each group, items sorted by created_at (descending)

#### Detailed Report (HTML)

Get a styled HTML detailed report:

```bash
curl http://localhost:8000/api/reports/details.html
```

Or visit in browser: `http://localhost:8000/api/reports/details.html`

Features:
- Grouped by algorithm type
- Shows user prompts
- Timestamps for each selection
- Color-coded sections
- Empty state guidance

### Frontend Report UI

Open `frontend/index.html` (loads React via CDN) and it will call `GET /api/reports/usage` to render colored usage bars.

Features:
- Interactive usage visualization
- Real-time data from API
- Responsive design

### Docker

#### Build Docker Image

```bash
docker build -t algorithm-teacher .
```

The Dockerfile:
- Uses Python 3.11 slim base image
- Copies application code and dependencies
- Sets working directory to `/app`
- Exposes port 8000
- Runs uvicorn with `--host 0.0.0.0`

#### Run with Docker Compose

Includes MongoDB service automatically:

```bash
docker-compose up
```

This starts:
- **api** service: FastAPI application on port 8000
- **mongo** service: MongoDB 7 on port 27017
- Automatic networking between containers
- Volume persistence for MongoDB data

Access:
- API: `http://localhost:8000`
- MongoDB: `mongodb://localhost:27017`

#### Run Standalone Container

**With external MongoDB:**
```bash
docker run --name algorithm-teacher -p 8000:8000 \
  -e MONGODB_URI=mongodb://host.docker.internal:27017 \
  -e MONGODB_DB=algorithm_teacher \
  algorithm-teacher
```

**With Docker network (requires MongoDB container):**
```bash
# Create network
docker network create algo-network

# Start MongoDB
docker run -d --name mongo \
  --network algo-network \
  -p 27017:27017 \
  mongo:7

# Start app
docker run -d --name algorithm-teacher \
  --network algo-network \
  -p 8000:8000 \
  -e MONGODB_URI=mongodb://mongo:27017 \
  -e MONGODB_DB=algorithm_teacher \
  algorithm-teacher
```

#### Docker Tests

**Run all Docker tests:**
```bash
pytest tests/test_docker.py -v
```

Tests included:
1. `test_docker_build`: Verifies Docker image builds successfully
2. `test_docker_run`: Verifies container starts and responds to GET requests
3. `test_docker_api_endpoints`: Tests all API endpoints with MongoDB
4. `test_docker_e2e_full_workflow`: Full e2e workflow with multiple prompts

**Run specific test:**
```bash
pytest tests/test_docker.py::test_docker_e2e_full_workflow -v -s
```

**Test details:**
- Automatically creates Docker networks
- Starts MongoDB containers when needed
- Uses unique container names and ports to avoid conflicts
- Cleans up containers and networks after tests
- Waits for containers to be ready before testing
- Captures and displays logs on failures

**Skip Docker tests:**
```bash
pytest -q -k "not docker"
```

**Requirements:**
- Docker Desktop must be running (Windows/Mac)
- Or Docker daemon running (Linux)
- At least 2GB free disk space for images

**Note:** First run may take longer while pulling MongoDB image (~700MB). Subsequent runs use cached images.

## Tests

- Install deps:

```
python -m pip install -r requirements.txt
```

- Run tests:

```
pytest -q
```

- Tests include:
  - Unit-ish API test for `POST /api/recommend` and `GET /api/reports/usage` with an in-memory repo
  - Unique requests test verifying deduplication and algorithm type categorization
  - Metrics endpoint availability test for `GET /metrics`
  - E2E test posting multiple prompts then verifying usage totals
  - Docker build and run tests (`tests/test_docker.py`), including full e2e workflow test

## Logs

- Structured JSON logging via structlog.
- Configure level with env: `LOG_LEVEL=DEBUG` (default INFO).
- Request logs include method, path, status, client; prompts are not logged (only length) to reduce PII risk.

## CI/CD

### GitHub Actions Workflow

GitHub Actions workflow (`.github/workflows/ci.yml`) runs automatically on push/PR to `main`, `master`, or `develop` branches.

#### Jobs

1. **test** job:
   - Runs on: `ubuntu-latest`
   - Steps:
     - Sets up Python 3.11
     - Installs dependencies from `requirements.txt`
     - Runs all pytest tests: `pytest -q --tb=short`
   - Tests included:
     - Unit API tests (`test_api.py`)
     - E2E tests (`test_e2e.py`)
     - Metrics tests (`test_metrics.py`)
     - Docker tests (build/run only, no MongoDB)

2. **docker-build** job:
   - Runs on: `ubuntu-latest`
   - Steps:
     - Sets up Docker Buildx
     - Builds Docker image: `docker build -t algorithm-teacher:test .`
     - Starts container: `docker run -d --name test-container -p 8000:8000 algorithm-teacher:test`
     - Verifies container responds: `curl -f http://localhost:8000/`
     - Shows container logs
     - Cleans up container
   - Verifies: Image builds successfully and container starts

3. **docker-e2e** job:
   - Runs on: `ubuntu-latest`
   - Services:
     - MongoDB 7 on port 27017 (GitHub Actions service)
   - Steps:
     - Builds Docker image
     - Runs container with MongoDB connection:
       ```bash
       docker run -d \
         --name test-app \
         --network host \
         -e MONGODB_URI=mongodb://localhost:27017 \
         -e MONGODB_DB=test_db \
         algorithm-teacher:test
       ```
     - Waits for container startup (5 seconds)
     - Runs e2e tests against container:
       ```bash
       pytest -q tests/test_e2e.py -v
       ```
     - Cleans up container (always, even on failure)
   - Verifies: Full e2e workflow with MongoDB persistence

### Local CI Test Execution

Run all CI tests locally:

```bash
# Run all tests (unit, e2e, docker)
pytest tests/ -v

# Run only Docker tests
pytest tests/test_docker.py -v

# Run specific Docker test
pytest tests/test_docker.py::test_docker_e2e_full_workflow -v -s
```

Docker tests automatically:
- Create Docker networks
- Start MongoDB containers (if needed)
- Start app containers with proper environment variables
- Clean up containers and networks after tests

## Monitoring

- Prometheus metrics exposed at `GET /metrics` using `prometheus-fastapi-instrumentator`.
- Custom counters:
  - `recommendations_total` – total recommendation requests served
  - `algorithm_top_selections_total{algorithm="..."}` – count of top recommended algorithms

## Troubleshooting

- Cannot import `backend` in tests:
  - Ensure tests run from repo root (uses `tests/conftest.py` to set `sys.path`).

- MongoDB connection errors:
  - Set `MONGODB_URI` and `MONGODB_DB` environment variables, or start a local MongoDB at `mongodb://localhost:27017`.
  - Tests do not require MongoDB; they use an in-memory repository via dependency overrides.

- Metrics not available:
  - Confirm server is running and visit `http://localhost:8000/metrics`.

- No recommendations returned:
  - Provide clearer task hints like "classification", "regression", "clustering", and data modality (text/image/time series).

- Frontend report fails to load:
  - Serve `frontend/index.html` from the same origin as the API or adjust fetch URL to the API origin.

## Unique Requests Database

The system maintains a MongoDB collection of unique user requests categorized by algorithm type. This allows tracking distinct AI/ML problems submitted by users.

### Features

- **Automatic Storage**: Unique requests are automatically stored when recommendations are made
- **Deduplication**: Duplicate prompts (case-insensitive) are not stored twice
- **Algorithm Type Categorization**: Each request is categorized by the recommended algorithm type:
  - Classification
  - Regression
  - Clustering
  - Time Series
  - NLP
  - Vision
  - Anomaly Detection
  - Recommender Systems
  - Reinforcement Learning
  - Causal Inference
  - Dimensionality Reduction
  - Other

### Seeding Database with 1000 Prompts

The project includes scripts to generate and seed 1000 unique AI/ML prompts:

**Generate prompts:**
```bash
python scripts/generate_prompts.py
```

This creates `prompts.txt` with 1000 unique prompts across all algorithm categories.

**Seed database:**
```bash
python scripts/seed_unique_requests.py
```

This script:
- Reads prompts from `generate_prompts.py`
- Uses the recommendation engine to verify algorithm type categorization
- Stores unique requests in the `unique_requests` MongoDB collection
- Skips duplicates automatically

**Prerequisites for seeding:**
- MongoDB must be running and accessible
- Set `MONGODB_URI` and `MONGODB_DB` environment variables if needed
- Default connection: `mongodb://localhost:27017` with database `ai_algo_teacher`

The seeding script will:
- Add 1000 unique prompts (or fewer if duplicates are found)
- Display progress every 100 prompts
- Show final counts by algorithm type

## Notes

- Transparent, rules-based engine for education and quick guidance; not a full AutoML system.
- Unique requests are only stored when recommendations are successfully generated (at least one algorithm recommended).


