## Cursor Project Prompt: AI Algorithm Teacher

### Overview
AI Algorithm Teacher is a rules-based helper that recommends AI/ML algorithms
from natural-language descriptions. It provides:
- FastAPI backend with endpoints for recommendations and reports
- Optional MongoDB persistence
- Prometheus metrics at `/metrics`
- Minimal HTML/JS report UI
- Tests for API, E2E flows, and Docker

### Tech Stack
- Python 3.11
- FastAPI, Uvicorn
- `pymongo` (MongoDB optional)
- `prometheus-fastapi-instrumentator`
- Pytest
- Docker and Docker Compose (optional)

### How to Run (Dev)
1) Install deps:
```
python -m pip install -r requirements.txt
```
2) Start API:
```
uvicorn backend.app:app --reload
```
3) Open:
- API root: http://localhost:8000/
- Recommendations (POST): `/api/recommend`
- Usage report (JSON): `/api/reports/usage`
- Usage report (HTML): `/api/reports/usage.html`
- Metrics: `/metrics`

### Docker
- Build:
```
docker build -t algorithm-teacher .
```
- Run (external Mongo):
```
docker run --name algorithm-teacher -p 8000:8000 \
  -e MONGODB_URI=mongodb://host.docker.internal:27017 \
  -e MONGODB_DB=algorithm_teacher \
  algorithm-teacher
```
- Compose (with MongoDB):
```
docker-compose up
```

### Tests
```
python -m pip install -r requirements.txt
pytest -q
```
Key suites:
- Unit-ish API tests
- E2E tests creating multiple prompts
- Docker build/run tests
- Metrics endpoint test

### Project Structure (key paths)
```
backend/
  app.py               # FastAPI app and routes mounting
  services.py          # Core recommendation logic
  repositories.py      # Persistence abstraction (in-memory, Mongo)
  routers/             # API routers (index, recommendations, reports)
frontend/
  index.html           # Minimal report UI (fetches /api/reports/usage)
tests/
  test_api.py, test_e2e.py, test_metrics.py, test_docker.py
scripts/
  generate_prompts.py, seed_unique_requests.py
ai_algorithm_teacher.py # CLI entry point
```

### Coding Conventions (enforced preferences)
- PEP 8, UTF-8, 4-space indents, max line length 79
- Imports grouped: stdlib → third-party → local, one per line
- Naming: snake_case (modules/functions/vars), CapWords (classes),
  UPPER_SNAKE_CASE (constants), private with leading underscore
- Type hints for public functions and return types
- Use `is`/`is not` for `None`; check emptiness with `if items:`
- No bare `except:`; avoid mutable default args
- Use logger for server code (no `print`)

### Contribution Guidance for Cursor
- Prefer small, focused edits; keep functions short and readable
- Add or extend tests for new behavior
- Maintain existing API contracts and response shapes
- When touching DB logic, keep `repositories.py` abstractions intact
- Keep metrics backward compatible where possible
- For user-visible changes, update `README.md`

### Git Workflow
- Default branch: `main` (synchronized with `master`)
- Open PRs from feature branches into `main`
- Keep `.gitignore` exclusions for caches, venvs, and office docs

### Non-Goals
- This is not AutoML; it offers transparent, rules-based guidance

### Quick Task Ideas
- Expand algorithm rules/coverage in `services.py`
- Add more detailed HTML reports in `routers/reports.py`
- Enhance frontend styling in `frontend/styles.css`
- Improve metrics or add histograms for latency


