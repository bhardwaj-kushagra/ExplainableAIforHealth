# Professional Features Guide - Beyond Basic Coding

## Table of Contents
1. [API Health Checks](#api-health-checks)
2. [Request/Response Handling](#requestresponse-handling)
3. [Testing Frameworks](#testing-frameworks)
4. [Docker Containerization](#docker-containerization)
5. [CI/CD Pipelines](#cicd-pipelines)
6. [Logging and Monitoring](#logging-and-monitoring)
7. [Error Handling](#error-handling)
8. [Documentation Standards](#documentation-standards)
9. [Security Practices](#security-practices)
10. [Performance Optimization](#performance-optimization)

---

## API Health Checks

### What is a Health Check?
A simple endpoint that tells you if your API is alive and functional.

### Why It Matters
```
Load Balancer: "Is server 1 working?"
Server 1 Health Check: "Yes, all systems operational"

Load Balancer: "Is server 2 working?"
Server 2 Health Check: [no response]
Load Balancer: "Server 2 is down, route traffic to Server 1"
```

### Basic Implementation
```python
# src/api/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    """
    Simplest health check - just returns 200 OK
    """
    return {"status": "ok"}
```

### Professional Health Check
```python
from fastapi import FastAPI, status
from pydantic import BaseModel
import psutil  # For system metrics
from datetime import datetime

class HealthResponse(BaseModel):
    status: str  # "ok", "degraded", "error"
    timestamp: datetime
    version: str
    model_loaded: bool
    model_metrics: dict
    system: dict

@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Comprehensive health check with diagnostics
    
    Returns:
    - status: Overall system health
    - model_loaded: Is ML model in memory?
    - model_metrics: Performance metrics (R², MAE)
    - system: CPU, memory, disk usage
    """
    # Check if model is loaded
    model_ok = model is not None
    
    # Get system metrics
    system_info = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    # Determine overall status
    if not model_ok:
        overall_status = "error"
    elif system_info["cpu_percent"] > 90 or system_info["memory_percent"] > 90:
        overall_status = "degraded"
    else:
        overall_status = "ok"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version="1.0.0",
        model_loaded=model_ok,
        model_metrics={
            "test_r2": 0.903,
            "test_mae": 0.897
        } if model_ok else {},
        system=system_info
    )
```

### Health Check Best Practices

**1. Different Levels of Health Checks**
```python
# Liveness: "Is the app running?" (for container restart)
@app.get("/health/live")
def liveness():
    return {"status": "alive"}

# Readiness: "Is the app ready to serve traffic?" (for load balancing)
@app.get("/health/ready")
def readiness():
    if model is None:
        return {"status": "not_ready"}, 503
    return {"status": "ready"}

# Startup: "Has initialization completed?" (for Kubernetes)
@app.get("/health/startup")
def startup():
    if not artifacts_loaded:
        return {"status": "starting"}, 503
    return {"status": "started"}
```

**2. Include Dependencies**
```python
@app.get("/health")
def health_check():
    checks = {
        "model": model is not None,
        "database": check_db_connection(),
        "redis": check_redis_connection(),
        "disk_space": psutil.disk_usage('/').percent < 90
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ok" if all_healthy else "degraded",
        "checks": checks
    }

def check_db_connection():
    try:
        # Simple query
        db.execute("SELECT 1")
        return True
    except Exception:
        return False
```

**3. Don't Be Too Honest (Security)**
```python
# BAD: Exposes internal details
@app.get("/health")
def health_check():
    return {
        "database_host": "db.internal.company.com",  # ❌ Leaks infrastructure
        "database_password": "***",  # ❌ Even masked, hints at DB
        "model_path": "/opt/app/models/xgb_v1.joblib"  # ❌ Reveals file structure
    }

# GOOD: Minimal necessary info
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "model_loaded": True
    }
```

### Monitoring with Health Checks

**Prometheus Integration**
```python
from prometheus_client import Counter, Gauge, generate_latest

# Metrics
health_check_counter = Counter('health_check_requests_total', 'Total health check requests')
model_loaded_gauge = Gauge('model_loaded', 'Is model loaded? (1=yes, 0=no)')

@app.get("/health")
def health_check():
    health_check_counter.inc()  # Increment counter
    model_loaded_gauge.set(1 if model is not None else 0)  # Update gauge
    
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    """Prometheus scrapes this endpoint"""
    return generate_latest()
```

**External Monitoring**
```bash
# Uptime monitoring (checks every 30 seconds)
curl -f http://api.example.com/health || alert "API is down!"

# Kubernetes liveness probe (in deployment.yaml)
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3  # Restart pod after 3 failures
```

---

## Request/Response Handling

### Using curl for API Testing

**Basic GET Request**
```bash
# Simple GET
curl http://localhost:8000/health

# Verbose output (see headers)
curl -v http://localhost:8000/health

# Save response to file
curl http://localhost:8000/health -o response.json
```

**POST Requests with JSON**
```bash
# Basic POST with data
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"temp_mean_c": 28.5, "humidity": 65}'

# POST with data from file
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @forecast_data.json

# PowerShell equivalent
Invoke-RestMethod -Uri "http://localhost:8000/predict" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"temp_mean_c": 28.5}'
```

**Advanced curl Options**
```bash
# Include response headers in output
curl -i http://localhost:8000/health

# Follow redirects
curl -L http://example.com/redirect

# Set custom headers
curl -H "Authorization: Bearer token123" \
     -H "User-Agent: MyApp/1.0" \
     http://api.example.com/data

# HTTP/2
curl --http2 https://api.example.com

# Measure timing
curl -w "Time: %{time_total}s\n" -o /dev/null -s http://localhost:8000/health
```

### Pydantic for Request Validation

**Why Pydantic?**
```python
# Without Pydantic (manual validation nightmare)
@app.post("/predict")
def predict(request: dict):
    # Manual validation
    if 'temp_mean_c' not in request:
        return {"error": "temp_mean_c is required"}, 400
    
    try:
        temp = float(request['temp_mean_c'])
    except (ValueError, TypeError):
        return {"error": "temp_mean_c must be a number"}, 400
    
    if temp < -50 or temp > 60:
        return {"error": "temp_mean_c out of range"}, 400
    
    # ... repeat for 10 more fields ...

# With Pydantic (automatic validation)
from pydantic import BaseModel, Field

class PredictRequest(BaseModel):
    temp_mean_c: float = Field(..., ge=-50, le=60)  # All validation in one line!

@app.post("/predict")
def predict(request: PredictRequest):  # Automatic validation!
    temp = request.temp_mean_c  # Guaranteed to be float in range
    # Just use it!
```

**Field Validators**
```python
from pydantic import BaseModel, Field, validator

class ForecastDay(BaseModel):
    date: str
    temp_mean_c: float = Field(..., ge=-50, le=60, description="Temperature in Celsius")
    relative_humidity_pct: float = Field(..., ge=0, le=100)
    pm25_ugm3: float = Field(..., ge=0, description="PM2.5 concentration")
    
    @validator('date')
    def validate_date(cls, v):
        """Custom validator for date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @validator('pm25_ugm3')
    def check_pm25_realistic(cls, v):
        """Warn if PM2.5 is extremely high"""
        if v > 500:
            # Could raise ValueError to reject, or just log warning
            import logging
            logging.warning(f"Extremely high PM2.5 value: {v}")
        return v
```

**Nested Models**
```python
class ForecastDay(BaseModel):
    date: str
    temp_mean_c: float
    humidity: float

class PredictRequest(BaseModel):
    region_id: str
    forecast: List[ForecastDay]  # Nested model
    
    @validator('forecast')
    def check_forecast_length(cls, v):
        if len(v) == 0:
            raise ValueError('Forecast must contain at least 1 day')
        if len(v) > 10:
            raise ValueError('Forecast cannot exceed 10 days')
        return v

# Request example
{
  "region_id": "R1",
  "forecast": [
    {"date": "2025-11-25", "temp_mean_c": 28.5, "humidity": 65},
    {"date": "2025-11-26", "temp_mean_c": 30.0, "humidity": 70}
  ]
}
```

### Response Models

**Why Define Response Models?**
```python
# Without response model (unreliable)
@app.post("/predict")
def predict(request: PredictRequest):
    return {"prediction": 12.5}  # What if you typo "prediciton"?

# With response model (guaranteed schema)
class PredictResponse(BaseModel):
    region_id: str
    predictions: List[float]
    forecast_date: datetime

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    return PredictResponse(
        region_id="R1",
        predictions=[12.5, 13.1, 11.8],
        forecast_date=datetime.now()
    )
    # If you forget a field or use wrong type → immediate error
```

**Automatic Documentation**
```python
# FastAPI generates OpenAPI docs from Pydantic models
# Visit: http://localhost:8000/docs

# You'll see:
# - All endpoints
# - Request schema (with examples)
# - Response schema
# - Try-it-out feature (test API in browser)
```

---

## Testing Frameworks

### pytest Basics

**Why pytest over unittest?**
```python
# unittest (verbose)
import unittest

class TestModel(unittest.TestCase):
    def setUp(self):
        self.model = load_model()
    
    def test_prediction_shape(self):
        result = self.model.predict(X_test)
        self.assertEqual(result.shape[0], len(X_test))

# pytest (concise)
import pytest

@pytest.fixture
def model():
    return load_model()

def test_prediction_shape(model):
    result = model.predict(X_test)
    assert result.shape[0] == len(X_test)  # Plain assert!
```

**Test Organization**
```
tests/
├── conftest.py           # Shared fixtures
├── test_ingest.py        # Data ingestion tests
├── test_preprocess.py    # Feature engineering tests
├── test_model.py         # Model training tests
└── test_api.py           # API endpoint tests
```

**conftest.py - Shared Fixtures**
```python
# tests/conftest.py
import pytest
import pandas as pd

@pytest.fixture(scope="session")
def sample_data():
    """Load sample data once for all tests"""
    return pd.read_csv('data_synthetic/synthetic_data.csv')

@pytest.fixture(scope="module")
def trained_model():
    """Train model once per test module"""
    from src.models.xgb_train import train_model
    return train_model()

@pytest.fixture
def api_client():
    """Create API test client"""
    from fastapi.testclient import TestClient
    from src.api.main import app, load_artifacts
    
    load_artifacts()  # Load model
    return TestClient(app)
```

**Using Fixtures**
```python
# tests/test_model.py
def test_model_predictions(trained_model, sample_data):
    """Test uses both fixtures automatically"""
    X = sample_data[feature_cols]
    predictions = trained_model.predict(X)
    
    assert predictions.shape[0] == len(X)
    assert (predictions >= 0).all()  # No negative admissions
```

### Test Patterns

**1. Arrange-Act-Assert (AAA)**
```python
def test_feature_engineering():
    # Arrange - Set up test data
    df = pd.DataFrame({
        'date': pd.date_range('2020-01-01', periods=30),
        'temp_mean': [20, 22, 24, 26, 28] * 6
    })
    
    # Act - Perform action
    result = add_lag_features(df, ['temp_mean'], max_lag=3)
    
    # Assert - Verify outcome
    assert 'temp_mean_lag1' in result.columns
    assert 'temp_mean_lag2' in result.columns
    assert 'temp_mean_lag3' in result.columns
    assert result['temp_mean_lag1'].iloc[1] == 20  # Yesterday's temp
```

**2. Parametrized Tests**
```python
@pytest.mark.parametrize("temp,expected_category", [
    (10, "cold"),
    (20, "mild"),
    (30, "warm"),
    (40, "hot")
])
def test_temperature_categorization(temp, expected_category):
    """Test multiple inputs without repeating code"""
    result = categorize_temperature(temp)
    assert result == expected_category

# Runs 4 separate tests automatically!
```

**3. Testing Exceptions**
```python
def test_invalid_input_raises_error():
    """Verify that bad input is rejected"""
    with pytest.raises(ValueError, match="Temperature out of range"):
        calculate_heat_index(temp=150, humidity=50)  # Invalid temp
```

**4. Mocking External Dependencies**
```python
from unittest.mock import Mock, patch

def test_api_without_real_model(api_client):
    """Test API without loading actual model (faster)"""
    
    # Mock the model
    mock_model = Mock()
    mock_model.predict.return_value = [12.5, 13.1]
    
    with patch('src.api.main.model', mock_model):
        response = api_client.post("/predict", json={...})
        
        assert response.status_code == 200
        mock_model.predict.assert_called_once()  # Verify model was called
```

### Test Coverage

**Measuring Coverage**
```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Opens htmlcov/index.html
# Shows which lines are covered (green) vs not covered (red)
```

**Coverage Configuration**
```ini
# .coveragerc
[run]
source = src
omit = 
    */tests/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

**Coverage Best Practices**
- Aim for 80% coverage (100% is overkill)
- Focus on critical paths (model training, API endpoints)
- Don't test third-party libraries
- Test edge cases (empty inputs, None, extremes)

---

## Docker Containerization

### Why Docker?

**The Problem**:
```
Developer: "Works on my machine!"
Ops Engineer: "Doesn't work in production"
Reason: Different Python versions, missing libraries, OS differences
```

**Docker Solution**:
```
Dockerfile defines exact environment
→ Same image runs on dev, staging, production
→ "Works on my machine" = "Works everywhere"
```

### Dockerfile Explained Line-by-Line

```dockerfile
# Base image - official Python on Debian Linux
FROM python:3.11-slim
# Why slim? python:3.11 is 1GB, slim is 150MB
# Trade-off: slim requires manual installation of some system libraries

# Metadata (optional but professional)
LABEL maintainer="your-email@example.com"
LABEL version="1.0.0"
LABEL description="Climate-CVD Risk Prediction API"

# Set working directory
WORKDIR /app
# All subsequent commands run in /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ \                    # C compilers (for building Python packages)
    libgdal-dev \                # Geospatial Data Abstraction Library
    libgeos-dev \                # Geometry Engine Open Source
    libproj-dev \                # Cartographic projections
    && rm -rf /var/lib/apt/lists/*
# Why chain with &&? Single layer = smaller image
# Why remove apt lists? Saves 50MB

# Copy only requirements first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Why separate step? If requirements.txt unchanged, Docker reuses cached layer
# Saves time on rebuild (don't reinstall packages)

# Copy application code
COPY . /app
# Copies everything except items in .dockerignore

# Generate data at build time (optional - could do at runtime)
RUN python data_synthetic/generate_synthetic.py && \
    python src/preprocess.py
# Pros: Faster container startup
# Cons: Larger image, data baked into image

# Expose ports (documentation only, doesn't actually open ports)
EXPOSE 8000 8501
# 8000: FastAPI
# 8501: Streamlit

# Health check (Docker monitors container health)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
# Checks every 30s, allows 40s for startup, fails after 3 retries

# Default command (can be overridden)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
# --host 0.0.0.0: Listen on all interfaces (not just localhost)
```

### .dockerignore

**Why It Matters**
```
# Without .dockerignore
Sending build context to Docker daemon: 2.5GB  # Uploading everything!
Step 1/10 : FROM python:3.11-slim

# With .dockerignore
Sending build context to Docker daemon: 50MB   # Much faster!
```

**What to Ignore**
```
# .dockerignore

# Version control
.git/
.gitignore

# Python cache
__pycache__/
*.pyc
*.pyo
*.egg-info/

# Virtual environments
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp

# Large data files (download separately)
data_raw/
*.csv
*.parquet

# Model artifacts (stored in registry, not image)
outputs/*.joblib

# Documentation (not needed in container)
docs/
*.md

# Tests (run in CI, not production)
tests/
pytest.ini
.coverage

# OS files
.DS_Store
Thumbs.db
```

### Docker Commands

**Building**
```bash
# Build image
docker build -t explainable-ai-cvd:v1.0.0 .

# Build with custom Dockerfile
docker build -f Dockerfile.dev -t myapp:dev .

# Build without cache (force rebuild)
docker build --no-cache -t myapp .

# Build with build args
docker build --build-arg PYTHON_VERSION=3.11 -t myapp .
```

**Running**
```bash
# Run container (foreground)
docker run -p 8000:8000 explainable-ai-cvd:v1.0.0

# Run in background (detached)
docker run -d -p 8000:8000 --name cvd-api explainable-ai-cvd:v1.0.0

# Run with environment variables
docker run -e DATABASE_URL=postgres://... -p 8000:8000 myapp

# Run with volume mount (access host files)
docker run -v $(pwd)/outputs:/app/outputs -p 8000:8000 myapp

# Run different command (override CMD)
docker run myapp python src/models/xgb_train.py

# Interactive shell
docker run -it myapp /bin/bash
```

**Managing Containers**
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop container
docker stop cvd-api

# Start stopped container
docker start cvd-api

# Restart container
docker restart cvd-api

# Remove container
docker rm cvd-api

# View logs
docker logs cvd-api

# Follow logs (like tail -f)
docker logs -f cvd-api

# Execute command in running container
docker exec cvd-api ls /app/outputs
docker exec -it cvd-api /bin/bash  # Interactive shell
```

**Managing Images**
```bash
# List images
docker images

# Remove image
docker rmi explainable-ai-cvd:v1.0.0

# Remove unused images
docker image prune

# Tag image
docker tag explainable-ai-cvd:v1.0.0 myregistry.com/cvd:v1.0.0

# Push to registry
docker push myregistry.com/cvd:v1.0.0

# Pull from registry
docker pull myregistry.com/cvd:v1.0.0
```

### Docker Compose

**Why Compose?**
Multiple services (API + dashboard + database) in one config

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/cvd
    depends_on:
      - db
    volumes:
      - ./outputs:/app/outputs
    restart: unless-stopped
  
  dashboard:
    build: .
    command: streamlit run src/dashboard/app.py
    ports:
      - "8501:8501"
    depends_on:
      - api
    restart: unless-stopped
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=cvd
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres-data:
```

**Compose Commands**
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f api

# Rebuild images
docker-compose build

# Scale service
docker-compose up --scale api=3  # Run 3 API containers
```

---

## CI/CD Pipelines

### What is CI/CD?

**Continuous Integration (CI)**:
- Every code push triggers automated tests
- Catches bugs before they reach production
- Enforces code quality (linting, formatting)

**Continuous Deployment (CD)**:
- Passing tests → automatic deployment
- Reduces manual errors
- Faster releases

### GitHub Actions Workflow

**File**: `.github/workflows/ci.yml`

```yaml
name: CI

# When to run
on:
  push:
    branches: [ main, develop ]  # Run on push to these branches
  pull_request:
    branches: [ main ]  # Run on PRs to main

# Jobs (can run in parallel)
jobs:
  test:
    name: Test and Lint
    runs-on: ubuntu-latest  # Free GitHub-hosted runner
    
    strategy:
      matrix:
        python-version: [3.10, 3.11]  # Test on multiple Python versions
    
    steps:
      # Step 1: Get code
      - name: Checkout code
        uses: actions/checkout@v3
      
      # Step 2: Setup Python
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      # Step 3: Cache dependencies (speed up builds)
      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      # Step 4: Install dependencies
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install flake8 black pytest-cov
      
      # Step 5: Lint
      - name: Lint with flake8
        run: |
          # Stop build if syntax errors or undefined names
          flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
          # Exit-zero treats all errors as warnings (max line length 100)
          flake8 src/ tests/ --count --exit-zero --max-line-length=100 --statistics
      
      # Step 6: Check formatting
      - name: Check format with black
        run: black src/ tests/ --check --diff
        # --check: Don't modify files, just check
        # --diff: Show what would change
      
      # Step 7: Generate data
      - name: Generate synthetic data
        run: python data_synthetic/generate_synthetic.py
      
      # Step 8: Run preprocessing
      - name: Run preprocessing
        run: python src/preprocess.py
      
      # Step 9: Run tests with coverage
      - name: Run tests
        run: pytest tests/ -v --cov=src --cov-report=xml --cov-report=term
      
      # Step 10: Upload coverage to Codecov (optional)
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
      
      # Step 11: Upload artifacts
      - name: Upload test artifacts
        uses: actions/upload-artifact@v3
        if: always()  # Upload even if tests fail
        with:
          name: test-results-${{ matrix.python-version }}
          path: |
            outputs/
            htmlcov/
            .coverage
  
  docker:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test  # Only run if tests pass
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Build Docker image
        run: docker build -t explainable-ai-cvd:${{ github.sha }} .
      
      - name: Test Docker image
        run: |
          # Verify Python version
          docker run explainable-ai-cvd:${{ github.sha }} python --version
          
          # Verify files exist
          docker run explainable-ai-cvd:${{ github.sha }} ls -la outputs/
      
      # Optional: Push to registry
      - name: Log in to Docker Hub
        if: github.ref == 'refs/heads/main'  # Only on main branch
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Push to Docker Hub
        if: github.ref == 'refs/heads/main'
        run: |
          docker tag explainable-ai-cvd:${{ github.sha }} username/cvd:latest
          docker push username/cvd:latest
```

### Secrets Management

**Setting Secrets**:
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `API_KEY`, etc.

**Using Secrets**:
```yaml
- name: Deploy to production
  env:
    API_KEY: ${{ secrets.API_KEY }}
    DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
  run: |
    echo "Deploying with API key: $API_KEY"
    # Secrets are masked in logs (shows ***)
```

### Status Badges

```markdown
# README.md
[![CI](https://github.com/username/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/username/repo/actions)
[![codecov](https://codecov.io/gh/username/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/username/repo)
```

---

## Summary

### Key Professional Features

1. **Health Checks**: Monitor system status, enable load balancing
2. **Pydantic Validation**: Automatic request validation, clear errors
3. **pytest**: Simple, powerful testing framework
4. **Docker**: Reproducible environments, easy deployment
5. **CI/CD**: Automated quality gates, faster releases

### Best Practices

- ✅ Health checks at multiple levels (liveness, readiness)
- ✅ Comprehensive request validation with Pydantic
- ✅ Test coverage > 80%
- ✅ Docker images < 500MB
- ✅ CI/CD runs on every commit
- ✅ Secrets never in code
- ✅ Log everything important
- ✅ Monitor production

### Common Mistakes to Avoid

- ❌ No health checks (can't detect failures)
- ❌ Manual validation (error-prone)
- ❌ No tests (regressions inevitable)
- ❌ Large Docker images (slow deployments)
- ❌ No CI/CD (broken code reaches production)
- ❌ Secrets in code (security breach)

---

**Next**: Read `04-infrastructure-files-guide.md` for configuration files explained
