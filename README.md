# Explainable AI for Climate-Linked Cardiovascular Admissions

[![CI](https://github.com/[your-username]/ExplainableAIforHealth/actions/workflows/ci.yml/badge.svg)](https://github.com/[your-username]/ExplainableAIforHealth/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Production-ready system linking regional climate variability to daily cardiovascular emergency admissions with causal inference, explainable AI, and policy-ready visualizations.**

---

## 🎯 Overview

This end-to-end project demonstrates how meteorological conditions influence cardiovascular health outcomes. It combines:

- **Causal Inference:** Distributed Lag Non-Linear Models (DLNM) to estimate exposure-response relationships
- **Machine Learning:** XGBoost predictive model (R²=0.903) for multi-day forecasting
- **Explainability:** SHAP values revealing which features drive predictions
- **Policy Tools:** Risk calendars, threshold curves, spatial maps, and automated policy briefs
- **Production API:** FastAPI REST service for real-time predictions and alerts
- **Interactive Dashboard:** Streamlit application for exploratory analysis

**Current Status:** All milestones complete (0-7). System runs on synthetic data and is ready for deployment with real hospital admissions data.

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Architecture](#-architecture)
3. [Installation](#-installation)
4. [Usage](#-usage)
5. [Data Pipeline](#-data-pipeline)
6. [Models](#-models)
7. [API Reference](#-api-reference)
8. [Dashboard](#-dashboard)
9. [Deployment](#-deployment)
10. [Production Deployment with Real Data](#-production-deployment-with-real-data)
11. [Data Governance](#-data-governance)
12. [Testing](#-testing)
13. [Contributing](#-contributing)
14. [License](#-license)

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```powershell
# Build image
docker build -t explainable-ai-cvd .

# Run API (http://localhost:8000)
docker run -p 8000:8000 explainable-ai-cvd

# Run dashboard (http://localhost:8501)
docker run -p 8501:8501 explainable-ai-cvd streamlit run src/dashboard/app.py
```

### Option 2: Local Installation

```powershell
# Clone and setup
git clone https://github.com/[your-username]/ExplainableAIforHealth.git
cd ExplainableAIforHealth

# Create virtual environment (Python 3.11 recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run full pipeline
make all

# Start API
make run-api

# Start dashboard (separate terminal)
make run-dashboard
```

**First Run Output:**
- Synthetic data: `data_synthetic/synthetic_data.csv`
- Processed features: `data_processed/region_daily.parquet` (129 columns)
- Trained model: `outputs/xgb_model.joblib`
- Visualizations: `outputs/*.png` and `outputs/spatial_risk_map.html`
- Policy brief: `outputs/policy_statement.txt`

---

## 🏗 Architecture

```
┌─────────────────┐
│ Meteorological  │
│  Data Sources   │──┐
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌──────────────────┐
│ Hospital EHR    │──┼───▶│  Data Pipeline   │
│ (Admissions)    │  │    │ (ingest, feature │
└─────────────────┘  │    │  engineering)    │
                     │    └────────┬─────────┘
┌─────────────────┐  │             │
│ Air Quality     │──┘             │
│ Monitoring      │                ▼
└─────────────────┘    ┌───────────────────────┐
                       │  Modeling Layer       │
                       │ • DLNM (Causal)       │
                       │ • XGBoost (Predictive)│
                       │ • SHAP (Explainability)│
                       └───────────┬───────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
         ┌───────────┐      ┌──────────┐     ┌──────────────┐
         │  FastAPI  │      │ Streamlit│     │ Visualizations│
         │  (REST)   │      │ Dashboard│     │ (Policy Briefs)│
         └───────────┘      └──────────┘     └──────────────┘
```

**Key Components:**

- **Data Layer:** Ingestion, validation, provenance tracking
- **Feature Engineering:** 117 engineered features (lags, rolling stats, derived indices)
- **Modeling:** DLNM for causal inference + XGBoost for prediction
- **Explainability:** SHAP values for feature importance and interaction effects
- **Deployment:** API + dashboard for operational use

---

## 💾 Installation

### Prerequisites

- Python 3.11+ (3.10 also supported)
- 2GB RAM minimum (4GB recommended for SHAP analysis)
- Optional: R 4.0+ with `dlnm` and `mgcv` packages for canonical DLNM

### System Dependencies (for Docker/geopandas)

**Linux/WSL:**
```bash
sudo apt-get install gcc g++ libgdal-dev libgeos-dev libproj-dev
```

**macOS:**
```bash
brew install gdal geos proj
```

**Windows:** Use Docker or install via conda-forge

### Python Packages

```powershell
pip install -r requirements.txt
```

**Core Dependencies:**
- `pandas>=2.2.2`, `numpy>=1.26.4` – Data manipulation
- `xgboost>=2.0.3` – ML modeling
- `shap>=0.45.0` – Explainability
- `fastapi>=0.115.0`, `uvicorn>=0.30.6` – API
- `streamlit>=1.38.0` – Dashboard
- `statsmodels>=0.14.2` – DLNM fallback
- `matplotlib>=3.9.0`, `seaborn>=0.13.2` – Visualization
- `geopandas>=1.0.1`, `folium>=0.17.0` – Spatial maps

---

## 📖 Usage

### End-to-End Pipeline

```powershell
# Generate synthetic data
make synthetic

# Preprocess and engineer features
make preprocess

# Train models
make train

# Generate visualizations
make viz

# Run tests
make test

# Or run everything at once
make all
```

### Individual Components

**1. Data Generation (Synthetic)**
```powershell
python data_synthetic/generate_synthetic.py
```
Output: `data_synthetic/synthetic_data.csv` (1,096 daily records)

**2. Preprocessing**
```powershell
python src/preprocess.py
```
Output: `data_processed/region_daily.parquet` (129 features)

**3. DLNM Causal Modeling**
```powershell
python src/models/run_dlnm.py
```
Output: `outputs/dlnm_*.png`, `outputs/dlnm_effect_summary.txt`

**4. XGBoost Training**
```powershell
python src/models/xgb_train.py
```
Output: `outputs/xgb_model.joblib`, `outputs/metrics.json`

**5. SHAP Explainability**
```powershell
python src/explainers.py
```
Output: `outputs/shap_summary.png`, `outputs/shap_dependence_*.png`

**6. Policy Statement**
```powershell
python src/models/produce_policy_statement.py
```
Output: `outputs/policy_statement.txt`, `outputs/policy_statement.json`

---

## 🔄 Data Pipeline

### Input Schema

**Required Columns:**
```
date              YYYY-MM-DD
region_id         String (e.g., "R1")
admissions        Integer (daily count)
temp_mean_c       Float (°C)
temp_min_c        Float (°C)
temp_max_c        Float (°C)
relative_humidity_pct  Float (%)
dew_point_c       Float (°C)
pm25_ugm3         Float (µg/m³)
day_of_week       Integer (0=Mon, 6=Sun)
is_holiday        Boolean (0/1)
season            String (Winter/Spring/Summer/Fall)
```

### Feature Engineering

**Engineered Features (117 total):**

1. **Lag Features (0-21 days):** `temp_mean_c_lag_1`, `humidity_lag_7`, etc.
2. **Rolling Statistics:** 3/7/14-day means and standard deviations
3. **Derived Indices:**
   - Heat Index: `heat_index_c = 0.5*(T + 61 + 1.2(T-68) + 0.094*RH)`
   - Apparent Temperature: `apparent_temp_c = T + 0.33*vapor_pressure - 0.7*wind_speed - 4.0`
   - Diurnal Range: `temp_range_c = temp_max_c - temp_min_c`
4. **Temporal Features:** Month, year, day of year, day of week
5. **Weather Derivatives:** Rate of change, volatility measures

**Processing Steps:**
1. Date parsing and chronological sorting
2. Schema validation (types, ranges)
3. Feature generation (vectorized operations)
4. Provenance logging (`outputs/data_provenance.json`)
5. Parquet serialization for performance

---

## 🤖 Models

### 1. Distributed Lag Non-Linear Model (DLNM)

**Purpose:** Estimate causal exposure-response relationships accounting for delayed effects

**Implementation:**
- **Preferred:** R script using `dlnm` package with natural cubic splines
- **Fallback:** Python using `statsmodels` GLM with `patsy` for basis functions

**Key Outputs:**
- Exposure-response curves (temperature vs. relative risk)
- Lag-response surfaces (effect decay over time)
- Effect summary statistics (cumulative lag 0-14 days)

**Files:**
- `src/models/dlnm_r_script.R`
- `src/models/run_dlnm.py`

### 2. XGBoost Regressor

**Purpose:** Predict daily admissions for multi-day forecasts

**Configuration:**
```python
XGBRegressor(
    objective='count:poisson',
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
```

**Performance (Synthetic Data):**
- **Test MAE:** 0.897 admissions/day
- **Test RMSE:** 0.938
- **Test R²:** 0.903
- **Calibration:** Well-calibrated (see `outputs/xgb_calibration.png`)

**Features Used:** All 129 engineered features

**Train/Test Split:** Time-based (first 80% train, last 20% test)

**Files:**
- `src/models/xgb_train.py`
- `outputs/xgb_model.joblib`

### 3. SHAP Explainability

**Purpose:** Interpret model predictions and identify key drivers

**Method:** PermutationExplainer (robust to XGBoost version compatibility)

**Key Analyses:**
- **Summary Plot:** Feature importance across all predictions
- **Dependence Plots:** Interaction effects between features
- **Force Plots:** Individual prediction explanations for high-risk days

**Top Drivers (Typical):**
1. `temp_mean_c_lag_1` (1-day lagged temperature)
2. `temp_mean_c_lag_2` (2-day lagged temperature)
3. `pm25_ugm3_lag_1` (1-day lagged air pollution)
4. `relative_humidity_pct` (current humidity)
5. `day_of_week` (temporal pattern)

**Files:**
- `src/explainers.py`
- `outputs/shap_summary.png`

---

## 🌐 API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### `GET /health`

**Description:** Service health check

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_metrics": {
    "test_mae": 0.897,
    "test_r2": 0.903
  }
}
```

#### `POST /predict`

**Description:** Generate 5-day forecast with SHAP-based feature attributions

**Request Body:**
```json
{
  "forecast_days": [
    {
      "date": "2023-01-15",
      "temp_mean_c": 28.5,
      "temp_min_c": 22.0,
      "temp_max_c": 35.0,
      "relative_humidity_pct": 65.0,
      "dew_point_c": 18.5,
      "pm25_ugm3": 35.0,
      "day_of_week": 0,
      "is_holiday": false,
      "season": "Summer"
    }
  ]
}
```

**Response:**
```json
{
  "region_id": "R1",
  "forecast_date": "2023-01-10T12:00:00",
  "predictions": [
    {
      "date": "2023-01-15",
      "predicted_admissions": 8.5,
      "risk_score": 0.72,
      "drivers": [
        {"feature": "temp_mean_c_lag_1", "contribution": 1.2},
        {"feature": "pm25_ugm3_lag_1", "contribution": 0.8}
      ]
    }
  ]
}
```

**Usage:**
```powershell
curl -X POST http://localhost:8000/predict `
  -H "Content-Type: application/json" `
  -d @examples/sample_forecast.json
```

#### `POST /alert`

**Description:** Check if conditions exceed risk thresholds

**Request Body:**
```json
{
  "date": "2023-01-15",
  "temp_mean_c": 35.0,
  "pm25_ugm3": 50.0,
  "predicted_admissions": 12.0
}
```

**Response:**
```json
{
  "alert": true,
  "date": "2023-01-15",
  "predicted_admissions": 12.0,
  "threshold_exceeded": true,
  "risk_level": "high",
  "recommendations": [
    "Activate heat health warning system",
    "Increase hospital staffing for cardiovascular units"
  ]
}
```

---

## 📊 Dashboard

### Launch

```powershell
streamlit run src/dashboard/app.py
```

Access at: `http://localhost:8501`

### Pages

1. **Overview**
   - Model performance metrics
   - Dataset summary statistics
   - Recent prediction trends

2. **Risk Calendar**
   - Year-by-year heatmap of daily risk scores
   - Spatial risk map (interactive folium)

3. **Model Explainability**
   - SHAP summary plot
   - Top feature contributions
   - Dependence plots

4. **Forecast**
   - Input form for custom predictions
   - 5-day forecast visualization

5. **Policy Statement**
   - Downloadable policy brief (PDF)
   - Machine-readable JSON export

---

## 🐳 Deployment

### Docker Build

```powershell
docker build -t explainable-ai-cvd:v1.0.0 .
```

**Build Process:**
1. Installs system dependencies (geopandas requirements)
2. Installs Python packages
3. Generates synthetic data
4. Runs preprocessing
5. Exposes ports 8000 (API) and 8501 (dashboard)

### Run Containers

**API:**
```powershell
docker run -d -p 8000:8000 --name cvd-api explainable-ai-cvd:v1.0.0
```

**Dashboard:**
```powershell
docker run -d -p 8501:8501 --name cvd-dashboard `
  explainable-ai-cvd:v1.0.0 streamlit run src/dashboard/app.py
```

### Docker Compose (Recommended)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  api:
    image: explainable-ai-cvd:v1.0.0
    ports:
      - "8000:8000"
    volumes:
      - ./outputs:/app/outputs
  
  dashboard:
    image: explainable-ai-cvd:v1.0.0
    command: streamlit run src/dashboard/app.py
    ports:
      - "8501:8501"
    volumes:
      - ./outputs:/app/outputs
```

Run:
```powershell
docker-compose up -d
```

---

## 🏥 Production Deployment with Real Data

### Step 1: Data Acquisition

**Replace synthetic data with real hospital admissions:**

1. **Extract from EHR:**
   - ICD-10 codes: I00-I99 (cardiovascular)
   - Daily aggregation (count by date and region)
   - De-identify before export (no patient IDs)

2. **Obtain Meteorological Data:**
   - Historical: NOAA Climate Data Online (CDO)
   - Forecast: National Weather Service API
   - Required: temp_mean/min/max, relative humidity, dew point

3. **Air Quality Data:**
   - EPA Air Quality System (AQS)
   - Daily PM2.5 averages by monitoring station
   - Map to health regions

### Step 2: Data Preparation

**Format CSV matching schema:**
```csv
date,region_id,admissions,temp_mean_c,temp_min_c,temp_max_c,relative_humidity_pct,dew_point_c,pm25_ugm3,day_of_week,is_holiday,season
2020-01-01,R1,8,15.2,12.0,18.5,60.0,8.5,25.0,2,1,Winter
```

**Place file at:**
```
data_raw/hospital_admissions.csv
```

**Update `src/ingest.py`:**
```python
# Change line 85
df = pd.read_csv("data_raw/hospital_admissions.csv")  # Real data path
```

### Step 3: Retrain Models

```powershell
# Full pipeline with new data
make preprocess
make train
make viz

# Verify performance
pytest tests/test_model.py
```

### Step 4: Validate Performance

**Checklist:**
- [ ] Test R² > 0.80 (acceptable for operational use)
- [ ] Residuals show no systematic bias by season
- [ ] SHAP values align with epidemiological knowledge
- [ ] Forecast accuracy validated on recent holdout period
- [ ] Causal estimates match literature (DLNM)

### Step 5: Configure Forecast Integration

**Update `src/api/main.py` for live weather API:**

```python
import requests

def fetch_weather_forecast(region_id: str, days: int = 5):
    """Fetch real-time weather forecast"""
    url = f"https://api.weather.gov/points/{lat},{lon}/forecast"
    response = requests.get(url)
    # Parse and return ForecastDay objects
    return forecast_days
```

**Replace line 45 in `/predict` endpoint:**
```python
# Real forecast source
forecast_days = fetch_weather_forecast(request.region_id)
```

### Step 6: Deploy with Security

**Environment Variables:**
```powershell
# Create .env file
$env:API_KEY="your-secure-key"
$env:DB_CONNECTION_STRING="postgresql://..."
$env:LOG_LEVEL="INFO"
```

**API Authentication:**
Add to `src/api/main.py`:
```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.post("/predict")
async def predict(request: PredictRequest, api_key: str = Depends(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(401, "Invalid API key")
    # ... existing code
```

---

## 🔒 Data Governance

### Privacy and Security

**HIPAA Compliance:**
- No patient identifiers in aggregated admissions data
- Minimum cell size: ≥5 admissions/day to prevent re-identification
- Secure data enclave for model training
- Access controls via institutional IRB approval

**Data Use Agreement:**
- Hospital retains ownership of admissions data
- Research use only (specify in DUA)
- No commercial redistribution
- Annual compliance audits

### Data Provenance

**Tracked in `outputs/data_provenance.json`:**
```json
{
  "source_file": "data_raw/hospital_admissions.csv",
  "ingestion_timestamp": "2023-01-15T10:30:00",
  "row_count": 1096,
  "date_range": ["2020-01-01", "2022-12-31"],
  "schema_version": "1.0.0",
  "preprocessing_params": {
    "max_lag_days": 21,
    "rolling_windows": [3, 7, 14]
  }
}
```

### Model Versioning

**Semantic Versioning:**
- Major: Breaking changes to API or data schema
- Minor: New features (e.g., additional regions)
- Patch: Bug fixes or performance improvements

**Artifact Registry:**
- Model file: `outputs/xgb_model_v1.0.0.joblib`
- Training metadata: `outputs/model_metadata.json`
- Git tag: `v1.0.0`

---

## 🧪 Testing

### Run All Tests

```powershell
pytest tests/ -v
```

**Coverage:**
- Ingestion: Schema validation, date parsing
- Preprocessing: Feature engineering, null checks
- Models: Training, prediction, SHAP computation
- API: Health check, prediction, alert endpoints
- Visualizations: Plot generation, file output

### Smoke Test (End-to-End)

```powershell
.\tests\run_smoke.sh
```

**Verifies:**
1. Data generation completes
2. Preprocessing produces expected columns
3. Model training converges
4. API responds to requests
5. Dashboard launches without errors

### Continuous Integration

**GitHub Actions:** `.github/workflows/ci.yml`

**Triggers:** Push to main, pull requests

**Jobs:**
1. **Test:** Lint, pytest, visualization checks
2. **Docker:** Build image, smoke test

---

## 📚 Documentation

### Key Documents

- **Model Card:** [`docs/model_card.md`](docs/model_card.md)
  - Model architecture, performance, limitations
  - Intended use and ethical considerations

- **Data Datasheet:** [`docs/datasheet.md`](docs/datasheet.md)
  - Dataset composition, collection methods
  - Privacy and maintenance procedures

- **Handover Guide:** [`handover.txt`](handover.txt)
  - Production deployment checklist
  - Where to modify forecast sources
  - How to swap synthetic data with real data

### Code Documentation

**Docstrings:** All functions include NumPy-style docstrings

**Example:**
```python
def add_lag_features(df: pd.DataFrame, cols: List[str], max_lag: int) -> pd.DataFrame:
    """
    Add lagged features for specified columns.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with time series data
    cols : List[str]
        Column names to create lags for
    max_lag : int
        Maximum lag in days
    
    Returns
    -------
    pd.DataFrame
        Dataframe with additional lag columns
    """
```

---

## 🤝 Contributing

### Development Setup

```powershell
# Fork and clone
git clone https://github.com/[your-username]/ExplainableAIforHealth.git
cd ExplainableAIforHealth

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
pytest tests/

# Commit with descriptive messages
git commit -m "Add feature: multi-region support"

# Push and create pull request
git push origin feature/your-feature-name
```

### Code Style

**Linting:**
```powershell
flake8 src/ tests/ --max-line-length=100
black src/ tests/ --check
```

**Pre-commit Hooks (Optional):**
```powershell
pip install pre-commit
pre-commit install
```

### Contribution Guidelines

1. **Tests Required:** All new features must include tests
2. **Documentation:** Update README and docstrings
3. **Backwards Compatibility:** Maintain API schema stability
4. **Performance:** Profile code for large datasets (>100k rows)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

**Citation:**
```bibtex
@software{explainable_ai_cvd_2025,
  title={Explainable AI for Climate-Linked Cardiovascular Admissions},
  author={[Your Name]},
  year={2025},
  url={https://github.com/[your-username]/ExplainableAIforHealth}
}
```

---

## 📞 Contact

**Questions or Issues:** Open a GitHub issue

**Security Vulnerabilities:** Email [security@example.com]

**Collaboration Inquiries:** [contact@example.com]

---

## 🏆 Acknowledgments

- **Methodology:** Inspired by Gasparrini et al. (2010) DLNM framework
- **Explainability:** SHAP (Lundberg & Lee, 2017)
- **Data Standards:** Model Cards (Mitchell et al., 2019), Datasheets (Gebru et al., 2021)

---

**Version:** 1.0.0  
**Last Updated:** November 2025
