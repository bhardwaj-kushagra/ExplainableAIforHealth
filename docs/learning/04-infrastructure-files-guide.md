# Infrastructure Files Reference Guide

## Table of Contents
1. [requirements.txt](#requirementstxt)
2. [.gitignore](#gitignore)
3. [.dockerignore](#dockerignore)
4. [Dockerfile](#dockerfile)
5. [docker-compose.yml](#docker-composeyml)
6. [.github/workflows/](#githubworkflows)
7. [Makefile](#makefile)
8. [LICENSE](#license)
9. [Configuration Files](#configuration-files)
10. [Documentation Files](#documentation-files)

---

## requirements.txt

### Purpose
Lists all Python packages your project depends on.

### Why It Matters
```
Developer 1: Uses Python 3.11, XGBoost 2.0.3 → works fine
Developer 2: Uses Python 3.11, XGBoost 1.7.0 → breaks (API changed)

Solution: requirements.txt pins exact versions
→ Everyone uses same dependencies
→ Reproducible environment
```

### Our File Explained

```txt
# requirements.txt

# ============================================================================
# Data Science Stack
# ============================================================================
numpy>=1.24.0,<2.0.0
# Why? NumPy 2.0 has breaking changes
# >= allows bug fixes (1.24.1, 1.24.2)
# < prevents major version jump

pandas>=2.0.0
# DataFrames for data manipulation
# 2.0+ has performance improvements and better dtypes

scikit-learn>=1.4.0
# ML utilities: train_test_split, metrics, preprocessing
# 1.4+ has new scalers and improved consistency

# ============================================================================
# XGBoost and Explainability
# ============================================================================
xgboost==2.0.3
# Exact version pinned (==) because XGBoost API changes between versions
# 2.0.3 is latest stable at project time

shap>=0.45.0
# SHapley Additive exPlanations
# 0.45+ has better XGBoost integration

# ============================================================================
# DLNM (Distributed Lag Non-linear Models)
# ============================================================================
patsy>=0.5.0
# Formula interface: "admissions ~ cr(temp, df=4) + C(dow)"
# Required by DLNM for building design matrices

dlnm @ git+https://github.com/gasparrini/dlnmpy.git#egg=dlnm
# Install from GitHub (not on PyPI)
# Format: package @ git+URL#egg=package_name

# ============================================================================
# API Framework
# ============================================================================
fastapi>=0.115.0
# Modern API framework
# 0.115+ has latest security fixes

uvicorn[standard]>=0.32.0
# ASGI server to run FastAPI
# [standard]: includes uvloop, httptools (faster performance)

pydantic>=2.0.0
# Data validation
# 2.0 is complete rewrite (much faster than 1.x)

# ============================================================================
# Dashboard
# ============================================================================
streamlit>=1.38.0
# Interactive web apps
# 1.38+ has fragment support for better performance

plotly>=5.24.0
# Interactive plots
# 5.24+ has better Streamlit integration

folium>=0.18.0
# Interactive maps
# 0.18+ fixes leaflet.js compatibility

# ============================================================================
# Visualization
# ============================================================================
matplotlib>=3.9.0
# Static plots
# 3.9+ has improved defaults

seaborn>=0.13.0
# Statistical visualization
# 0.13+ has native Matplotlib 3.x support

# ============================================================================
# Data Serialization
# ============================================================================
joblib>=1.4.0
# Save/load models efficiently
# Better than pickle for NumPy arrays

# ============================================================================
# Testing
# ============================================================================
pytest>=8.3.0
# Testing framework
# 8.3+ has better error messages

pytest-cov>=6.0.0
# Coverage plugin for pytest
# 6.0+ supports latest pytest

# ============================================================================
# Development Tools (optional)
# ============================================================================
black>=24.0.0
# Code formatter
# 24.0+ is latest style

flake8>=7.1.0
# Linter
# 7.1+ supports Python 3.12

mypy>=1.13.0
# Type checker
# 1.13+ has better pydantic support
```

### Version Specifiers

```txt
package==1.0.0     # Exact version (most restrictive)
package>=1.0.0     # Minimum version
package<=1.0.0     # Maximum version
package>=1.0.0,<2.0.0  # Range
package~=1.0.0     # Compatible release (allows 1.0.1, 1.0.2, but not 1.1.0)
package            # Latest version (dangerous! not reproducible)
```

### Best Practices

**1. Pin Critical Dependencies**
```txt
# Pin if API changes between versions
xgboost==2.0.3  # API changed significantly from 1.x
pydantic>=2.0.0,<3.0.0  # 2.x is compatible, 3.x will have breaking changes
```

**2. Group Related Packages**
```txt
# Good: Organized by purpose
# Data Processing
pandas>=2.0.0
numpy>=1.24.0

# Bad: Random order
pandas>=2.0.0
fastapi>=0.115.0
numpy>=1.24.0
uvicorn>=0.32.0
```

**3. Document Why**
```txt
# Good
xgboost==2.0.3  # Exact version - API incompatible with 1.x

# Bad
xgboost==2.0.3
```

### Installing Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Upgrade all to latest compatible versions
pip install -U -r requirements.txt

# Install in editable mode (for development)
pip install -e .
```

### Generating requirements.txt

```bash
# From current environment (includes everything)
pip freeze > requirements.txt

# Better: Use pip-compile (only direct dependencies)
pip install pip-tools
pip-compile requirements.in -o requirements.txt

# Or: pipreqs (scans code for imports)
pip install pipreqs
pipreqs . --force
```

### requirements-dev.txt

```txt
# requirements-dev.txt
# Development-only dependencies

-r requirements.txt  # Include production dependencies

# Testing
pytest>=8.3.0
pytest-cov>=6.0.0
pytest-mock>=3.14.0

# Code Quality
black>=24.0.0
flake8>=7.1.0
mypy>=1.13.0
isort>=5.13.0

# Documentation
sphinx>=8.1.0
sphinx-rtd-theme>=3.0.0

# Debugging
ipdb>=0.13.0
ipython>=8.29.0
```

---

## .gitignore

### Purpose
Tells Git which files/folders to ignore (never commit).

### Why It Matters
```
# Without .gitignore
git add .  # Accidentally commits:
- .env (contains secrets!)
- __pycache__/ (Python cache, 100MB)
- node_modules/ (dependencies, 500MB)
- .vscode/ (personal IDE settings)
→ Large repo, security breach, conflicts

# With .gitignore
git add .  # Only commits source code
→ Clean repo, secure, fast
```

### Our File Explained

```gitignore
# ============================================================================
# Python
# ============================================================================
__pycache__/
# Why ignore? Python creates these automatically
# They're binary files, differ between Python versions
# Waste space in repo

*.py[cod]
# .pyc: compiled bytecode
# .pyo: optimized bytecode
# .pyd: Windows extension modules

*.so
# Linux shared libraries (compiled extensions)

*.egg
*.egg-info/
# Package metadata (generated during install)

dist/
build/
# Build artifacts from setuptools/pip

.Python
pip-log.txt
pip-delete-this-directory.txt

# ============================================================================
# Virtual Environments
# ============================================================================
.venv/
venv/
env/
ENV/
# Why ignore? Each developer has their own venv
# Dependencies listed in requirements.txt instead
# Can be 500MB+

# ============================================================================
# IDE / Editor
# ============================================================================
.vscode/
# VS Code settings (personal preferences)
# Exception: .vscode/settings.json with team settings can be committed

.idea/
# PyCharm settings

*.swp
*.swo
*~
# Vim temporary files

.DS_Store
# macOS folder metadata

Thumbs.db
# Windows thumbnail cache

# ============================================================================
# Project Specific
# ============================================================================
data_raw/
# Raw data (large, not needed in repo)
# Download separately or use DVC

outputs/*.joblib
outputs/*.pkl
# Trained models (large binary files)
# Store in model registry (MLflow, S3) instead

outputs/*.png
outputs/*.pdf
# Generated plots (can be regenerated)

logs/
*.log
# Log files (generated at runtime)

.coverage
htmlcov/
# Test coverage reports (regenerated each test run)

.pytest_cache/
# pytest cache

# ============================================================================
# Environment Variables
# ============================================================================
.env
.env.local
.env.*.local
# Contains secrets!
# DATABASE_URL=postgresql://user:password@host/db
# API_KEY=sk_live_secret123
# Never commit these!

# ============================================================================
# Documentation
# ============================================================================
docs/_build/
# Sphinx generated docs (can be rebuilt)

# ============================================================================
# Notebooks
# ============================================================================
.ipynb_checkpoints/
# Jupyter checkpoint files

# ============================================================================
# OS Files
# ============================================================================
*.bak
*.tmp
*.temp
# Backup and temporary files

# ============================================================================
# Docker
# ============================================================================
docker-compose.override.yml
# Local Docker overrides (personal settings)

# ============================================================================
# Large Files (if not using Git LFS)
# ============================================================================
*.csv
*.parquet
*.feather
# Data files (use DVC or download separately)

*.h5
*.hdf5
# HDF5 data files

*.db
*.sqlite
# Database files
```

### Global vs Local .gitignore

**Local (in repo)**:
```gitignore
# .gitignore
# Project-specific ignores
outputs/
data_raw/
```

**Global (in ~/.gitignore_global)**:
```bash
# Setup global gitignore
git config --global core.excludesfile ~/.gitignore_global

# ~/.gitignore_global
.DS_Store
.vscode/
.idea/
*.swp
```

### Checking What's Ignored

```bash
# Check if file is ignored
git check-ignore -v file.txt

# List all ignored files
git status --ignored

# Force add ignored file (if really needed)
git add -f file.txt
```

### Common Patterns

```gitignore
# Ignore all .log files
*.log

# But don't ignore important.log
!important.log

# Ignore folder but not its contents
folder/
!folder/.gitkeep

# Ignore all files in folder except one
folder/*
!folder/config.json

# Ignore by extension
*.tmp
*.bak
*.swp

# Ignore files starting with temp
temp*

# Ignore deeply nested files
**/cache/
```

---

## .dockerignore

### Purpose
Tells Docker which files to exclude when building images.

### Why It's Critical

```
# Without .dockerignore
Sending build context to Docker daemon: 2.5GB
→ Uploads .git/ (500MB), .venv/ (800MB), data_raw/ (1GB)
→ Build takes 5 minutes
→ Image is 2GB

# With .dockerignore
Sending build context to Docker daemon: 50MB
→ Only sends necessary files
→ Build takes 30 seconds
→ Image is 400MB
```

### Our File Explained

```dockerignore
# ============================================================================
# Version Control
# ============================================================================
.git/
.gitignore
.gitattributes
# Why ignore? Git history not needed in container
# Saves 100-500MB

# ============================================================================
# Python
# ============================================================================
__pycache__/
*.py[cod]
*.so
*.egg-info/
# Python cache not needed (regenerated in container)

.venv/
venv/
env/
# Virtual environment not needed (pip install in container instead)
# Saves 500MB+

# ============================================================================
# IDE / Editor
# ============================================================================
.vscode/
.idea/
*.swp
.DS_Store
Thumbs.db
# Personal settings, not needed in production

# ============================================================================
# Documentation
# ============================================================================
docs/
*.md
README.md
# Documentation not needed in container
# Exception: Some keep README for metadata

# ============================================================================
# Testing
# ============================================================================
tests/
.coverage
htmlcov/
.pytest_cache/
# Tests run in CI, not in production container

pytest.ini
.coveragerc
# Test configuration not needed

# ============================================================================
# CI/CD
# ============================================================================
.github/
.gitlab-ci.yml
.travis.yml
Jenkinsfile
# CI config not needed in container

# ============================================================================
# Large Data Files
# ============================================================================
data_raw/
*.csv
*.parquet
*.h5
# Large files should be downloaded at runtime or mounted as volumes
# Exception: If data is static and not too large, can include

# ============================================================================
# Model Artifacts (if large)
# ============================================================================
outputs/*.joblib
# If models > 100MB, download from S3/registry instead of baking into image
# Trade-off: Faster builds vs startup time

# ============================================================================
# Development Tools
# ============================================================================
Makefile
docker-compose.yml
docker-compose.override.yml
# Dev tools not needed in production container

# ============================================================================
# Logs and Temporary Files
# ============================================================================
logs/
*.log
*.tmp
*.bak
# Temporary files not needed

# ============================================================================
# Environment Files
# ============================================================================
.env
.env.*
# Secrets handled via environment variables at runtime

# ============================================================================
# Notebooks
# ============================================================================
notebooks/
*.ipynb
.ipynb_checkpoints/
# Exploratory notebooks not needed in production
```

### .dockerignore vs .gitignore

| File | Purpose | Why Different? |
|------|---------|----------------|
| `.gitignore` | Don't commit to Git | Includes dev files (IDE settings, logs) |
| `.dockerignore` | Don't send to Docker | Excludes more (tests, docs, even .git) |

**Example**:
```
# .gitignore (commit tests, but ignore logs)
*.log

# .dockerignore (exclude both tests and logs from image)
tests/
*.log
```

### Size Optimization Strategy

```dockerfile
# Bad: No .dockerignore
COPY . /app
# Copies 2GB including .git/, .venv/, data_raw/

# Good: With .dockerignore
COPY . /app
# Copies only 50MB of source code

# Better: Copy only what's needed
COPY requirements.txt /app/
COPY src/ /app/src/
COPY data_synthetic/ /app/data_synthetic/
# Explicit control, but more maintenance
```

---

## Dockerfile

### Purpose
Blueprint for building Docker images.

### Structure Overview

```dockerfile
# 1. Base Image
FROM python:3.11-slim

# 2. Metadata
LABEL maintainer="..."

# 3. System Dependencies
RUN apt-get update && apt-get install -y ...

# 4. Python Dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# 5. Application Code
COPY . /app

# 6. Configuration
EXPOSE 8000
ENV PYTHONUNBUFFERED=1

# 7. Startup Command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0"]
```

### Our Dockerfile Explained

```dockerfile
# ============================================================================
# Base Image
# ============================================================================
FROM python:3.11-slim

# Why python:3.11-slim?
# - python:3.11: 1GB (includes build tools, dev packages)
# - python:3.11-slim: 150MB (minimal Python, no compilers)
# - python:3.11-alpine: 50MB (lightest, but harder to build packages)
#
# Trade-off: slim is best balance of size vs compatibility

# ============================================================================
# Metadata (Optional but Professional)
# ============================================================================
LABEL maintainer="your-email@example.com"
LABEL version="1.0.0"
LABEL description="Climate-CVD Risk Prediction API"
LABEL org.opencontainers.image.source="https://github.com/user/repo"

# Used by:
# - Container registries (display info)
# - docker inspect (view metadata)
# - Monitoring tools (identify containers)

# ============================================================================
# Set Working Directory
# ============================================================================
WORKDIR /app

# All subsequent commands run in /app
# Benefits:
# - Cleaner commands (no /app prefix everywhere)
# - Standard location (everyone knows where code is)

# ============================================================================
# Install System Dependencies
# ============================================================================
RUN apt-get update && apt-get install -y \
    gcc g++ \
    # C/C++ compilers for building Python packages (NumPy, pandas)
    libgdal-dev \
    # GDAL: Geospatial Data Abstraction Library (for folium maps)
    libgeos-dev \
    # GEOS: Geometry Engine (for shapely, folium)
    libproj-dev \
    # PROJ: Cartographic projections (for coordinate systems)
    curl \
    # For health checks
    && rm -rf /var/lib/apt/lists/*
    # Delete apt cache (saves 50MB)

# Why chain with &&?
# Each RUN creates a new layer
# Chaining = one layer = smaller image
#
# Bad (3 layers):
# RUN apt-get update
# RUN apt-get install gcc
# RUN rm -rf /var/lib/apt/lists/*
#
# Good (1 layer):
# RUN apt-get update && apt-get install gcc && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Python Dependencies (Separate for Caching)
# ============================================================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Why separate from COPY . /app?
# Docker layer caching:
# 1. If requirements.txt unchanged → reuse cached layer (fast!)
# 2. If only code changed → reuse pip install layer
#
# Order matters:
# requirements.txt (changes rarely) → cached
# source code (changes often) → not cached

# --no-cache-dir: Don't keep pip cache (saves 100MB)

# ============================================================================
# Copy Application Code
# ============================================================================
COPY . /app

# Copies everything except .dockerignore items

# ============================================================================
# Generate Data (Build-time vs Runtime)
# ============================================================================
RUN python data_synthetic/generate_synthetic.py && \
    python src/preprocess.py

# Pros:
# - Faster container startup (data ready)
# - Consistent data (same across containers)
#
# Cons:
# - Larger image (data baked in)
# - Rebuild required to update data
#
# Alternative (runtime):
# CMD ["sh", "-c", "python data_synthetic/generate_synthetic.py && uvicorn ..."]

# ============================================================================
# Expose Ports (Documentation Only)
# ============================================================================
EXPOSE 8000 8501

# 8000: FastAPI
# 8501: Streamlit
#
# NOTE: This doesn't actually open ports!
# It's documentation for developers
# Actual port mapping: docker run -p 8000:8000

# ============================================================================
# Environment Variables
# ============================================================================
ENV PYTHONUNBUFFERED=1
# Don't buffer stdout/stderr (see logs immediately)

ENV PYTHONDONTWRITEBYTECODE=1
# Don't create .pyc files (smaller image)

ENV MODEL_PATH=/app/outputs/xgb_model.joblib
# Default model path (can override at runtime)

# ============================================================================
# Health Check
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Docker monitors container health:
# - interval=30s: Check every 30 seconds
# - timeout=10s: Health check must complete in 10s
# - start-period=40s: Grace period for app startup
# - retries=3: Unhealthy after 3 failures
#
# Status: healthy, unhealthy, starting
# docker ps shows status
# Orchestrators (Kubernetes) can restart unhealthy containers

# ============================================================================
# User (Security Best Practice)
# ============================================================================
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

# Why not run as root?
# - Security: If container compromised, attacker has limited privileges
# - Best practice: Principle of least privilege
#
# Creates user 'appuser' with no password
# Changes ownership of /app to appuser
# Switches to appuser (all subsequent commands run as appuser)

# ============================================================================
# Startup Command
# ============================================================================
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# CMD vs ENTRYPOINT:
# - CMD: Can be overridden (docker run myimage python script.py)
# - ENTRYPOINT: Always runs (docker run myimage adds arguments)
#
# --host 0.0.0.0: Listen on all interfaces (not just localhost)
# Why? Container network isolation - must bind to 0.0.0.0 to be reachable

# Alternative for multiple services (use docker-compose instead):
# CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 & streamlit run src/dashboard/app.py"]
```

### Multi-Stage Builds (Advanced)

```dockerfile
# Stage 1: Builder (large, has compilers)
FROM python:3.11 AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime (small, just Python)
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local  # Copy installed packages
COPY . /app

ENV PATH=/root/.local/bin:$PATH

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0"]

# Result: Image is 200MB instead of 1GB
# Builder artifacts discarded
```

### Build Arguments

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ARG MODEL_VERSION=v1.0.0
ENV MODEL_VERSION=${MODEL_VERSION}

# Build with custom args
# docker build --build-arg PYTHON_VERSION=3.10 --build-arg MODEL_VERSION=v2.0.0 .
```

---

## docker-compose.yml

### Purpose
Define and run multi-container applications.

### Why Use It?

```bash
# Without docker-compose (manual)
docker network create cvd-network
docker run -d --name db --network cvd-network postgres:15
docker run -d --name api --network cvd-network -p 8000:8000 cvd-api
docker run -d --name dashboard --network cvd-network -p 8501:8501 cvd-dashboard

# With docker-compose (one command)
docker-compose up
```

### Our File Explained

```yaml
# ============================================================================
# Version
# ============================================================================
version: '3.8'

# Compose file format version
# 3.8 is latest for Compose v1
# Newer Docker Compose (v2) doesn't require version

# ============================================================================
# Services (Containers)
# ============================================================================
services:
  # --------------------------------------------------------------------------
  # API Service
  # --------------------------------------------------------------------------
  api:
    # Build from Dockerfile in current directory
    build:
      context: .
      dockerfile: Dockerfile
      # Alternative: Use pre-built image
      # image: myregistry.com/cvd-api:v1.0.0
    
    # Container name (easier to reference)
    container_name: cvd-api
    
    # Port mapping (host:container)
    ports:
      - "8000:8000"
    # Access at http://localhost:8000
    
    # Environment variables
    environment:
      - DATABASE_URL=postgresql://cvduser:cvdpass@db:5432/cvddb
      - LOG_LEVEL=INFO
      - MODEL_PATH=/app/outputs/xgb_model.joblib
    
    # Or load from .env file
    env_file:
      - .env
    
    # Dependencies (start order)
    depends_on:
      - db
    # Starts db before api
    # NOTE: Doesn't wait for db to be ready, just started
    
    # Volumes (persist data, share files)
    volumes:
      - ./outputs:/app/outputs
      # Host ./outputs maps to container /app/outputs
      # Changes in either location reflected in both
      
      - model-cache:/app/cache
      # Named volume (managed by Docker)
    
    # Restart policy
    restart: unless-stopped
    # - no: Never restart
    # - always: Always restart
    # - on-failure: Restart if exit code != 0
    # - unless-stopped: Restart unless manually stopped
    
    # Health check (override Dockerfile HEALTHCHECK)
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'    # Max 2 CPUs
          memory: 4G     # Max 4GB RAM
        reservations:
          cpus: '1.0'    # Reserve 1 CPU
          memory: 2G     # Reserve 2GB RAM
    
    # Network
    networks:
      - cvd-network
  
  # --------------------------------------------------------------------------
  # Dashboard Service
  # --------------------------------------------------------------------------
  dashboard:
    build: .
    container_name: cvd-dashboard
    
    # Override CMD from Dockerfile
    command: streamlit run src/dashboard/app.py --server.port=8501
    
    ports:
      - "8501:8501"
    
    depends_on:
      - api
    
    environment:
      - API_URL=http://api:8000
      # Use service name 'api', not 'localhost'
      # Docker DNS resolves service names
    
    restart: unless-stopped
    
    networks:
      - cvd-network
  
  # --------------------------------------------------------------------------
  # Database Service
  # --------------------------------------------------------------------------
  db:
    # Use official PostgreSQL image
    image: postgres:15
    
    container_name: cvd-db
    
    # No port mapping (only accessible from other containers)
    # Uncomment to access from host:
    # ports:
    #   - "5432:5432"
    
    environment:
      - POSTGRES_DB=cvddb
      - POSTGRES_USER=cvduser
      - POSTGRES_PASSWORD=cvdpass
      # In production, use secrets:
      # POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    
    volumes:
      - postgres-data:/var/lib/postgresql/data
      # Persist database (survives container restart)
      
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      # Run SQL on first startup
    
    restart: unless-stopped
    
    networks:
      - cvd-network
  
  # --------------------------------------------------------------------------
  # Redis (Caching)
  # --------------------------------------------------------------------------
  redis:
    image: redis:7-alpine
    container_name: cvd-redis
    
    command: redis-server --appendonly yes
    # Enable persistence
    
    volumes:
      - redis-data:/data
    
    restart: unless-stopped
    
    networks:
      - cvd-network
  
  # --------------------------------------------------------------------------
  # Nginx (Reverse Proxy)
  # --------------------------------------------------------------------------
  nginx:
    image: nginx:alpine
    container_name: cvd-nginx
    
    ports:
      - "80:80"      # HTTP
      - "443:443"    # HTTPS
    
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      # Mount config (read-only)
      
      - ./ssl:/etc/nginx/ssl:ro
      # SSL certificates
    
    depends_on:
      - api
      - dashboard
    
    restart: unless-stopped
    
    networks:
      - cvd-network

# ============================================================================
# Volumes (Named)
# ============================================================================
volumes:
  postgres-data:
    # Managed by Docker
    # Location: /var/lib/docker/volumes/postgres-data
    
  redis-data:
    # Separate volume for Redis
    
  model-cache:
    # Shared cache for models

# ============================================================================
# Networks
# ============================================================================
networks:
  cvd-network:
    driver: bridge
    # Default driver, containers can communicate by name
```

### Common Commands

```bash
# Start all services
docker-compose up

# Start in background (detached)
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild images
docker-compose build

# View logs
docker-compose logs -f api

# Execute command in service
docker-compose exec api python src/models/xgb_train.py

# Scale service (multiple containers)
docker-compose up --scale api=3

# View status
docker-compose ps

# Restart service
docker-compose restart api
```

### Environment Variables

**Option 1: .env file**
```bash
# .env
DATABASE_URL=postgresql://user:pass@db:5432/cvddb
API_KEY=secret123
LOG_LEVEL=INFO
```

```yaml
# docker-compose.yml
services:
  api:
    env_file:
      - .env
```

**Option 2: Environment section**
```yaml
services:
  api:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/cvddb
      - API_KEY=secret123
```

**Option 3: Variable substitution**
```yaml
services:
  api:
    environment:
      - DATABASE_URL=${DATABASE_URL}  # From host environment
```

### Development vs Production

**docker-compose.override.yml** (for development):
```yaml
# Automatically loaded with docker-compose.yml

services:
  api:
    volumes:
      - .:/app  # Live code reload
    environment:
      - DEBUG=true
    command: uvicorn src.api.main:app --reload
```

**docker-compose.prod.yml** (for production):
```yaml
# Load with: docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

services:
  api:
    image: myregistry.com/cvd-api:v1.0.0  # Use pre-built image
    restart: always
    deploy:
      replicas: 3  # Multiple instances
```

---

## .github/workflows/

### Purpose
GitHub Actions workflow definitions (CI/CD).

### File Structure

```
.github/
└── workflows/
    ├── ci.yml              # Main CI pipeline
    ├── deploy.yml          # Deployment pipeline
    └── cron-tests.yml      # Scheduled tests
```

### ci.yml Explained

```yaml
# ============================================================================
# Workflow Name
# ============================================================================
name: CI

# Shows in GitHub Actions UI
# Badge: ![CI](https://github.com/user/repo/actions/workflows/ci.yml/badge.svg)

# ============================================================================
# Triggers
# ============================================================================
on:
  push:
    branches:
      - main
      - develop
    paths-ignore:
      - 'docs/**'
      - '**.md'
    # Ignore docs-only changes
  
  pull_request:
    branches:
      - main
  
  schedule:
    - cron: '0 0 * * 0'  # Weekly (Sunday midnight UTC)
  
  workflow_dispatch:
    # Manual trigger (button in GitHub UI)

# ============================================================================
# Concurrency (Cancel Previous Runs)
# ============================================================================
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# If new push while workflow running → cancel old run
# Saves CI minutes

# ============================================================================
# Jobs
# ============================================================================
jobs:
  # --------------------------------------------------------------------------
  # Lint Job
  # --------------------------------------------------------------------------
  lint:
    name: Lint Code
    runs-on: ubuntu-latest  # GitHub-hosted runner (free)
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        # Downloads repo code
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install linters
        run: |
          pip install flake8 black mypy
      
      - name: Lint with flake8
        run: |
          flake8 src/ tests/ --max-line-length=100
      
      - name: Check formatting with black
        run: |
          black src/ tests/ --check --diff
      
      - name: Type check with mypy
        run: |
          mypy src/ --ignore-missing-imports
  
  # --------------------------------------------------------------------------
  # Test Job (Matrix Strategy)
  # --------------------------------------------------------------------------
  test:
    name: Test (Python ${{ matrix.python-version }}, OS ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
        os: [ubuntu-latest, windows-latest, macos-latest]
        exclude:
          - os: macos-latest
            python-version: '3.10'
      fail-fast: false
      # Continue other matrix jobs if one fails
    
    # Matrix creates 8 parallel jobs:
    # - ubuntu + 3.10, 3.11, 3.12
    # - windows + 3.10, 3.11, 3.12
    # - macos + 3.11, 3.12 (3.10 excluded)
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
        # Caches pip packages (faster subsequent runs)
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Generate data
        run: python data_synthetic/generate_synthetic.py
      
      - name: Run preprocessing
        run: python src/preprocess.py
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=src --cov-report=xml --cov-report=term
      
      - name: Upload coverage
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          fail_ci_if_error: true
        # Only upload coverage once (not from all matrix jobs)
  
  # --------------------------------------------------------------------------
  # Docker Build Job
  # --------------------------------------------------------------------------
  docker:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, test]  # Only run if lint and test pass
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
        # Enables advanced Docker features (caching, multi-platform)
      
      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-${{ github.sha }}
          restore-keys: |
            ${{ runner.os }}-buildx-
      
      - name: Build Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: false  # Don't push yet
          tags: cvd-api:${{ github.sha }}
          cache-from: type=local,src=/tmp/.buildx-cache
          cache-to: type=local,dest=/tmp/.buildx-cache-new
      
      - name: Test Docker image
        run: |
          docker run --rm cvd-api:${{ github.sha }} python --version
          docker run --rm cvd-api:${{ github.sha }} pytest tests/ -v
      
      - name: Log in to Docker Hub
        if: github.ref == 'refs/heads/main'
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}
      
      - name: Push to Docker Hub
        if: github.ref == 'refs/heads/main'
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            username/cvd-api:latest
            username/cvd-api:${{ github.sha }}
            username/cvd-api:v1.0.${{ github.run_number }}
      
      # Move cache to prevent unbounded growth
      - name: Move cache
        run: |
          rm -rf /tmp/.buildx-cache
          mv /tmp/.buildx-cache-new /tmp/.buildx-cache

# ============================================================================
# Workflow Complete Notification
# ============================================================================
# (Separate job that always runs)
  notify:
    name: Notify
    runs-on: ubuntu-latest
    needs: [lint, test, docker]
    if: always()
    
    steps:
      - name: Send Slack notification
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "CI failed for ${{ github.repository }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": ":x: CI failed for *${{ github.repository }}*\nCommit: ${{ github.sha }}\nActor: ${{ github.actor }}"
                  }
                }
              ]
            }
```

### Secrets Configuration

1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Add secrets:
   - `DOCKER_USERNAME`
   - `DOCKER_TOKEN`
   - `SLACK_WEBHOOK`
   - `AWS_ACCESS_KEY_ID`
   - etc.

3. Use in workflow:
```yaml
- name: Deploy
  env:
    API_KEY: ${{ secrets.API_KEY }}
  run: deploy_script.sh
```

---

## Summary

### Key Configuration Files

| File | Purpose | Key Principles |
|------|---------|----------------|
| `requirements.txt` | Python dependencies | Pin versions, group by purpose, document why |
| `.gitignore` | Exclude from Git | Secrets, cache, IDE, generated files |
| `.dockerignore` | Exclude from Docker | More aggressive than .gitignore (size matters) |
| `Dockerfile` | Build instructions | Layer caching, multi-stage, security (non-root user) |
| `docker-compose.yml` | Multi-container apps | Service dependencies, volumes, networks |
| `.github/workflows/` | CI/CD pipelines | Matrix tests, Docker build, secrets management |

### Best Practices

**requirements.txt**:
- ✅ Pin critical packages with `==`
- ✅ Use ranges for stable packages `>=1.0,<2.0`
- ✅ Group and comment
- ❌ Don't use `package` (unpinned)

**Dockerfiles**:
- ✅ Use slim base images
- ✅ Copy requirements.txt separately (caching)
- ✅ Chain RUN commands with `&&`
- ✅ Use non-root user
- ✅ HEALTHCHECK for monitoring
- ❌ Don't run as root
- ❌ Don't include secrets

**docker-compose.yml**:
- ✅ Use named volumes for persistence
- ✅ depends_on for startup order
- ✅ restart policies
- ✅ Resource limits in production
- ❌ Don't expose internal services

**CI/CD**:
- ✅ Lint before tests (fail fast)
- ✅ Matrix strategy for compatibility
- ✅ Cache dependencies
- ✅ Store secrets properly
- ❌ Don't hardcode credentials

---

**Next**: Read `05-technical-architecture.md` for system design and component interactions

