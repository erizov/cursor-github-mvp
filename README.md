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
│  └─ test_metrics.py
├─ ai_algorithm_teacher.py
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

### Frontend Report UI

- Open `frontend/index.html` (loads React via CDN) and it will call `GET /api/reports/usage` to render colored usage bars.

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
  - Metrics endpoint availability test for `GET /metrics`
  - E2E test posting multiple prompts then verifying usage totals

## Logs

- Structured JSON logging via structlog.
- Configure level with env: `LOG_LEVEL=DEBUG` (default INFO).
- Request logs include method, path, status, client; prompts are not logged (only length) to reduce PII risk.

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

## Notes

- Transparent, rules-based engine for education and quick guidance; not a full AutoML system.


