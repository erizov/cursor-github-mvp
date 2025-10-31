# Code Style and Conventions

This project follows a strict, readable Python style aligned with PEP 8.
Use this document as the single source of truth for coding rules.

## Formatting
- Encoding: UTF-8
- Indentation: 4 spaces (no tabs)
- Max line length: 79 characters
- Two blank lines between top-level declarations (functions/classes)
- One blank line between methods inside classes
- Imports at top of file, grouped and ordered:
  1) Standard library
  2) Third-party packages
  3) Local application imports
  Use one import per line.

## Naming
- Modules, functions, variables: snake_case
- Classes, exceptions: CapWords (PascalCase)
- Constants: UPPER_SNAKE_CASE
- Private/internal: leading underscore (e.g., _internal_helper)

## Spacing and Operators
- One space around binary operators (a + b, x == y)
- No extra spaces inside parentheses/brackets/braces
- Slices may use symmetric spacing (a[start : end])

## Booleans and Comparisons
- Compare with None using `is` / `is not`
- Check emptiness with `if items:` rather than `len(items) > 0`
- Prefer clear guard clauses over deep nesting

## Exceptions
- Never use bare `except:` — catch specific exceptions
- Avoid mutable default arguments (use None and initialize inside)

## Comments and Docstrings
- Explain why, not just what
- Docstrings follow PEP 257:
  - Triple quotes
  - One-line summary; for multi-line, include a blank line after summary
- Keep comments concise and high-signal; avoid obvious comments

## Type Hints
- Provide type hints for public functions/methods and return values
- Avoid `Any` where possible; prefer precise types

## Logging
- Use a logger in server/backend code (no `print`)
- Ensure logs are structured and informative (see `logging_config.py`)

## Project Architecture
- Default repository: in-memory; MongoDB is optional via `repositories.py`
- Public API surface (minimal):
  - `POST /api/recommend`
  - `GET /api/reports/usage` and `GET /api/reports/usage.html`
  - `GET /metrics` (optional)
- Keep HTML/JS UI minimal (`frontend/index.html`)

## Testing
- Keep tests deterministic and fast (`pytest -q`)
- Cover new feature branches with unit/e2e tests where appropriate

## Git Workflow
- Default branch: `main`
- Create feature branches; open PRs into `main`
- Keep `.gitignore` entries for caches, venvs, Office docs, archives, bytecode

## Style Enforcement
- Run tools in a clean venv when possible
- Fix linter/type checker findings before merging
