@echo off
REM Start FastAPI server with in-memory backend
set BACKEND_TYPE=inmemory
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000


