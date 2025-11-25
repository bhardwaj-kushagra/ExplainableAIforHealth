# Technical Architecture - How Everything Fits Together

## Table of Contents
1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Model Pipeline](#model-pipeline)
5. [API Design](#api-design)
6. [Dashboard Architecture](#dashboard-architecture)
7. [Deployment Architecture](#deployment-architecture)
8. [Scaling Considerations](#scaling-considerations)
9. [Monitoring and Observability](#monitoring-and-observability)
10. [Security Architecture](#security-architecture)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   Web Browser    │              │  API Clients     │        │
│  │                  │              │  (curl, Python)  │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                  │                   │
│           │ HTTP                             │ HTTP/JSON        │
│           ▼                                  ▼                   │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │  Streamlit       │────HTTP──────│   FastAPI        │        │
│  │  Dashboard       │              │   REST API       │        │
│  │  (Port 8501)     │              │   (Port 8000)    │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                  │                   │
└───────────┼──────────────────────────────────┼───────────────────┘
            │                                  │
            │                                  │
┌───────────┼──────────────────────────────────┼───────────────────┐
│           │      Application Logic Layer    │                   │
├───────────┼──────────────────────────────────┼───────────────────┤
│           │                                  │                   │
│           ▼                                  ▼                   │
│  ┌─────────────────────────────────────────────────┐           │
│  │            Model Artifacts Manager               │           │
│  │  ┌───────────┐  ┌───────────┐  ┌──────────┐   │           │
│  │  │  XGBoost  │  │   DLNM    │  │ Baseline │   │           │
│  │  │   Model   │  │   Model   │  │   Data   │   │           │
│  │  └───────────┘  └───────────┘  └──────────┘   │           │
│  └─────────────────────────────────────────────────┘           │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────┐           │
│  │         Feature Engineering Pipeline             │           │
│  │  - Lag features                                  │           │
│  │  - Rolling means                                 │           │
│  │  - Temporal features                             │           │
│  └─────────────────────────────────────────────────┘           │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            │
┌───────────────────────────┼──────────────────────────────────────┐
│                           │      Data Layer                      │
├───────────────────────────┼──────────────────────────────────────┤
│                           ▼                                      │
│  ┌──────────────────┐   ┌──────────────────┐                   │
│  │  Synthetic Data  │   │  Preprocessed    │                   │
│  │  Generator       │───│  Features        │                   │
│  │  (.py script)    │   │  (.csv)          │                   │
│  └──────────────────┘   └──────────────────┘                   │
│                                                                   │
│  ┌──────────────────────────────────────────────────┐          │
│  │         Model Artifacts (outputs/)               │          │
│  │  - xgb_model.joblib                              │          │
│  │  - dlnm_model.joblib                             │          │
│  │  - baseline_data.joblib                          │          │
│  │  - feature_names.joblib                          │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Streamlit | Interactive dashboard |
| **API** | FastAPI | REST API endpoints |
| **Models** | XGBoost, DLNM | Prediction and risk analysis |
| **Explainability** | SHAP | Model interpretability |
| **Visualization** | Plotly, Folium | Interactive charts and maps |
| **Data** | pandas, NumPy | Data processing |
| **Server** | Uvicorn | ASGI server |
| **Containerization** | Docker | Deployment packaging |
| **CI/CD** | GitHub Actions | Automated testing and deployment |
| **Testing** | pytest | Unit and integration tests |

---

## Component Architecture

### 1. Data Generation Module

**Location**: `data_synthetic/generate_synthetic.py`

```
┌─────────────────────────────────────────┐
│     Synthetic Data Generator            │
├─────────────────────────────────────────┤
│                                         │
│  Input: Configuration                   │
│  - n_years = 4                          │
│  - n_regions = 3                        │
│  - seasonal patterns                    │
│                                         │
│  Process:                               │
│  1. Generate dates (2020-2024)         │
│  2. Simulate climate variables          │
│     - Temperature (seasonal)            │
│     - Humidity (correlated)             │
│     - PM2.5 (pollution)                 │
│  3. Simulate CVD admissions             │
│     - Poisson distribution              │
│     - Temperature effects               │
│     - Humidity effects                  │
│     - Day-of-week effects               │
│  4. Add realistic noise                 │
│                                         │
│  Output: synthetic_data.csv             │
│  - date, region_id, temp, humidity,    │
│    pm25, cvd_admissions                 │
│                                         │
└─────────────────────────────────────────┘
```

**Why Synthetic?**
- No real patient data (privacy/ethics)
- Control over relationships (known ground truth)
- Reproducible (same seed = same data)
- Educational (demonstrates concepts)

### 2. Preprocessing Module

**Location**: `src/preprocess.py`

```
┌────────────────────────────────────────────────────────┐
│              Feature Engineering Pipeline               │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Input: synthetic_data.csv                             │
│                                                         │
│  Step 1: Temporal Features                             │
│  ┌────────────────────────────────────┐               │
│  │ - day_of_week (0-6)                │               │
│  │ - month (1-12)                     │               │
│  │ - day_of_year (1-365)              │               │
│  │ - is_weekend (binary)              │               │
│  │ - season (winter, spring, ...)     │               │
│  └────────────────────────────────────┘               │
│                                                         │
│  Step 2: Lag Features (Historical Values)              │
│  ┌────────────────────────────────────┐               │
│  │ - temp_mean_c_lag1 (yesterday)     │               │
│  │ - temp_mean_c_lag2 (2 days ago)    │               │
│  │ - temp_mean_c_lag3                 │               │
│  │ - temp_mean_c_lag7 (last week)     │               │
│  │ - ... (same for humidity, pm25)    │               │
│  └────────────────────────────────────┘               │
│                                                         │
│  Step 3: Rolling Statistics (Moving Windows)           │
│  ┌────────────────────────────────────┐               │
│  │ - temp_mean_c_roll3 (3-day avg)    │               │
│  │ - temp_mean_c_roll7 (week avg)     │               │
│  │ - temp_mean_c_roll14 (2-week avg)  │               │
│  │ - ... (for all climate vars)       │               │
│  └────────────────────────────────────┘               │
│                                                         │
│  Step 4: Interaction Features                          │
│  ┌────────────────────────────────────┐               │
│  │ - temp_x_humidity                  │               │
│  │ - temp_range_7d                    │               │
│  │ - pm25_spike (sudden increase)     │               │
│  └────────────────────────────────────┘               │
│                                                         │
│  Output: preprocessed_features.csv                     │
│  - Original columns (10)                               │
│  - Engineered features (50+)                           │
│  - Total: ~60 columns                                  │
│                                                         │
└────────────────────────────────────────────────────────┘
```

**Design Patterns**:
- **Pipeline Pattern**: Sequential transformations
- **Factory Pattern**: Different lag/rolling window configs
- **Single Responsibility**: Each function does one thing

### 3. DLNM Model Module

**Location**: `src/models/dlnm_fit.py`

```
┌──────────────────────────────────────────────────────┐
│    Distributed Lag Non-linear Model (DLNM)          │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Purpose: Capture delayed non-linear effects         │
│                                                       │
│  Example:                                            │
│  Today's heat → CVD admissions increase over         │
│  next 0-3 days (cumulative effect)                   │
│                                                       │
│  Input:                                              │
│  - date, region_id                                   │
│  - temp_mean_c                                       │
│  - relative_humidity_pct                             │
│  - cvd_admissions                                    │
│                                                       │
│  Model Specification:                                │
│  ┌─────────────────────────────────────┐            │
│  │ admissions ~ cr(temp, df=4, lag=3)  │            │
│  │            + cr(humid, df=4, lag=3) │            │
│  │            + C(dow) + C(month)      │            │
│  └─────────────────────────────────────┘            │
│                                                       │
│  Components:                                         │
│  - cr(): Cubic regression spline (non-linear)        │
│  - df=4: 4 degrees of freedom (flexibility)          │
│  - lag=3: Effects up to 3 days                       │
│  - C(): Categorical variables                        │
│                                                       │
│  Output:                                             │
│  ┌─────────────────────────────────────┐            │
│  │ 1. dlnm_model.joblib (fitted model) │            │
│  │ 2. Coefficients and predictions     │            │
│  │ 3. Lag-response curves (plots)      │            │
│  └─────────────────────────────────────┘            │
│                                                       │
│  Interpretation:                                     │
│  "30°C on Day 0 → +2.3 admissions on Day 1"         │
│  "Cumulative effect over 3 days: +5.7 admissions"   │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 4. XGBoost Model Module

**Location**: `src/models/xgb_train.py`

```
┌──────────────────────────────────────────────────────────┐
│              XGBoost Training Pipeline                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Input: preprocessed_features.csv (60+ features)         │
│                                                           │
│  Step 1: Train/Test Split                                │
│  ┌───────────────────────────────────────┐              │
│  │ 80% training (2020-2023)              │              │
│  │ 20% testing (2024)                    │              │
│  │ Temporal split (not random!)          │              │
│  └───────────────────────────────────────┘              │
│                                                           │
│  Step 2: XGBoost Configuration                           │
│  ┌───────────────────────────────────────┐              │
│  │ objective = 'count:poisson'           │ Count data   │
│  │ max_depth = 5                         │ Tree depth   │
│  │ learning_rate = 0.05                  │ Slow learn   │
│  │ n_estimators = 200                    │ 200 trees    │
│  │ subsample = 0.8                       │ 80% data     │
│  │ colsample_bytree = 0.8                │ 80% features │
│  │ eval_metric = 'poisson-nloglik'       │ Loss metric  │
│  │ early_stopping_rounds = 20            │ Prevent overfit│
│  └───────────────────────────────────────┘              │
│                                                           │
│  Step 3: Training                                        │
│  ┌───────────────────────────────────────┐              │
│  │ Fit on training data                  │              │
│  │ Validate on 20% of training (CV)      │              │
│  │ Early stop if no improvement          │              │
│  └───────────────────────────────────────┘              │
│                                                           │
│  Step 4: Evaluation                                      │
│  ┌───────────────────────────────────────┐              │
│  │ Test R² = 0.903                       │ 90.3% var    │
│  │ Test MAE = 0.897                      │ ±0.9 admits  │
│  │ Test RMSE = 1.201                     │              │
│  └───────────────────────────────────────┘              │
│                                                           │
│  Step 5: Feature Importance (SHAP)                       │
│  ┌───────────────────────────────────────┐              │
│  │ Calculate SHAP values                 │              │
│  │ Top features:                         │              │
│  │  1. temp_mean_c_lag1 (yesterday)      │              │
│  │  2. temp_mean_c_roll7 (week avg)      │              │
│  │  3. day_of_week                       │              │
│  │  4. temp_mean_c (today)               │              │
│  │  5. relative_humidity_pct_lag1        │              │
│  └───────────────────────────────────────┘              │
│                                                           │
│  Output:                                                 │
│  ┌───────────────────────────────────────┐              │
│  │ xgb_model.joblib (trained model)      │              │
│  │ feature_names.joblib (column order)   │              │
│  │ baseline_data.joblib (SHAP baseline)  │              │
│  │ shap_values.npy (explanations)        │              │
│  │ Plots: importance, predictions        │              │
│  └───────────────────────────────────────┘              │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 5. API Module

**Location**: `src/api/main.py`

```
┌────────────────────────────────────────────────────────┐
│                 FastAPI Application                     │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Initialization (Startup Event)                        │
│  ┌──────────────────────────────────────┐             │
│  │ @app.on_event("startup")             │             │
│  │ def load_artifacts():                │             │
│  │   - Load xgb_model.joblib            │             │
│  │   - Load dlnm_model.joblib           │             │
│  │   - Load baseline_data.joblib        │             │
│  │   - Load feature_names.joblib        │             │
│  │   - Validate all loaded              │             │
│  └──────────────────────────────────────┘             │
│                                                         │
│  Endpoints:                                            │
│                                                         │
│  1. GET /health                                        │
│  ┌──────────────────────────────────────┐             │
│  │ Purpose: Health check                │             │
│  │ Returns:                             │             │
│  │  - status: "ok"                      │             │
│  │  - model_loaded: true                │             │
│  │  - version: "1.0.0"                  │             │
│  └──────────────────────────────────────┘             │
│                                                         │
│  2. POST /predict                                      │
│  ┌──────────────────────────────────────┐             │
│  │ Purpose: Get CVD predictions         │             │
│  │ Input (JSON):                        │             │
│  │  {                                   │             │
│  │    "region_id": "R1",                │             │
│  │    "forecast": [                     │             │
│  │      {                               │             │
│  │        "date": "2025-11-25",         │             │
│  │        "temp_mean_c": 28.5,          │             │
│  │        "relative_humidity_pct": 65,  │             │
│  │        "pm25_ugm3": 42.0             │             │
│  │      }                               │             │
│  │    ]                                 │             │
│  │  }                                   │             │
│  │                                      │             │
│  │ Process:                             │             │
│  │ 1. Validate request (Pydantic)       │             │
│  │ 2. Build feature DataFrame           │             │
│  │ 3. Add temporal features             │             │
│  │ 4. Add lag features (from history)   │             │
│  │ 5. Align to model's expected columns │             │
│  │ 6. XGBoost prediction                │             │
│  │ 7. SHAP explanation                  │             │
│  │                                      │             │
│  │ Output (JSON):                       │             │
│  │  {                                   │             │
│  │    "region_id": "R1",                │             │
│  │    "predictions": [12.5, 13.1],      │             │
│  │    "shap_values": [...],             │             │
│  │    "baseline": 11.2                  │             │
│  │  }                                   │             │
│  └──────────────────────────────────────┘             │
│                                                         │
│  3. POST /explain                                      │
│  ┌──────────────────────────────────────┐             │
│  │ Purpose: Detailed SHAP explanation   │             │
│  │ Similar to /predict but returns:     │             │
│  │  - SHAP values per feature           │             │
│  │  - Feature contributions             │             │
│  │  - Waterfall plot data               │             │
│  └──────────────────────────────────────┘             │
│                                                         │
│  Error Handling:                                       │
│  ┌──────────────────────────────────────┐             │
│  │ - Pydantic validation errors → 422   │             │
│  │ - Missing required fields → 400      │             │
│  │ - Model not loaded → 503             │             │
│  │ - Prediction errors → 500            │             │
│  │ - All errors logged with traceback   │             │
│  └──────────────────────────────────────┘             │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### 6. Dashboard Module

**Location**: `src/dashboard/app.py`

```
┌──────────────────────────────────────────────────────────┐
│              Streamlit Dashboard                         │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Layout: Sidebar + Main Area                             │
│                                                           │
│  Sidebar:                                                │
│  ┌────────────────────────────────────┐                 │
│  │ Inputs:                            │                 │
│  │ - Region: R1, R2, R3 (selectbox)   │                 │
│  │ - Date: calendar picker            │                 │
│  │ - Temperature: slider (0-45°C)     │                 │
│  │ - Humidity: slider (0-100%)        │                 │
│  │ - PM2.5: slider (0-200 µg/m³)      │                 │
│  │ - [Get Prediction] button          │                 │
│  └────────────────────────────────────┘                 │
│                                                           │
│  Main Area:                                              │
│                                                           │
│  Tab 1: Predictions                                      │
│  ┌────────────────────────────────────┐                 │
│  │ Metric Cards:                      │                 │
│  │  ┌──────────────────────────┐      │                 │
│  │  │ Predicted Admissions     │      │                 │
│  │  │      12.5 ± 0.9         │      │                 │
│  │  └──────────────────────────┘      │                 │
│  │                                    │                 │
│  │ Time Series Plot:                  │                 │
│  │  - Historical admissions           │                 │
│  │  - Predicted admissions            │                 │
│  │  - Confidence interval             │                 │
│  │                                    │                 │
│  │ SHAP Waterfall Plot:               │                 │
│  │  - Base value: 11.2                │                 │
│  │  + temp_lag1: +0.8                 │                 │
│  │  + temp_roll7: +0.5                │                 │
│  │  - humidity: -0.1                  │                 │
│  │  = Prediction: 12.5                │                 │
│  └────────────────────────────────────┘                 │
│                                                           │
│  Tab 2: Risk Heatmap                                     │
│  ┌────────────────────────────────────┐                 │
│  │ 2D Heatmap:                        │                 │
│  │  X-axis: Temperature (0-45°C)      │                 │
│  │  Y-axis: Humidity (0-100%)         │                 │
│  │  Color: Predicted admissions       │                 │
│  │                                    │                 │
│  │ Contour lines for risk zones:      │                 │
│  │  - Green: < 10 (low)               │                 │
│  │  - Yellow: 10-15 (moderate)        │                 │
│  │  - Orange: 15-20 (high)            │                 │
│  │  - Red: > 20 (very high)           │                 │
│  └────────────────────────────────────┘                 │
│                                                           │
│  Tab 3: Regional Map                                     │
│  ┌────────────────────────────────────┐                 │
│  │ Interactive Folium Map:            │                 │
│  │  - Region markers (R1, R2, R3)     │                 │
│  │  - Color by risk level             │                 │
│  │  - Popup: predicted admissions     │                 │
│  │  - Zoom/pan enabled                │                 │
│  └────────────────────────────────────┘                 │
│                                                           │
│  Tab 4: DLNM Analysis                                    │
│  ┌────────────────────────────────────┐                 │
│  │ Lag-Response Curves:               │                 │
│  │  - Temperature effect over time    │                 │
│  │  - Humidity effect over time       │                 │
│  │  - Cumulative effects              │                 │
│  │  - Confidence bands                │                 │
│  └────────────────────────────────────┘                 │
│                                                           │
│  Data Flow:                                              │
│  User Input → Validate → Call API → Parse Response      │
│            → Update Visualizations → Display Results     │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## Data Flow

### End-to-End Data Journey

```
1. Data Generation
   ├─ generate_synthetic.py
   ├─ Creates: synthetic_data.csv
   └─ Format: date, region, climate, admissions

2. Preprocessing
   ├─ src/preprocess.py
   ├─ Loads: synthetic_data.csv
   ├─ Adds: 50+ engineered features
   └─ Creates: preprocessed_features.csv

3. Model Training
   ├─ DLNM (dlnm_fit.py)
   │  ├─ Loads: synthetic_data.csv (raw)
   │  ├─ Fits: lag-response models
   │  └─ Saves: dlnm_model.joblib
   │
   └─ XGBoost (xgb_train.py)
      ├─ Loads: preprocessed_features.csv
      ├─ Splits: 80/20 train/test
      ├─ Trains: gradient boosted trees
      ├─ Computes: SHAP values
      └─ Saves: xgb_model.joblib, baseline_data.joblib

4. API Serving
   ├─ src/api/main.py
   ├─ Startup: Load all models (once)
   ├─ Request: JSON with climate data
   ├─ Processing:
   │  ├─ Build DataFrame from JSON
   │  ├─ Add temporal features
   │  ├─ Align to model features
   │  ├─ Predict with XGBoost
   │  └─ Explain with SHAP
   └─ Response: JSON with predictions + explanations

5. Dashboard Visualization
   ├─ src/dashboard/app.py
   ├─ User Input: Sliders, dropdowns
   ├─ HTTP POST: To FastAPI /predict
   ├─ Parse Response: JSON → DataFrames
   └─ Visualize: Plotly charts, Folium maps

6. User Interaction
   └─ Web Browser (http://localhost:8501)
      └─ Sees results in real-time
```

### Data Transformations

```python
# Raw Data (synthetic_data.csv)
date       | region_id | temp_mean_c | humidity | pm25 | cvd_admissions
2020-01-01 | R1        | 15.2        | 62       | 38   | 12
2020-01-02 | R1        | 16.1        | 58       | 42   | 13

# ↓ Preprocessing

# Engineered Features (preprocessed_features.csv)
date       | region | temp | humidity | ... | temp_lag1 | temp_roll7 | dow | month | admissions
2020-01-01 | R1     | 15.2 | 62       | ... | NaN       | NaN        | 2   | 1     | 12
2020-01-02 | R1     | 16.1 | 58       | ... | 15.2      | 15.65      | 3   | 1     | 13
# (+50 more columns)

# ↓ Model Training

# XGBoost Internal Representation
# DMatrix (sparse matrix)
# Features: [temp_lag1=15.2, temp_roll7=15.65, dow=3, ...]
# Label: 13

# ↓ Prediction

# API Request (JSON)
{
  "region_id": "R1",
  "forecast": [
    {"date": "2025-11-25", "temp_mean_c": 28.5, "humidity": 65, "pm25": 42}
  ]
}

# ↓ Feature Engineering

# API Internal DataFrame
date       | region | temp | humidity | pm25 | temp_lag1 | temp_roll7 | dow | ...
2025-11-25 | R1     | 28.5 | 65       | 42   | 27.8      | 28.1       | 1   | ...

# ↓ XGBoost Prediction

# Raw Prediction
predictions = [12.5]  # Predicted admissions

# ↓ SHAP Explanation

# SHAP Values
{
  "base_value": 11.2,
  "shap_values": {
    "temp_lag1": +0.8,
    "temp_roll7": +0.5,
    "dow": +0.1,
    "humidity": -0.1
  },
  "prediction": 12.5  # base_value + sum(shap_values)
}

# ↓ API Response

{
  "region_id": "R1",
  "predictions": [12.5],
  "shap_values": {...},
  "baseline": 11.2
}

# ↓ Dashboard Display

# Plotly Chart
X-axis: Date (2025-11-25)
Y-axis: Admissions (12.5)
Tooltip: "Predicted: 12.5, Temp: 28.5°C"
```

---

## Model Pipeline

### Training Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                   Training Pipeline                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  Load Raw Data        │
                  │  (synthetic_data.csv) │
                  └───────────┬───────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌─────────────────────┐   ┌─────────────────────┐
    │  DLNM Pipeline      │   │  XGBoost Pipeline   │
    ├─────────────────────┤   ├─────────────────────┤
    │ 1. Minimal features │   │ 1. Rich features    │
    │    (temp, humidity) │   │    (60+ columns)    │
    │                     │   │                     │
    │ 2. Patsy formula    │   │ 2. Train/test split │
    │    cr(temp, lag=3)  │   │    (80/20)          │
    │                     │   │                     │
    │ 3. GLM fit          │   │ 3. XGBoost fit      │
    │    (Poisson family) │   │    (Poisson obj)    │
    │                     │   │                     │
    │ 4. Lag curves       │   │ 4. SHAP values      │
    │                     │   │                     │
    │ 5. Save model       │   │ 5. Save artifacts   │
    └─────────┬───────────┘   └─────────┬───────────┘
              │                         │
              ▼                         ▼
    ┌─────────────────────┐   ┌─────────────────────┐
    │  dlnm_model.joblib  │   │  xgb_model.joblib   │
    │                     │   │  baseline_data.joblib│
    │                     │   │  feature_names.joblib│
    └─────────────────────┘   └─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  outputs/        │
                    │  (artifacts)     │
                    └──────────────────┘
```

### Inference Pipeline

```
┌───────────────────────────────────────────────────────────┐
│                  Inference Pipeline                        │
└───────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌──────────────────────────┐
              │  API Request (JSON)      │
              │  {region, date, climate} │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Pydantic Validation     │
              │  (schema check)          │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Build Feature DataFrame │
              │  (align to training)     │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  XGBoost Prediction      │
              │  (loaded model)          │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  SHAP Explanation        │
              │  (feature contributions) │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  JSON Response           │
              │  {predictions, shap}     │
              └──────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Dashboard Display       │
              │  (Plotly charts)         │
              └──────────────────────────┘
```

---

## API Design

### RESTful Principles

```
Resource-Oriented Design:
- /health        → GET  (check status)
- /predict       → POST (create prediction)
- /explain       → POST (create explanation)

Stateless:
- Each request contains all necessary data
- No session stored on server
- Enables horizontal scaling

JSON Communication:
- Content-Type: application/json
- Accept: application/json
- Standardized data exchange

HTTP Status Codes:
- 200 OK: Success
- 400 Bad Request: Invalid input
- 422 Unprocessable Entity: Validation error
- 500 Internal Server Error: Server error
- 503 Service Unavailable: Model not loaded
```

### Request/Response Schemas

**POST /predict**

```json
// Request
{
  "region_id": "R1",
  "forecast": [
    {
      "date": "2025-11-25",
      "temp_mean_c": 28.5,
      "relative_humidity_pct": 65,
      "pm25_ugm3": 42.0
    },
    {
      "date": "2025-11-26",
      "temp_mean_c": 29.0,
      "relative_humidity_pct": 68,
      "pm25_ugm3": 45.0
    }
  ]
}

// Response
{
  "region_id": "R1",
  "predictions": [12.5, 13.1],
  "dates": ["2025-11-25", "2025-11-26"],
  "shap_values": [
    {
      "temp_mean_c_lag1": 0.8,
      "temp_mean_c_roll7": 0.5,
      "day_of_week": 0.1,
      "relative_humidity_pct_lag1": -0.1
    },
    {
      "temp_mean_c_lag1": 0.9,
      "temp_mean_c_roll7": 0.6,
      "day_of_week": 0.0,
      "relative_humidity_pct_lag1": -0.2
    }
  ],
  "baseline": 11.2,
  "metadata": {
    "model_version": "1.0.0",
    "timestamp": "2025-01-18T12:00:00Z"
  }
}
```

### Error Handling

```python
# Validation Error (422)
{
  "detail": [
    {
      "loc": ["body", "forecast", 0, "temp_mean_c"],
      "msg": "ensure this value is greater than or equal to -50",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": -50}
    }
  ]
}

# Model Not Loaded (503)
{
  "detail": "Model not loaded. Service starting up."
}

# Prediction Error (500)
{
  "detail": "Prediction failed: Feature mismatch",
  "error_type": "PredictionError"
}
```

---

## Dashboard Architecture

### Streamlit App Structure

```python
# src/dashboard/app.py

# 1. Imports and Setup
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Climate-CVD Risk",
    page_icon="🏥",
    layout="wide"
)

# 2. Session State (Cache Data)
if 'predictions' not in st.session_state:
    st.session_state.predictions = None

# 3. Sidebar (Inputs)
with st.sidebar:
    region = st.selectbox("Region", ["R1", "R2", "R3"])
    date = st.date_input("Date")
    temp = st.slider("Temperature (°C)", 0, 45, 25)
    humidity = st.slider("Humidity (%)", 0, 100, 60)
    
    if st.button("Get Prediction"):
        # Call API
        response = requests.post(
            "http://localhost:8000/predict",
            json={...}
        )
        st.session_state.predictions = response.json()

# 4. Main Area (Tabs)
tab1, tab2, tab3 = st.tabs(["Predictions", "Risk Map", "DLNM"])

with tab1:
    if st.session_state.predictions:
        # Display results
        st.metric("Predicted Admissions", 12.5)
        st.plotly_chart(create_time_series())
        st.plotly_chart(create_shap_waterfall())

with tab2:
    st.plotly_chart(create_risk_heatmap())

with tab3:
    st.plotly_chart(create_lag_response_curve())
```

### Caching Strategy

```python
# Cache expensive computations
@st.cache_data
def load_historical_data():
    """Loads once, cached for session"""
    return pd.read_csv('data/preprocessed_features.csv')

@st.cache_resource
def create_map():
    """Folium map, created once"""
    return folium.Map(location=[...])

# Disable caching for real-time data
def get_prediction(inputs):
    """Always fetch fresh prediction"""
    return requests.post("http://api/predict", json=inputs)
```

---

## Deployment Architecture

### Development Environment

```
Developer Machine
├─ Python 3.11 (venv)
├─ VS Code
├─ Git
└─ Running:
   ├─ uvicorn (API on :8000)
   └─ streamlit (Dashboard on :8501)
```

### Docker Deployment

```
Docker Host
├─ cvd-api (container)
│  ├─ Python 3.11-slim
│  ├─ Models loaded
│  ├─ Port 8000 → Host 8000
│  └─ Restart: unless-stopped
│
└─ cvd-dashboard (container)
   ├─ Python 3.11-slim
   ├─ Connects to API
   ├─ Port 8501 → Host 8501
   └─ Restart: unless-stopped
```

### Production Architecture (Scalable)

```
┌────────────────────────────────────────────────────┐
│                  Internet                          │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
     ┌────────────────────────┐
     │  Load Balancer (Nginx) │
     │  - SSL Termination     │
     │  - Rate Limiting       │
     └──────┬────────┬────────┘
            │        │
    ┌───────┘        └───────┐
    │                        │
    ▼                        ▼
┌─────────┐            ┌─────────┐
│ API #1  │            │ API #2  │
│ (8000)  │            │ (8000)  │
└────┬────┘            └────┬────┘
     │                      │
     └──────────┬───────────┘
                │
                ▼
     ┌────────────────────┐
     │  Shared Storage    │
     │  (Model Artifacts) │
     │  - S3 / NFS        │
     └────────────────────┘
```

---

## Summary

### Key Architectural Patterns

1. **Layered Architecture**: Data → Models → API → UI
2. **Microservices**: API and Dashboard as separate services
3. **Pipeline Pattern**: Sequential data transformations
4. **Factory Pattern**: Model artifact loading
5. **Singleton Pattern**: Model loaded once (API startup)

### Component Interactions

```
User → Dashboard → API → Models → Data
  ↑                           ↓
  └────── Visualizations ←────┘
```

### Design Principles

- **Separation of Concerns**: Each module has single responsibility
- **Dependency Injection**: Models passed to API, not hardcoded
- **Loose Coupling**: Dashboard talks to API via HTTP (could swap implementations)
- **High Cohesion**: Related functions grouped (e.g., all SHAP in one module)
- **Fail Fast**: Validation at API boundary (Pydantic)
- **Defensive Programming**: None checks, try-except blocks

---

**Congratulations!** You now understand the complete technical architecture of the Climate-CVD prediction system. Review the other learning guides for detailed implementation knowledge.

