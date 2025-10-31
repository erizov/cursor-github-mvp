Project rules (coding + workflow)

- Coding style: PEP 8, UTF‑8, 4 spaces, line length ≤ 79
- Imports: stdlib → third‑party → local; one per line
- Naming: snake_case (modules/functions/vars), CapWords (classes), UPPER_SNAKE_CASE (constants), private with leading underscore
- Type hints: required for public functions/methods and return values
- Comparisons: use is/is not for None; check emptiness with if items:
- Exceptions: no bare except:; avoid mutable defaults; prefer guard clauses
- Logging: use a logger in server code; avoid print
- Comments/docstrings: explain why; PEP 257 for docstrings

- Default runtime: in‑memory repository; MongoDB optional via repositories.py
- API: POST /api/recommend; GET /api/reports/usage(.html); GET /metrics (optional)
- Frontend: minimal chart in frontend/index.html
- Tests: keep unit-ish API, e2e, metrics, Docker tests passing (pytest -q)

- Git: default branch main; feature branches → PR → merge
- Ignore: caches, venvs, Office docs, archives (*.zip), bytecode/__pycache__

See CODE_STYLE.md for the authoritative style guide. See README.md, readme_detailed.md, and cursor_prompt.md for usage and acceptance criteria.