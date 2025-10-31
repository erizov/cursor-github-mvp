## Cursor Project Prompt: AI Algorithm Teacher (Simplified)

You are generating or editing a small FastAPI service that recommends AI/ML
algorithms from a short natural-language description. Keep it minimal and easy
to run locally.

### Goals
- In-memory by default (no external DB required)
- Clean API: `POST /api/recommend`, reports at `/api/reports/usage(.html)`
- Small frontend page in `frontend/index.html` that fetches usage stats
- Keep tests green: unit-ish API, e2e flow, metrics endpoint

### Non-goals (do NOT add by default)
- No mandatory MongoDB. DB is optional via `repositories.py` abstraction
- No heavy metrics or dashboards beyond `/metrics` if already present
- No complex UI; keep the HTML minimal and self-contained

### Run locally
```
python -m pip install -r requirements.txt
uvicorn backend.app:app --reload
```

### Endpoints
- `POST /api/recommend` with JSON `{ "prompt": "..." }` returns algorithms
- `GET /api/reports/usage` returns counts JSON
- `GET /api/reports/usage.html` returns a simple chart
- `GET /metrics` (optional; keep current behavior if present)

### Project layout (expected)
```
backend/
  app.py            # FastAPI app and router mounting
  services.py       # Recommendation rules
  repositories.py   # In-memory + optional Mongo behind an interface
  routers/          # index, recommendations, reports
frontend/
  index.html        # Minimal usage chart
tests/
  test_api.py, test_e2e.py, test_metrics.py, test_docker.py
ai_algorithm_teacher.py  # CLI entry point
```

### Coding conventions
- PEP 8, UTF-8, 4 spaces, line length ≤ 79
- Imports: stdlib → third-party → local, one per line
- Use type hints for public interfaces; no bare `except:`
- Use logger in server code; avoid `print`

### Acceptance criteria
- App starts with `uvicorn backend.app:app --reload`
- `POST /api/recommend` returns at least one suggested algorithm for common
  prompts (classification/regression/clustering/time series)
- Usage endpoints respond and the HTML chart renders without extra setup
- Tests pass with `pytest -q`


