# Project Rules (Runtime and Workflow)

- Runtime defaults:
  - In-memory repository by default; MongoDB optional via `repositories.py`
  - Keep API minimal and stable
- API surface:
  - `POST /api/recommend` – returns suggested algorithms for a prompt
  - `GET /api/reports/usage` and `/api/reports/usage.html`
  - `GET /metrics` (optional; keep current behavior if present)
- Frontend:
  - Minimal chart at `frontend/index.html` rendering `/api/reports/usage`
- Tests:
  - Keep unit-ish API, E2E, metrics, and Docker tests passing (`pytest -q`)
- Git workflow:
  - Default branch `main`; feature branches → PR → merge
  - `.gitignore` must exclude caches, venvs, Office docs, archives, bytecode
- Style reference:
  - Follow `CODE_STYLE.md` for formatting and naming
  - Use type hints for public functions and return values
  - No bare `except:`; avoid mutable defaults
