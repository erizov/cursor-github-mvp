# Deployment folder

This directory contains Dockerfiles and helper scripts for building and running
AI Algorithm Teacher.

## Files

- `Dockerfile` – production image (uvicorn, port 8000)
- `Dockerfile.dev` – development image with `--reload`
- `build.sh` – Linux/macOS build helper
- `build.ps1` – Windows PowerShell build helper

## Build

```bash
# Prod image
docker build -f deployment/Dockerfile -t algorithm-teacher:prod .

# Dev image
docker build -f deployment/Dockerfile.dev -t algorithm-teacher:dev .
```

## Run

```bash
# Prod
docker run --rm -p 8000:8000 algorithm-teacher:prod

# Dev (mount source for live reload if desired)
# docker run --rm -p 8000:8000 -v "$PWD/backend:/app/backend" algorithm-teacher:dev
```
