AI Algorithm Teacher

A small, rules-based FastAPI service that recommends AI/ML algorithms from a
natural-language description. The simplified default uses in-memory storage and
keeps the surface area minimal.

## Quickstart

### Start FastAPI Server

```bash
python -m pip install -r requirements.txt
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: http://localhost:8000

### Try a Recommendation

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Classify reviews by sentiment"}'
```

## API Endpoints

### Recommendations
- `POST /api/recommend` - Get algorithm recommendations for a prompt

### Reports
- `GET /api/reports` - Reports and monitoring index (HTML)
- `GET /api/reports/index.json` - Reports index (JSON)
- `GET /api/reports/usage` - Usage statistics (JSON)
- `GET /api/reports/usage.html` - Usage chart (HTML)
- `GET /api/reports/details` - Detailed report by algorithm (JSON)
- `GET /api/reports/details.html` - Detailed report (HTML)

### Monitoring
- `GET /api/monitoring` - Monitoring endpoints index (JSON)
- `GET /metrics` - Prometheus metrics (plain text)
- `GET /metrics.html` - Prometheus metrics (HTML table)

### Tests
- `GET /api/tests` - Test endpoints index (JSON)
- `POST /api/tests/run` - Run all tests
- `GET /api/tests/run` - Run all tests (GET method)
- `POST /api/tests/unit` - Run unit tests only
- `GET /api/tests/unit` - Run unit tests (GET method)
- `POST /api/tests/pipeline` - Run e2e pipeline test
- `GET /api/tests/pipeline` - Run pipeline test (GET method)

### Cleanup
- `POST /api/cleanup/images?age_minutes=30` - Clean up old Docker images
- `GET /api/cleanup/images?age_minutes=30` - Clean up images (GET method)

### Documentation
- `GET /` - Home page with endpoint listing
- `GET /api` - API index (HTML)
- `GET /index.json` - All endpoints (JSON)
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

## Environment configuration

Create a `.env` (or export env vars) to control runtime:

```
# Default: in-memory repositories (no external DB needed)
USE_IN_MEMORY=1

# To enable MongoDB instead, set:
# USE_IN_MEMORY=0
# MONGODB_URI=mongodb://localhost:27017
# MONGODB_DB=ai_algo_teacher

# Optional logging level (default INFO)
# LOG_LEVEL=INFO
```

## Minimal Stack
- Python 3.11, FastAPI, Uvicorn
- In-memory repository by default
- Optional: MongoDB and Prometheus metrics are supported but not required

## Project Structure (key paths)
```
backend/
  app.py            # FastAPI app and router mounting
  services.py       # Recommendation rules
  repositories.py   # In-memory + optional Mongo
  routers/          # index, recommendations, reports
frontend/
  index.html        # Minimal usage chart
tests/
  test_api.py, test_e2e.py, test_metrics.py, test_docker.py
ai_algorithm_teacher.py  # CLI
```

## Docker (optional)
```
docker build -t algorithm-teacher .
docker run --name algorithm-teacher -p 8000:8000 algorithm-teacher
```

## Tests
```
python -m pip install -r requirements.txt
pytest -q
```

## Conventions
- PEP 8, UTF-8, 4-space indent, line length ≤ 79
- Imports: stdlib → third-party → local, one per line
- Type hints for public functions, no bare `except:`

## Notes
- Transparent, rules-based guidance; not AutoML


