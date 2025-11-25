# Complete Project Walkthrough - Technical Deep Dive

## Table of Contents
1. [Project Overview](#project-overview)
2. [Development Timeline](#development-timeline)
3. [Milestone-by-Milestone Implementation](#milestone-by-milestone-implementation)
4. [Technical Decisions and Rationale](#technical-decisions-and-rationale)
5. [Code Architecture](#code-architecture)

---

## Project Overview

### What We Built
A production-ready machine learning system that:
- Predicts daily cardiovascular emergency admissions based on weather conditions
- Combines causal inference (epidemiological rigor) with ML predictions
- Provides explainable AI through SHAP values
- Exposes REST API for real-time predictions
- Includes interactive dashboard for stakeholders
- Generates automated policy briefs for decision-makers

### Why This Approach?
1. **Causal + Predictive**: DLNM establishes causality, XGBoost provides accuracy
2. **Explainable**: SHAP makes the "black box" transparent for clinical trust
3. **Production-Ready**: API, Docker, CI/CD, comprehensive tests
4. **Policy-Oriented**: Not just science—actual tools for public health officials

---

## Development Timeline

### Milestone 0: Bootstrap (Foundation)
**Goal**: Set up project structure and synthetic data generation

**What We Did:**
1. Created directory structure following Python best practices
2. Implemented deterministic synthetic data generator
3. Set up version control (git) with clear commits
4. Created initial test suite
5. Wrote Makefile for automation
6. Added MIT license and basic README

**Why These Choices:**
- **Deterministic seed (42)**: Reproducibility is critical for science
- **Parquet format**: 5-10x faster than CSV, columnar storage efficient
- **Makefile**: One command (`make all`) runs everything—reduces friction
- **Tests first**: TDD mindset—write tests before adding features

**Code Walkthrough:**

```python
# data_synthetic/generate_synthetic.py
def generate(start_date="2020-01-01", days=1096, seed=42):
    """
    Why 1096 days? 3 years = enough for seasonal patterns
    Why seed=42? Reproducibility—same data every run
    """
    np.random.seed(seed)
    
    # Seasonal temperature pattern using sine wave
    # Why sine? Temperature follows sinusoidal annual pattern
    day_of_year = np.arange(days) % 365
    temp_mean_c = 15 + 12 * np.sin(2 * np.pi * day_of_year / 365 - np.pi / 2)
    
    # Why shift by -π/2? Makes January (day 0) the coldest month
    # Without shift: January would be at 15°C (spring-like)
    # With shift: January at ~3°C (realistic winter)
```

**Key Learning**: Synthetic data needs to mimic real patterns:
- Seasonal cycles (temperature, admissions)
- Lag effects (yesterday's heat affects today's admissions)
- Weekend patterns (fewer admissions on weekends—hospital coding delays)
- Random noise (real data is never perfectly smooth)

---

### Milestone 1: Data Ingestion & Preprocessing
**Goal**: Transform raw data into ML-ready features

**What We Did:**
1. Built validation pipeline (schema checks, date parsing)
2. Implemented provenance tracking (where did data come from?)
3. Created 117 engineered features from 12 input columns
4. Generated lag features (0-21 days)
5. Computed rolling statistics (3, 7, 14-day windows)
6. Derived weather indices (heat index, apparent temperature)

**Why Feature Engineering Matters:**
Machine learning models can't automatically understand time lags:
- Raw data: "Today is 30°C, 8 admissions"
- Model needs: "Today 30°C, yesterday 28°C, 2 days ago 27°C, 7-day avg 26°C..."

**Technical Deep Dive:**

```python
# src/features.py - Lag Features
def add_lag_features(df, cols, max_lag=21):
    """
    Why 21 days? Epidemiological studies show weather effects 
    typically span 0-21 days (acute + delayed responses)
    
    Why shift()? pandas shift(1) = move data down 1 row
    - Row 2 gets Row 1's value = "yesterday's temperature"
    """
    for col in cols:
        for lag in range(max_lag + 1):
            df[f'{col}_lag{lag}'] = df[col].shift(lag)
    
    # First 21 rows will have NaN for lag_21
    # Solution: forward fill or drop
    return df
```

**Rolling Statistics - Why?**
```python
def add_rolling_features(df, cols, windows=[3, 7, 14]):
    """
    Rolling mean = moving average
    Why? Captures short/medium/long-term trends
    
    3-day: Recent acute changes (heat wave starts)
    7-day: Weekly patterns (captures full week cycle)
    14-day: Longer trends (prolonged heat exposure)
    """
    for col in cols:
        for win in windows:
            df[f'{col}_rollmean{win}'] = df[col].rolling(win).mean()
            df[f'{col}_rollstd{win}'] = df[col].rolling(win).std()
    
    # std = volatility (stable weather vs. rapid changes)
    return df
```

**Provenance Tracking - Why?**
```python
# src/ingest.py
def write_provenance(df, source_file):
    """
    Scientific reproducibility requirement:
    - What data was used?
    - When was it processed?
    - What transformations were applied?
    
    Critical for audits and troubleshooting
    """
    metadata = {
        "source_file": source_file,
        "ingestion_timestamp": datetime.now().isoformat(),
        "row_count": len(df),
        "date_range": [df['date'].min(), df['date'].max()],
        "schema_version": "1.0.0"
    }
    with open('outputs/data_provenance.json', 'w') as f:
        json.dump(metadata, f, indent=2)
```

---

### Milestone 2: DLNM - Distributed Lag Non-Linear Models
**Goal**: Establish causal relationships (not just correlation)

**What is DLNM?**
Standard regression: "Is temperature related to admissions?"
DLNM: "How does temperature affect admissions over the next 14 days, and is the relationship linear or curved?"

**Why DLNM Matters:**
- **Delayed effects**: Heat exposure on Monday affects Tuesday, Wednesday...
- **Non-linearity**: 35°C isn't just "5 degrees hotter than 30°C"—it's exponentially worse
- **Causal inference**: Controls for confounders, establishes dose-response

**Technical Implementation:**

```r
# src/models/dlnm_r_script.R
# Why R? The 'dlnm' package is the gold standard (Gasparrini 2010)

# Create crossbasis - combines lag structure + non-linear response
cb_temp <- crossbasis(
  df$temp_mean_c,
  lag = 14,                    # Effects up to 14 days
  argvar = list(fun = "ns", df = 5),  # Natural spline with 5 knots
  arglag = list(fun = "ns", df = 4)   # Lag structure: 4 knots
)

# Why natural splines?
# - Flexible: can fit curves (not just straight lines)
# - Smooth: avoids overfitting
# - Constrained: sensible behavior at extremes

# Quasi-Poisson GLM
# Why quasi-Poisson? Admissions are counts (0, 1, 2...) not continuous
model <- glm(
  admissions ~ cb_temp + rel_humidity + day_of_week,
  family = quasipoisson,  # Handles overdispersion (variance > mean)
  data = df
)
```

**Python Fallback - Why?**
Not everyone has R installed. We need a pure-Python solution:

```python
# src/models/run_dlnm.py - Python fallback
def python_fallback():
    # Use statsmodels (Python's stats library)
    # Approximate DLNM with distributed lag blocks
    
    # Block 1: Lags 0-3 (immediate effects)
    df['temp_block1'] = df[[f'temp_mean_lag{i}' for i in range(0,4)]].mean(axis=1)
    
    # Block 2: Lags 4-7 (short-term delayed)
    df['temp_block2'] = df[[f'temp_mean_lag{i}' for i in range(4,8)]].mean(axis=1)
    
    # Why blocks? Simplifies from 22 lag terms to 4 terms
    # Trade-off: Less precise than R's crossbasis, but easier to fit
    
    # Use patsy for spline basis
    from patsy import dmatrix
    spline = dmatrix("bs(temp_mean, df=5, degree=3)", data=df)
    
    # Fit Quasi-Poisson GLM
    model = sm.GLM(y, X, family=sm.families.Poisson()).fit()
```

**Key Learning**: 
- R is preferred for canonical DLNM (better tools)
- Python fallback ensures accessibility
- Always have a backup plan for dependencies

---

### Milestone 3: XGBoost + SHAP Explainability
**Goal**: High-accuracy predictions + interpretability

**Why XGBoost?**
1. **Best for tabular data**: Consistently wins Kaggle competitions
2. **Handles non-linearity**: Captures complex temperature-admission curves
3. **Feature importance**: Built-in ranking of what matters
4. **Fast**: Trains in seconds, predicts in milliseconds

**Why Count:Poisson Objective?**
```python
XGBRegressor(
    objective='count:poisson',  # Key choice!
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05
)
```

**Why Poisson?**
- Admissions are counts: 0, 1, 2, 3... (discrete, not continuous)
- Can't have negative admissions (Poisson guarantees non-negative)
- Variance often scales with mean (Poisson property)

**Alternative objectives we rejected:**
- `reg:squarederror` - Assumes Gaussian (can predict -2 admissions!)
- `reg:gamma` - For continuous positive values (e.g., revenue)
- `count:poisson` ✅ - Perfect for count data

**Time-Based Split - Critical!**
```python
# WRONG: Random split (leaks future into past)
X_train, X_test = train_test_split(X, y, test_size=0.2, random_state=42)

# RIGHT: Chronological split (no time travel)
split_idx = int(len(df) * 0.8)
train = df.iloc[:split_idx]   # First 80% (older data)
test = df.iloc[split_idx:]     # Last 20% (recent data)
```

**Why this matters:** 
- Random split: Model sees future data during training (cheating!)
- Time split: Model only knows past when predicting future (realistic)

**SHAP - Making ML Interpretable**

**What is SHAP?**
"For this prediction of 12 admissions, temperature contributed +3, humidity -1, PM2.5 +2..."

```python
# src/explainers.py
import shap

# Why PermutationExplainer?
# TreeExplainer had compatibility issues with XGBoost 2.0.3
explainer = shap.Explainer(model.predict, X_sample)

# How it works:
# 1. Take a prediction: f(x) = 12
# 2. Remove one feature (set to baseline)
# 3. Measure change: f(x without temp) = 9
# 4. Attribution: temp contributed +3
# 5. Repeat for all features
```

**SHAP Outputs:**
1. **Summary Plot**: Global feature importance (all predictions)
2. **Dependence Plots**: How one feature affects predictions
3. **Force Plot**: Single prediction breakdown

**Key Learning**:
- XGBoost is powerful but a "black box"
- SHAP opens the box—crucial for clinical trust
- Always check compatibility (TreeExplainer vs PermutationExplainer)

---

### Milestone 4: Causal Integration & Policy Statements
**Goal**: Bridge ML predictions with policy recommendations

**Why This Matters:**
- Scientists want: Causal effect estimates (DLNM)
- Operators want: Accurate forecasts (XGBoost)
- Policy-makers want: "What should I do?"

**Causal Effect Estimation:**
```python
# src/models/model_utils.py
def estimate_causal_effect(df, exposure='temp_mean_c', outcome='admissions'):
    """
    Question: "What's the effect of a 5°C temperature increase?"
    
    Method: Stratified analysis with bootstrap confidence intervals
    """
    # Stratify by exposure level
    low_temp = df[df[exposure] < df[exposure].quantile(0.25)]
    high_temp = df[df[exposure] > df[exposure].quantile(0.75)]
    
    # Compare outcomes
    effect = high_temp[outcome].mean() - low_temp[outcome].mean()
    
    # Bootstrap for confidence interval (1000 resamples)
    bootstrap_effects = []
    for _ in range(1000):
        sample_low = low_temp.sample(frac=1, replace=True)
        sample_high = high_temp.sample(frac=1, replace=True)
        boot_effect = sample_high[outcome].mean() - sample_low[outcome].mean()
        bootstrap_effects.append(boot_effect)
    
    # 95% CI = 2.5th to 97.5th percentile
    ci_lower = np.percentile(bootstrap_effects, 2.5)
    ci_upper = np.percentile(bootstrap_effects, 97.5)
    
    return effect, (ci_lower, ci_upper)
```

**Policy Statement Generation:**
```python
# src/models/produce_policy_statement.py
def generate_policy_statement(shap_values, causal_estimates):
    """
    Combines:
    1. SHAP findings (what drives predictions)
    2. Causal estimates (magnitude of effects)
    3. Plain language (for non-technical readers)
    """
    statement = f"""
    EXECUTIVE SUMMARY
    
    High temperature days (>30°C) are associated with 
    {causal_estimates['effect']:.1f} additional cardiovascular 
    admissions (95% CI: {causal_estimates['ci'][0]:.1f} to 
    {causal_estimates['ci'][1]:.1f}).
    
    KEY DRIVERS (from ML model):
    1. {shap_values['top_features'][0]}: {shap_values['contributions'][0]:.2f} impact
    2. {shap_values['top_features'][1]}: {shap_values['contributions'][1]:.2f} impact
    
    RECOMMENDATIONS:
    - Activate heat-health warning system when forecast >30°C
    - Increase cardiovascular unit staffing during heat waves
    - Target vulnerable populations (elderly, chronic conditions)
    """
    return statement
```

**Key Learning:**
- Scientific rigor (causal inference) + operational utility (predictions)
- Bootstrap = simple but powerful uncertainty quantification
- Policy statements bridge technical → actionable

---

### Milestone 5: Visualizations
**Goal**: Make insights accessible to diverse audiences

**Risk Calendar - Why?**
Shows daily risk across an entire year at a glance

```python
# src/viz.py
def create_risk_calendar(df):
    """
    Heatmap: rows=weeks, columns=days of week
    Color intensity = admission count
    
    Why this format?
    - Human-readable: "Week 23 had a spike"
    - Patterns visible: "Mondays are always higher"
    - Anomalies obvious: "What happened that week?"
    """
    df['week'] = df['date'].dt.isocalendar().week
    df['dayofweek'] = df['date'].dt.dayofweek
    
    # Pivot to grid format
    grid = df.pivot(index='week', columns='dayofweek', values='admissions')
    
    # Heatmap
    sns.heatmap(grid, cmap='YlOrRd', annot=False)
    plt.title('Daily Cardiovascular Admissions Risk Calendar')
```

**Threshold Curves - Why?**
Shows non-linear relationship between temperature and risk

```python
def create_threshold_curves(df, model):
    """
    X-axis: Temperature (10°C to 40°C)
    Y-axis: Predicted admissions
    Shaded area: 95% confidence interval
    
    Why non-linear?
    - 15°C → 20°C: Small increase
    - 30°C → 35°C: Exponential increase (heat stress threshold)
    """
    temps = np.linspace(10, 40, 100)
    predictions = []
    ci_lower = []
    ci_upper = []
    
    for temp in temps:
        # Predict with temp varied, other features at median
        features = baseline_features.copy()
        features['temp_mean_c'] = temp
        pred = model.predict([features])[0]
        predictions.append(pred)
        
        # Bootstrap CI (run prediction 100 times with resampled data)
        # ... (simplified for readability)
    
    plt.plot(temps, predictions, label='Predicted Admissions')
    plt.fill_between(temps, ci_lower, ci_upper, alpha=0.3, label='95% CI')
    plt.axvline(30, color='red', linestyle='--', label='High Risk Threshold')
```

**Spatial Risk Map - Why?**
Interactive map for geographic context (future: multi-region support)

```python
import folium

def create_spatial_risk_map(df):
    """
    Why folium?
    - Interactive (zoom, pan, click)
    - HTML output (embed in dashboards)
    - Easy integration with Streamlit
    """
    center_lat, center_lon = 40.7128, -74.0060  # Example: NYC
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    # Add circle marker
    risk_level = df['admissions'].mean()
    folium.CircleMarker(
        location=[center_lat, center_lon],
        radius=20,
        popup=f"Mean Risk: {risk_level:.1f}",
        color='red' if risk_level > 10 else 'orange',
        fill=True
    ).add_to(m)
    
    m.save('outputs/spatial_risk_map.html')
```

**Key Learning:**
- Different stakeholders need different visualizations
- Calendars: Operations teams planning staff
- Curves: Scientists understanding dose-response
- Maps: Public health officials targeting interventions

---

### Milestone 6: API + Dashboard
**Goal**: Make system accessible to end-users

**FastAPI - Why?**
```python
# src/api/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Climate-CVD Risk Prediction API",
    description="Predicts daily cardiovascular admissions",
    version="1.0.0"
)

# Why FastAPI over Flask?
# 1. Automatic OpenAPI docs (http://localhost:8000/docs)
# 2. Type validation (Pydantic)
# 3. Async support (handle multiple requests)
# 4. Fast (built on Starlette/Uvicorn)
```

**Pydantic Schemas - Why?**
```python
# src/api/schemas.py
from pydantic import BaseModel, Field
from datetime import date as date_type

class ForecastDay(BaseModel):
    """
    Why Pydantic?
    - Automatic validation (temp must be float)
    - Clear error messages ("temp_mean_c is required")
    - Documentation generation (appears in /docs)
    """
    date: date_type
    temp_mean_c: float = Field(..., ge=-50, le=60, description="Mean temperature (°C)")
    relative_humidity_pct: float = Field(..., ge=0, le=100)
    pm25_ugm3: float = Field(..., ge=0, description="PM2.5 concentration")
    
    # Field validation happens automatically!
    # Request with temp_mean_c=150 → automatic 422 error
```

**Health Check Endpoint - Why?**
```python
@app.get("/health")
def health_check():
    """
    Why needed?
    - Load balancers use this to detect dead servers
    - Monitoring systems check every 30 seconds
    - Quick way to verify model is loaded
    
    Returns:
    - Status: ok/degraded/error
    - Model loaded: true/false
    - Performance metrics: MAE, R²
    """
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_metrics": {
            "test_mae": 0.897,
            "test_r2": 0.903
        }
    }
```

**Predict Endpoint - Design Choices:**
```python
@app.post("/predict")
def predict(request: PredictRequest):
    """
    Why POST not GET?
    - GET: Simple queries (no body)
    - POST: Complex data (forecast array)
    
    Why return SHAP drivers?
    - User sees: "Tomorrow: 12 admissions"
    - User wants: "Why 12? What's driving it?"
    - We return: Top 5 contributing features
    """
    # Load forecast data
    forecast_days = request.forecast
    
    # Build feature matrix
    X = prepare_features(forecast_days)  # Add lags, rolling stats
    
    # Predict
    predictions = model.predict(X)
    
    # Explain (SHAP)
    shap_values = explainer(X)
    top_drivers = get_top_features(shap_values, n=5)
    
    return {
        "predictions": predictions.tolist(),
        "drivers": top_drivers,  # Key addition!
        "forecast_date": datetime.now()
    }
```

**Alert Endpoint - Threshold Logic:**
```python
@app.post("/alert")
def check_alert(request: AlertRequest):
    """
    Trigger alerts when thresholds exceeded
    
    Why thresholds?
    - Binary decision: activate response or not
    - Calculated from historical 90th percentile
    - Adjustable per region/season
    """
    HIGH_TEMP = 30.0  # °C (90th percentile)
    HIGH_PM25 = 50.0  # µg/m³ (EPA "Unhealthy")
    HIGH_ADMISSIONS = 10.0  # Count (historical)
    
    alert_triggered = (
        request.temp_mean_c > HIGH_TEMP or
        request.pm25_ugm3 > HIGH_PM25 or
        request.predicted_admissions > HIGH_ADMISSIONS
    )
    
    recommendations = []
    if request.temp_mean_c > HIGH_TEMP:
        recommendations.append("Activate heat-health warning system")
    if request.pm25_ugm3 > HIGH_PM25:
        recommendations.append("Issue air quality alert")
    
    return {
        "alert": alert_triggered,
        "risk_level": "high" if alert_triggered else "moderate",
        "recommendations": recommendations
    }
```

**Streamlit Dashboard - Why?**
```python
# src/dashboard/app.py
import streamlit as st

# Why Streamlit?
# - Python-only (no HTML/CSS/JavaScript needed)
# - Automatic reactivity (change input → plot updates)
# - Built-in widgets (sliders, date pickers)
# - Fast prototyping (dashboard in 100 lines)

# Page structure
pages = ["Overview", "Risk Calendar", "Model Explainability", "Forecast", "Policy"]
page = st.sidebar.selectbox("Navigate", pages)

if page == "Overview":
    st.title("Climate-CVD Risk System")
    st.metric("Model R²", "0.903")
    st.metric("MAE", "0.897 admissions")
    
elif page == "Forecast":
    # Interactive input form
    st.subheader("Enter Forecast Data")
    temp = st.slider("Temperature (°C)", 0, 45, 25)
    humidity = st.slider("Humidity (%)", 0, 100, 60)
    pm25 = st.number_input("PM2.5 (µg/m³)", 0, 200, 30)
    
    if st.button("Predict"):
        # Call API
        response = requests.post("http://localhost:8000/predict", json={...})
        prediction = response.json()["predictions"][0]
        st.success(f"Predicted Admissions: {prediction:.1f}")
```

**Key Learning:**
- APIs need health checks, validation, documentation
- SHAP values in API responses = transparency
- Streamlit = rapid dashboard development
- Always return confidence intervals, not just point estimates

---

### Milestone 7: Production Packaging
**Goal**: Make deployment reproducible and maintainable

**Docker - Why?**
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Why slim? Base python:3.11 is 1GB, slim is 150MB
# Trade-off: Need to manually install system libs

# Install system dependencies (for geopandas)
RUN apt-get update && apt-get install -y \
    gcc g++ \                      # Compilers
    libgdal-dev libgeos-dev \      # Geospatial libraries
    libproj-dev \                  # Coordinate projections
    && rm -rf /var/lib/apt/lists/*  # Clean up (reduce image size)

# Why delete apt lists? Saves 50MB in final image

# Copy requirements first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Why --no-cache-dir? Saves 200MB (pip cache not needed in container)

# Copy application code
COPY . /app
WORKDIR /app

# Generate synthetic data at build time
RUN python data_synthetic/generate_synthetic.py
RUN python src/preprocess.py

# Why at build? Faster container startup (data already there)

# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**.dockerignore - Why?**
```
# .dockerignore
__pycache__/
*.pyc
.git/
.venv/
*.egg-info/

# Why ignore?
# - Reduces build context size (faster uploads to Docker daemon)
# - Prevents local dev files from entering production image
# - Smaller image = faster deployment
```

**GitHub Actions CI/CD - Why?**
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

# Why run on push + PR?
# - Push: Catch breaking changes immediately
# - PR: Block merges if tests fail

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    # Why cache dependencies? Speeds up builds (don't reinstall every time)
    - name: Cache pip
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Lint (flake8)
      run: flake8 src/ tests/ --max-line-length=100
    
    # Why lint? Catches syntax errors, style violations
    
    - name: Format check (black)
      run: black src/ tests/ --check
    
    # Why black? Consistent code style across team
    
    - name: Run tests
      run: pytest tests/ -v --cov=src --cov-report=term
    
    # Why coverage? Identify untested code paths
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: test-reports
        path: |
          outputs/
          htmlcov/
    
  docker:
    runs-on: ubuntu-latest
    needs: test  # Only build Docker if tests pass
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t explainable-ai-cvd:${{ github.sha }} .
    
    # Why tag with commit SHA? Unique identifier for each build
    
    - name: Test Docker image
      run: |
        docker run explainable-ai-cvd:${{ github.sha }} python --version
        docker run explainable-ai-cvd:${{ github.sha }} ls outputs/
    
    # Why test image? Verify data generation happened during build
```

**Key Learning:**
- Docker = "works on my machine" → "works everywhere"
- CI/CD = automated quality gates (can't merge broken code)
- Layer caching = faster builds
- Artifacts = preserve test outputs for debugging

---

## Technical Decisions and Rationale

### Why Python 3.11?
- **Type hints**: Better than 3.10 (PEP 673, 675, 681)
- **Performance**: 10-60% faster than 3.10 (PEP 659)
- **Compatibility**: All major libraries support it
- **Future-proof**: Active development for 3+ years

### Why XGBoost over LightGBM/CatBoost?
| Feature | XGBoost | LightGBM | CatBoost |
|---------|---------|----------|----------|
| Speed   | ⭐⭐⭐     | ⭐⭐⭐⭐    | ⭐⭐      |
| Accuracy| ⭐⭐⭐⭐   | ⭐⭐⭐     | ⭐⭐⭐⭐   |
| Documentation | ⭐⭐⭐⭐ | ⭐⭐⭐   | ⭐⭐      |
| Poisson support | ✅ | ✅ | ❌ |

**Verdict**: XGBoost for count:poisson + mature ecosystem

### Why Parquet over CSV?
```python
# Size comparison
CSV:     10 MB (text, uncompressed)
Parquet: 2 MB (binary, columnar, compressed)

# Speed comparison (1M rows)
CSV read:    5.2 seconds
Parquet read: 0.8 seconds (6.5x faster!)

# Why?
# Parquet stores by column (good for analytics)
# CSV stores by row (good for... nothing really)
```

### Why FastAPI over Flask?
```python
# Flask (old school)
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()  # No validation!
    temp = data.get('temp')    # Could be None, string, anything
    # Manual validation code here...

# FastAPI (modern)
@app.post('/predict')
def predict(request: PredictRequest):  # Automatic validation!
    temp = request.temp_mean_c  # Guaranteed to be float
    # Just use it!
```

### Why Streamlit over Dash/Plotly?
- **Simplicity**: 10 lines of code for a dashboard
- **Python-only**: No HTML/CSS/JavaScript
- **Rapid iteration**: Change code → auto-refresh
- **Built-in components**: Sliders, file uploaders, etc.

---

## Code Architecture

### Directory Structure Rationale
```
ExplainableAIforHealth/
├── data_synthetic/     # Synthetic data (gitignored in production)
├── data_processed/     # Output of preprocessing (gitignored)
├── outputs/            # Model artifacts (gitignored, too large)
├── src/                # Source code (version controlled)
│   ├── api/           # REST API (isolated for microservices)
│   ├── dashboard/     # Streamlit app (isolated for deployment)
│   ├── models/        # Training scripts (reusable modules)
│   ├── ingest.py      # Data validation (single responsibility)
│   ├── features.py    # Feature engineering (pure functions)
│   ├── preprocess.py  # Pipeline orchestration (main entry point)
│   ├── explainers.py  # SHAP analysis (separated from training)
│   └── viz.py         # Visualizations (matplotlib/seaborn)
├── tests/             # Unit tests (mirror src/ structure)
├── docs/              # Documentation (Markdown)
├── .github/workflows/ # CI/CD (version controlled)
├── Dockerfile         # Container definition
├── requirements.txt   # Dependencies
├── Makefile          # Automation commands
└── README.md         # Entry point documentation
```

**Why this structure?**
- **Separation of concerns**: API, dashboard, models isolated
- **Testability**: Each module has unit tests
- **Reusability**: `features.py` functions used by both training and API
- **Deployment**: Can deploy API without dashboard (microservices)

### Design Patterns Used

**1. Pipeline Pattern (preprocess.py)**
```python
def preprocess():
    df = ingest()          # Step 1: Load
    df = add_lags(df)      # Step 2: Lags
    df = add_rolling(df)   # Step 3: Rolling
    df = add_derived(df)   # Step 4: Derived
    save(df)               # Step 5: Save
    return df

# Why? Clear flow, easy to debug (inspect after each step)
```

**2. Factory Pattern (model loading)**
```python
def load_model(model_type='xgboost'):
    """Load different models without changing API"""
    if model_type == 'xgboost':
        return joblib.load('xgb_model.joblib')
    elif model_type == 'lightgbm':
        return joblib.load('lgb_model.joblib')
    # Easy to extend!
```

**3. Singleton Pattern (API startup)**
```python
# Global state loaded once
model = None

@app.on_event("startup")
def load_artifacts():
    global model
    model = joblib.load('xgb_model.joblib')  # Load once, reuse for all requests
```

**4. Strategy Pattern (DLNM fallback)**
```python
def run_dlnm():
    if r_available():
        run_r_version()      # Strategy 1: R canonical
    else:
        python_fallback()    # Strategy 2: Python approximation
```

---

## Summary

### What Makes This Production-Ready?
1. **Testing**: 18 unit tests covering all critical paths
2. **Monitoring**: Health checks, logging, error handling
3. **Documentation**: Model card, datasheet, handover guide
4. **Deployment**: Docker, CI/CD, versioned releases
5. **Explainability**: SHAP, policy statements, visualizations
6. **Reproducibility**: Deterministic data, provenance tracking
7. **Maintainability**: Clear structure, type hints, docstrings

### What Would You Do Differently in Production?
1. **Real data**: Replace synthetic with actual hospital records
2. **Database**: Add PostgreSQL for prediction history
3. **Authentication**: API keys, OAuth2
4. **Scaling**: Kubernetes, load balancing
5. **Monitoring**: Prometheus, Grafana dashboards
6. **Alerts**: Email/SMS notifications
7. **Multi-region**: Train separate models per geography
8. **A/B testing**: Compare model versions in production

### Key Takeaways
- **Start simple**: Synthetic data → real data
- **Test early**: TDD prevents rework
- **Document always**: Future you will thank you
- **Plan for failure**: Fallbacks, error handling
- **Think users**: API docs, dashboards, policy briefs
- **Automate everything**: Makefile, Docker, CI/CD

---

**Next**: Read `02-problems-and-solutions.md` for detailed troubleshooting guide
