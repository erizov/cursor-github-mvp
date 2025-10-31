# AI Algorithm Teacher – Detailed Documentation

This document provides a complete, in-depth guide to running, using, testing,
and extending the AI Algorithm Teacher project. For a minimal quickstart,
see `README.md`. For a prescriptive generation prompt, see `cursor_prompt.md`.

## Overview

AI Algorithm Teacher is a rules-based helper that suggests AI/ML algorithms
from a natural-language description. It aims to be transparent and simple to
run locally, while supporting optional persistence and metrics.

Key components:
- FastAPI backend with endpoints for recommendations and reports
- In-memory repository by default; optional MongoDB
- Prometheus metrics exposed at `/metrics`
- Minimal HTML/JS report UI (`frontend/index.html`)
- Tests for API, end-to-end flows, metrics, and Docker

## Project Structure

```
backend/
  __init__.py
  app.py               # FastAPI app and router mounting
  db.py                # Optional MongoDB connection helpers
  logging_config.py    # Structured logging (structlog)
  models.py            # Pydantic models / schemas
  monitoring.py        # Prometheus instrumentation
  repositories.py      # In-memory + optional Mongo repository
  services.py          # Recommendation rules and logic
  routers/
    __init__.py
    index.py
    recommendations.py
    reports.py         # JSON and HTML usage reports
frontend/
  index.html           # Minimal usage chart UI
tests/
  conftest.py
  test_api.py
  test_e2e.py
  test_metrics.py
  test_docker.py
scripts/
  generate_prompts.py  # Builds prompts.txt (1000 prompts)
  seed_unique_requests.py # Seeds unique requests into Mongo (optional)
ai_algorithm_teacher.py   # CLI entry point
Dockerfile
docker-compose.yml
requirements.txt
```

## Running Locally (Recommended Minimal Path)

```
python -m pip install -r requirements.txt
uvicorn backend.app:app --reload
```

Open:
- API root: http://localhost:8000/
- Swagger: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics (if enabled)

### Example: Get Recommendations

```
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Classify customer reviews by sentiment"}'
```

### Usage Reports

JSON counts:
```
curl http://localhost:8000/api/reports/usage
```

HTML chart:
```
curl http://localhost:8000/api/reports/usage.html
```
Or visit in the browser: `http://localhost:8000/api/reports/usage.html`

## Docker

### Build
```
docker build -t algorithm-teacher .
```

### Run (no DB required)
```
docker run --name algorithm-teacher -p 8000:8000 algorithm-teacher
```

### Docker Compose (with MongoDB)

Brings up API and MongoDB:
```
docker-compose up
```

Services started:
- api: FastAPI on port 8000
- mongo: MongoDB 7 on port 27017

## Configuration

Environment variables:
- `MONGODB_URI` – MongoDB connection string (optional)
- `MONGODB_DB` – MongoDB database name (optional)
- `LOG_LEVEL` – Logging level (default `INFO`)

When Mongo settings are not provided, the repository runs in-memory.

## Recommendation Logic

Core rules live in `backend/services.py`. The service maps hints in the
prompt (e.g., classification/regression/clustering/time series, interpretability,
data size, latency) to a shortlist of algorithms and brief explanations.

Guidelines for extending rules:
- Prefer explicit, readable if/else logic with descriptive variable names
- Keep each rule small; avoid deep nesting
- Add tests covering new paths

## Reports & Analytics

Endpoints in `backend/routers/reports.py`:
- `GET /api/reports/usage` – JSON with total and per-algorithm counts
- `GET /api/reports/usage.html` – HTML chart of usage counts
- `GET /api/reports/details` – Detailed JSON grouped by algorithm
- `GET /api/reports/details.html` – Detailed HTML view

Features:
- Color-coded bars
- Totals and percentages
- Responsive layout

## Metrics

Exposed at `GET /metrics` via `prometheus-fastapi-instrumentator`.
Custom counters may include:
- `recommendations_total` – total recommendation requests served
- `algorithm_top_selections_total{algorithm="..."}` – count of top picks

## Tests

Install and run:
```
python -m pip install -r requirements.txt
pytest -q
```

Suites:
- `test_api.py` – Unit-ish API test for `POST /api/recommend` and reports
- `test_e2e.py` – End-to-end flow
- `test_metrics.py` – Metrics availability
- `test_docker.py` – Docker build/run and e2e container checks

Run a specific Docker test:
```
pytest tests/test_docker.py::test_docker_e2e_full_workflow -v -s
```

Skip Docker tests:
```
pytest -q -k "not docker"
```

## Unique Requests Database (Optional)

The system can store unique user prompts and their categorized algorithm types
in MongoDB to analyze distinct user needs.

### Features
- Automatic storage when recommendations are made (if repository uses Mongo)
- Deduplication (case-insensitive) of prompts
- Algorithm type categorization (classification/regression/etc.)

### Seeding 1000 Prompts

Generate prompts:
```
python scripts/generate_prompts.py
```
This creates `prompts.txt` with 1000 unique prompts.

Seed MongoDB:
```
python scripts/seed_unique_requests.py
```

Prerequisites:
- MongoDB is running and accessible
- `MONGODB_URI` and `MONGODB_DB` set (or defaults used)

The seeding script:
- Reads prompts, uses the recommendation engine to categorize
- Stores unique requests in `unique_requests` collection
- Skips duplicates automatically

## CI/CD (GitHub Actions)

Workflow in `.github/workflows/ci.yml` (if present) typically runs on push/PR
to `main`, `master`, or `develop` and includes jobs for unit/e2e tests and
Docker build checks. It verifies the image builds and the container responds.

## Troubleshooting

- Cannot import `backend` in tests:
  - Ensure tests run from repo root (relies on `tests/conftest.py`).

- MongoDB connection errors:
  - Set `MONGODB_URI` and `MONGODB_DB` or start a local MongoDB at
    `mongodb://localhost:27017`.
  - Tests default to in-memory repository; Mongo is optional.

- Metrics not available:
  - Confirm server is running; visit `http://localhost:8000/metrics`.

- No recommendations returned:
  - Provide clearer task hints (e.g., classification/regression/clustering,
    data modality: text/image/time series).

- Frontend report fails to load:
  - Serve `frontend/index.html` from the same origin as the API or adjust the
    fetch URL to point to the API origin.

## Coding Conventions

- PEP 8, UTF-8, 4 spaces, line length ≤ 79
- Imports grouped: stdlib → third-party → local (one per line)
- Naming: snake_case (modules/functions/vars), CapWords (classes),
  UPPER_SNAKE_CASE (constants), private with leading underscore
- Type hints for public functions and return values
- Use `is`/`is not` for `None`; check emptiness with `if items:`
- Avoid bare `except:`; avoid mutable default arguments
- Use a logger in server code (no `print` in services/routers)

## Notes

- Transparent, rules-based guidance; not a full AutoML system.
- The in-memory default is intentional for simplicity; MongoDB is optional.


