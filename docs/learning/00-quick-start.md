# Quick Start Guide - Get Running in 10 Minutes

This guide gets you from zero to running the complete system. For detailed explanations, see the [main learning materials](README.md).

## Prerequisites

- **Python 3.11+** installed
- **Git** installed
- **10 GB** disk space
- **Internet connection** (for downloading packages)

## Step 1: Get the Code (1 minute)

```bash
# Clone or navigate to project
cd "c:\A Developer's Stuff\CMP\ExplainableAIforHealth"
```

## Step 2: Set Up Environment (3 minutes)

### Windows (PowerShell)
```powershell
# Create virtual environment
python -m venv .venv

# Activate
.\.venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt
```

### Mac/Linux
```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Generate Data (1 minute)

```bash
# Create synthetic climate-health data
python data_synthetic/generate_synthetic.py

# Expected output:
# Generating synthetic data for 4 years, 3 regions...
# Saved to data_synthetic/synthetic_data.csv
# Shape: (4383, 6)
```

## Step 4: Preprocess Data (1 minute)

```bash
# Create 60+ features
python src/preprocess.py

# Expected output:
# Loading data from data_synthetic/synthetic_data.csv
# Adding temporal features...
# Adding lag features...
# Adding rolling features...
# Saved to data_synthetic/preprocessed_features.csv
# Original columns: 10, Engineered: 50+, Total: 60+
```

## Step 5: Train Models (2 minutes)

### Train XGBoost
```bash
python src/models/xgb_train.py

# Expected output (last lines):
# Test R²: 0.903
# Test MAE: 0.897
# Test RMSE: 1.201
# Model saved to outputs/xgb_model.joblib
```

### Train DLNM (optional)
```bash
python src/models/dlnm_fit.py

# Expected output:
# Fitting DLNM model...
# Model saved to outputs/dlnm_model.joblib
```

## Step 6: Run API (1 minute)

```bash
# Start FastAPI server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Started server process
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

**Keep this terminal open!**

## Step 7: Test API (30 seconds)

Open a **new terminal** (keep API running):

### Windows (PowerShell)
```powershell
# Health check
curl http://localhost:8000/health

# Prediction
curl -Method POST `
  -Uri "http://localhost:8000/predict" `
  -ContentType "application/json" `
  -Body '{"region_id":"R1","forecast":[{"date":"2025-11-25","temp_mean_c":28.5,"relative_humidity_pct":65,"pm25_ugm3":42}]}'
```

### Mac/Linux
```bash
# Health check
curl http://localhost:8000/health

# Prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "region_id": "R1",
    "forecast": [
      {
        "date": "2025-11-25",
        "temp_mean_c": 28.5,
        "relative_humidity_pct": 65,
        "pm25_ugm3": 42
      }
    ]
  }'
```

### Expected Response
```json
{
  "region_id": "R1",
  "predictions": [12.5],
  "dates": ["2025-11-25"],
  "shap_values": [...],
  "baseline": 11.2
}
```

## Step 8: Run Dashboard (1 minute)

Open a **third terminal** (keep API running):

```bash
# Activate virtual environment (if new terminal)
# Windows: .\.venv\Scripts\Activate.ps1
# Mac/Linux: source .venv/bin/activate

# Start Streamlit dashboard
streamlit run src/dashboard/app.py

# Expected output:
# You can now view your Streamlit app in your browser.
# Local URL: http://localhost:8501
```

**Dashboard automatically opens in browser!**

## Step 9: Interact with Dashboard (2 minutes)

In the dashboard:

1. **Left Sidebar**: 
   - Select Region: `R1`
   - Pick Date: `2025-11-25`
   - Temperature: `28°C`
   - Humidity: `65%`
   - PM2.5: `42`
   - Click **"Get Prediction"**

2. **Main Area - Tab 1 (Predictions)**:
   - See predicted CVD admissions: **~12.5**
   - View time series plot
   - Inspect SHAP waterfall (feature contributions)

3. **Main Area - Tab 2 (Risk Heatmap)**:
   - Interactive 2D heatmap (temp vs humidity)
   - Color shows risk level
   - Hover for exact predictions

4. **Main Area - Tab 3 (Regional Map)**:
   - Interactive map with region markers
   - Color-coded by risk level
   - Click markers for details

5. **Main Area - Tab 4 (DLNM Analysis)**:
   - Lag-response curves
   - Temperature effects over time
   - Cumulative effects

## Troubleshooting

### "Model not found" error
```bash
# Make sure you ran Step 5 (train models)
ls outputs/xgb_model.joblib

# If missing, train again:
python src/models/xgb_train.py
```

### "Module not found" error
```bash
# Make sure virtual environment is activated
# Windows: .\.venv\Scripts\Activate.ps1
# Mac/Linux: source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### API connection error in dashboard
```bash
# Make sure API is running (Step 6)
curl http://localhost:8000/health

# If not running, start it:
uvicorn src.api.main:app --reload
```

### Port already in use
```bash
# API (port 8000)
# Windows: netstat -ano | findstr :8000
# Mac/Linux: lsof -i :8000
# Kill process and restart

# Dashboard (port 8501)
# Windows: netstat -ano | findstr :8501
# Mac/Linux: lsof -i :8501
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
# Windows: start htmlcov\index.html
# Mac: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```

Expected: **18 tests passed** ✅

## Running with Docker

### Build Image
```bash
docker build -t explainable-ai-cvd:v1.0.0 .

# Takes ~5 minutes on first build
```

### Run API Container
```bash
docker run -d \
  -p 8000:8000 \
  --name cvd-api \
  explainable-ai-cvd:v1.0.0

# Check logs
docker logs -f cvd-api
```

### Run Dashboard Container
```bash
docker run -d \
  -p 8501:8501 \
  -e API_URL=http://host.docker.internal:8000 \
  --name cvd-dashboard \
  explainable-ai-cvd:v1.0.0 \
  streamlit run src/dashboard/app.py

# Check logs
docker logs -f cvd-dashboard
```

### Stop Containers
```bash
docker stop cvd-api cvd-dashboard
docker rm cvd-api cvd-dashboard
```

### Using Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## API Endpoints Reference

### GET /health
**Purpose**: Check API status

**Request**:
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "ok",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### POST /predict
**Purpose**: Get CVD admission predictions

**Request**:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "region_id": "R1",
    "forecast": [
      {
        "date": "2025-11-25",
        "temp_mean_c": 28.5,
        "relative_humidity_pct": 65,
        "pm25_ugm3": 42
      }
    ]
  }'
```

**Response**:
```json
{
  "region_id": "R1",
  "predictions": [12.5],
  "dates": ["2025-11-25"],
  "shap_values": [{...}],
  "baseline": 11.2,
  "metadata": {
    "model_version": "1.0.0",
    "timestamp": "2025-01-18T12:00:00Z"
  }
}
```

### POST /explain
**Purpose**: Detailed SHAP explanation

**Request**: Same as `/predict`

**Response**: Includes detailed feature contributions

## Common Commands Cheat Sheet

```bash
# Virtual Environment
python -m venv .venv                    # Create
.\.venv\Scripts\Activate.ps1           # Activate (Windows)
source .venv/bin/activate               # Activate (Mac/Linux)
deactivate                              # Deactivate

# Data Pipeline
python data_synthetic/generate_synthetic.py  # Generate data
python src/preprocess.py                     # Preprocess
python src/models/xgb_train.py              # Train XGBoost
python src/models/dlnm_fit.py               # Train DLNM

# API
uvicorn src.api.main:app --reload           # Start API
curl http://localhost:8000/health           # Health check
curl http://localhost:8000/docs             # API docs

# Dashboard
streamlit run src/dashboard/app.py          # Start dashboard

# Testing
pytest tests/ -v                            # Run tests
pytest tests/ --cov=src                     # With coverage

# Docker
docker build -t cvd-api .                   # Build image
docker run -p 8000:8000 cvd-api            # Run container
docker-compose up                           # Start all services

# Git
git status                                  # Check status
git add .                                   # Stage all
git commit -m "message"                     # Commit
git push                                    # Push to remote
```

## File Structure Overview

```
ExplainableAIforHealth/
├── data_synthetic/
│   ├── generate_synthetic.py          # Creates synthetic data
│   ├── synthetic_data.csv             # Raw data (generated)
│   └── preprocessed_features.csv      # Processed data (generated)
│
├── src/
│   ├── preprocess.py                  # Feature engineering
│   ├── models/
│   │   ├── xgb_train.py              # XGBoost training
│   │   └── dlnm_fit.py               # DLNM training
│   ├── api/
│   │   └── main.py                   # FastAPI application
│   └── dashboard/
│       └── app.py                    # Streamlit dashboard
│
├── outputs/
│   ├── xgb_model.joblib              # Trained XGBoost model
│   ├── dlnm_model.joblib             # Trained DLNM model
│   ├── baseline_data.joblib          # SHAP baseline
│   ├── feature_names.joblib          # Feature order
│   └── *.png                         # Generated plots
│
├── tests/
│   ├── test_ingest.py                # Data tests
│   ├── test_preprocess.py            # Feature tests
│   ├── test_model.py                 # Model tests
│   └── test_api.py                   # API tests
│
├── docs/
│   └── learning/                     # Learning materials
│       ├── README.md                 # This guide!
│       ├── 01-project-walkthrough.md
│       ├── 02-problems-and-solutions.md
│       ├── 03-professional-features-guide.md
│       ├── 04-infrastructure-files-guide.md
│       └── 05-technical-architecture.md
│
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Docker image definition
├── docker-compose.yml                 # Multi-container setup
└── README.md                          # Project overview
```

## What Next?

Now that everything is running:

1. **Explore the Dashboard**: Try different inputs, see how predictions change
2. **Check API Docs**: Visit http://localhost:8000/docs for interactive API documentation
3. **Read Learning Materials**: Start with [README.md](README.md) for comprehensive guides
4. **Modify Code**: Change hyperparameters, add features, customize dashboard
5. **Run Tests**: Ensure everything works: `pytest tests/ -v`

## Quick Wins - 5-Minute Experiments

### Experiment 1: Change Temperature
1. Dashboard → Temperature slider → Move from 20°C to 35°C
2. Click "Get Prediction"
3. **Observe**: Predictions increase with temperature
4. **Why?**: Heat stress increases CVD risk

### Experiment 2: Compare Regions
1. Select Region R1 → Get Prediction → Note value
2. Select Region R2 → Get Prediction → Note value
3. Select Region R3 → Get Prediction → Note value
4. **Observe**: Different baseline risks per region

### Experiment 3: API Direct Call
1. Use curl to call API with extreme values
2. Try temp=50°C (very hot)
3. Try humidity=100% (very humid)
4. **Observe**: Model handles edge cases gracefully

### Experiment 4: Feature Importance
1. Dashboard → SHAP Waterfall plot
2. **Observe**: Which features contribute most?
3. Common top features:
   - `temp_mean_c_lag1` (yesterday's temperature)
   - `temp_mean_c_roll7` (week average)
   - `day_of_week` (weekday effect)

### Experiment 5: Risk Heatmap
1. Dashboard → Risk Heatmap tab
2. Find the "danger zone" (red area)
3. **Typical**: High temp + high humidity = highest risk
4. **Why?**: Combined heat and humidity stress cardiovascular system

## Performance Benchmarks

On typical hardware (4-core CPU, 8GB RAM):

| Task | Time | Notes |
|------|------|-------|
| Generate synthetic data | 10-30s | Creates 4,383 records |
| Preprocessing | 5-15s | Adds 50+ features |
| Train XGBoost | 10-30s | 200 trees, 60 features |
| Train DLNM | 30-60s | Spline fitting |
| API startup | 2-5s | Load models |
| Single prediction | <100ms | Including SHAP |
| Docker build | 5-10min | First time (layers cached after) |

## System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 5 GB
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+

### Recommended
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 10 GB (for Docker images)
- **OS**: Windows 11, macOS 12+, Ubuntu 20.04+

## Support

### Documentation
- **Quick Start**: This file
- **Complete Guide**: [docs/learning/README.md](README.md)
- **API Docs**: http://localhost:8000/docs (when running)

### Common Issues
See [02-problems-and-solutions.md](02-problems-and-solutions.md) for detailed troubleshooting.

### Questions?
1. Check the learning materials in `docs/learning/`
2. Review error messages carefully
3. Search GitHub issues
4. Read official documentation:
   - FastAPI: https://fastapi.tiangolo.com
   - Streamlit: https://docs.streamlit.io
   - XGBoost: https://xgboost.readthedocs.io

---

**Success Criteria**: 
✅ API responds to health check
✅ Dashboard loads in browser
✅ Predictions change with different inputs
✅ All 18 tests pass

**Congratulations!** 🎉 You now have a fully functional production-quality ML system running. 

**Next Step**: Read [docs/learning/README.md](README.md) to understand how everything works!
