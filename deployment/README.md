# Deployment folder

This directory contains Dockerfiles and helper scripts for building and running
AI Algorithm Teacher with different backend options.

## Files

- `Dockerfile` / `Dockerfile.inmemory` – in-memory backend (default)
- `Dockerfile.mongodb` – MongoDB backend
- `Dockerfile.postgres` – PostgreSQL backend
- `Dockerfile.redis` – Redis backend
- `Dockerfile.sqlite` – SQLite backend
- `Dockerfile.memcached` – Memcached backend
- `Dockerfile.neo4j` – Neo4j backend
- `Dockerfile.cassandra` – **Cassandra backend (includes build tools for C extensions)**
- `Dockerfile.dev` – development image with `--reload`

## Backend Selection

Set the `BACKEND_TYPE` environment variable to switch between backends:
- `inmemory` (default)
- `mongodb`
- `postgres`
- `redis`
- `sqlite`
- `memcached`
- `neo4j`
- `cassandra`

## Cassandra Backend

**Important:** The Cassandra Python driver requires C extensions. The `Dockerfile.cassandra` uses the full `python:3.11` image (not slim) and includes build dependencies (`gcc`, `g++`, `libev-dev`) to compile the driver during the Docker build.

### Option 1: Use Docker (Recommended)

Docker automatically builds the C extensions during image creation:

```bash
# Start Cassandra database
docker-compose up -d cassandra

# Build and run with Cassandra backend
docker build -f deployment/Dockerfile.cassandra -t alg-teach-cassandra .
docker run --rm -p 8000:8000 \
  --network alg-teach_default \
  -e BACKEND_TYPE=cassandra \
  -e CASSANDRA_HOSTS=cassandra \
  alg-teach-cassandra
```

### Option 2: Local Development (Windows)

Install Visual Studio Build Tools:
1. Download from: https://visualstudio.microsoft.com/downloads/
2. Install "Desktop development with C++" workload
3. Install Python packages: `pip install cassandra-driver`

### Option 3: Local Development (Linux/macOS)

Install build tools:
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y build-essential libev-dev pkg-config

# macOS
brew install libev

# Then install Python package
pip install cassandra-driver
```

## Build

```bash
# In-memory backend (default)
docker build -f deployment/Dockerfile.inmemory -t alg-teach:inmemory .

# MongoDB backend
docker build -f deployment/Dockerfile.mongodb -t alg-teach:mongodb .

# PostgreSQL backend
docker build -f deployment/Dockerfile.postgres -t alg-teach:postgres .

# Cassandra backend (includes C extension build tools)
docker build -f deployment/Dockerfile.cassandra -t alg-teach:cassandra .
```

## Run

```bash
# With docker-compose (starts database + app)
docker-compose up -d

# Or run app container manually (ensure database is running)
docker run --rm -p 8000:8000 \
  --network alg-teach_default \
  -e BACKEND_TYPE=mongodb \
  -e MONGODB_URI=mongodb://mongo:27017 \
  alg-teach:mongodb
```
