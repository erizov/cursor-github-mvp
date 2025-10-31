AI Algorithm Teacher

A small, rules-based FastAPI service that recommends AI/ML algorithms from a
natural-language description. The simplified default uses in-memory storage and
keeps the surface area minimal.

## Quickstart

```
python -m pip install -r requirements.txt
uvicorn backend.app:app --reload
```

Try a recommendation:

```
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Classify reviews by sentiment"}'
```

Open usage chart (HTML): http://localhost:8000/api/reports/usage.html

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


