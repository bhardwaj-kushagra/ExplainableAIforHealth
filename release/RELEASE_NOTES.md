# Release Notes - v1.0.0
## Explainable AI for Climate-Linked Cardiovascular Admissions

**Release Date:** November 2025  
**Status:** Production-ready (with synthetic data)  

---

## 🎉 What's Included

This is the first production release of the Explainable AI for Climate-Linked Cardiovascular Admissions system. The system demonstrates a complete end-to-end pipeline from data ingestion to operational API and interactive dashboard.

### Core Capabilities

✅ **Data Pipeline**
- Automated data ingestion with schema validation
- 117 engineered features (lag, rolling, derived indices)
- Provenance tracking and data lineage

✅ **Causal Inference**
- Distributed Lag Non-Linear Models (DLNM)
- Exposure-response curves
- Lag-response surface analysis

✅ **Predictive Modeling**
- XGBoost regressor with Poisson objective
- Test R² = 0.903, MAE = 0.897 admissions/day
- Well-calibrated predictions across range

✅ **Explainability**
- SHAP-based feature importance
- Dependence plots showing interactions
- Individual prediction explanations

✅ **Policy Tools**
- Risk calendar (year-by-year heatmap)
- Threshold curves with confidence intervals
- Spatial risk maps (interactive HTML)
- Automated policy statement generation

✅ **Production API**
- FastAPI REST service
- Endpoints: `/health`, `/predict`, `/alert`
- <2s response time target met
- Pydantic validation for requests/responses

✅ **Interactive Dashboard**
- Streamlit multi-page application
- Model performance visualization
- Forecast input form
- Policy brief download

✅ **Deployment Infrastructure**
- Docker containerization
- GitHub Actions CI/CD
- Comprehensive testing suite (18 tests)
- Smoke test validation script

✅ **Documentation**
- Production-ready README
- Model card (Mitchell et al. framework)
- Data datasheet (Gebru et al. framework)
- Handover guide for deployment team

---

## 📦 Package Contents

```
ExplainableAIforHealth/
├── data_synthetic/           # Synthetic data generator
│   ├── generate_synthetic.py
│   └── synthetic_data.csv
├── data_processed/           # Preprocessed features
│   └── region_daily.parquet  # 1,096 rows × 129 columns
├── outputs/                  # Model artifacts and visualizations
│   ├── xgb_model.joblib      # Trained XGBoost model
│   ├── metrics.json          # Performance metrics
│   ├── shap_summary.png      # Feature importance
│   ├── risk_calendar.png     # Risk heatmap
│   ├── threshold_curve.png   # Temperature-response
│   ├── spatial_risk_map.html # Interactive map
│   ├── policy_statement.txt  # Human-readable brief
│   ├── policy_statement.json # Machine-readable data
│   └── [17 other output files]
├── src/                      # Source code
│   ├── api/                  # FastAPI REST service
│   ├── dashboard/            # Streamlit application
│   ├── models/               # Training and causal inference
│   ├── ingest.py             # Data validation
│   ├── features.py           # Feature engineering
│   ├── preprocess.py         # Pipeline orchestration
│   ├── explainers.py         # SHAP analysis
│   └── viz.py                # Visualizations
├── tests/                    # Test suite
│   ├── test_ingest.py
│   ├── test_preprocess.py
│   ├── test_model.py
│   ├── test_api.py
│   └── run_smoke.sh          # End-to-end validation
├── docs/                     # Documentation
│   ├── model_card.md
│   └── datasheet.md
├── .github/workflows/        # CI/CD
│   └── ci.yml
├── Dockerfile                # Container configuration
├── requirements.txt          # Python dependencies
├── Makefile                  # Build targets
├── README.md                 # Comprehensive guide
├── handover.txt              # Deployment procedures
└── LICENSE                   # MIT License
```

---

## 🚀 Quick Start

### With Docker (Recommended)

```powershell
# Build image
docker build -t explainable-ai-cvd:v1.0.0 .

# Run API (http://localhost:8000)
docker run -p 8000:8000 explainable-ai-cvd:v1.0.0

# Run dashboard (http://localhost:8501)
docker run -p 8501:8501 explainable-ai-cvd:v1.0.0 streamlit run src/dashboard/app.py
```

### Local Installation

```powershell
# Setup environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run full pipeline
make all

# Start services
make run-api       # Terminal 1
make run-dashboard # Terminal 2
```

---

## 📊 Model Performance (Synthetic Data)

**XGBoost Regressor:**
- Test MAE: 0.897 admissions/day
- Test RMSE: 0.938
- Test R²: 0.903
- Training time: ~15 seconds
- Prediction latency: <50ms

**Top Features (SHAP):**
1. `temp_mean_c_lag_1` (1-day lagged temperature)
2. `temp_mean_c_lag_2` (2-day lagged temperature)
3. `pm25_ugm3_lag_1` (1-day lagged PM2.5)
4. `relative_humidity_pct` (current humidity)
5. `day_of_week` (temporal patterns)

---

## 🔧 Production Deployment

### Replace Synthetic Data

1. Prepare CSV matching schema (see `handover.txt`)
2. Place at `data_raw/hospital_admissions.csv`
3. Update `src/ingest.py` line 85
4. Run: `make preprocess && make train`
5. Validate performance: `pytest tests/`

### Integrate Weather APIs

- **Option 1:** National Weather Service (free)
- **Option 2:** EPA AirNow for air quality (requires key)
- **Option 3:** OpenWeatherMap (commercial)

See `handover.txt` Section 2 for implementation details.

---

## 🧪 Testing

**Unit Tests:** 18 tests passing
```powershell
pytest tests/ -v
```

**Smoke Test:** End-to-end validation
```powershell
.\tests\run_smoke.sh
```

**Load Test:** API performance (not included, recommend k6 or Locust)

---

## 📋 Known Limitations

### Current Release

1. **Synthetic Data Only**
   - Model trained on simulated data
   - Performance on real data unvalidated
   - Requires retraining before operational use

2. **Single Region**
   - Only supports one geographic area
   - Multi-region requires model modifications (see handover guide)

3. **No Authentication**
   - API endpoints are open
   - Add API keys before production deployment

4. **Static Forecasts**
   - No live weather API integration
   - Requires manual forecast input or code updates

5. **No Database Persistence**
   - Predictions not stored
   - Add PostgreSQL for historical tracking

6. **Limited Error Handling**
   - Basic exception handling
   - Enhance for edge cases in production

### Model Assumptions

- Linear relationship between temperature and admissions may not hold at extremes
- Lag structure fixed at 0-21 days (may vary by region)
- Seasonal patterns assumed stationary (climate change impact not modeled)
- No interaction terms between weather variables (SHAP captures some)

---

## 🔜 Roadmap (Future Releases)

**v1.1.0 - Multi-Region Support**
- Train separate models per health district
- Region-specific threshold tuning
- Comparative analysis dashboard

**v1.2.0 - Real-Time Integration**
- NWS API forecast fetching
- EPA AirNow PM2.5 integration
- Automated daily predictions

**v1.3.0 - Advanced Features**
- Ensemble models (XGBoost + LightGBM + Random Forest)
- Time series forecasting (Prophet for trends)
- Uncertainty quantification (conformal prediction)

**v2.0.0 - Enterprise Features**
- Multi-tenancy (hospital network support)
- Role-based access control
- PostgreSQL persistence
- Real-time alerting (email, SMS, Slack)
- Grafana monitoring dashboards

---

## 🐛 Bug Reporting

**GitHub Issues:** [Add repository URL]

**Template:**
```
**Environment:** Docker / Local / Cloud
**Python Version:** 3.11
**OS:** Windows / Linux / macOS

**Steps to Reproduce:**
1. ...
2. ...

**Expected Behavior:**
...

**Actual Behavior:**
...

**Logs:**
...
```

---

## 📄 License

MIT License - see [LICENSE](../LICENSE) for full text.

**Commercial Use:** Permitted  
**Modification:** Permitted  
**Distribution:** Permitted  
**Patent Use:** Not granted (not applicable to this software)

---

## 🙏 Acknowledgments

**Frameworks and Tools:**
- XGBoost for gradient boosting
- SHAP for explainability
- FastAPI for API development
- Streamlit for dashboards
- Statsmodels for DLNM fallback

**Methodological References:**
- Gasparrini et al. (2010) - DLNM framework
- Lundberg & Lee (2017) - SHAP values
- Mitchell et al. (2019) - Model cards
- Gebru et al. (2021) - Datasheets for datasets

---

## 📞 Support

**Documentation:** See [README.md](../README.md) and [handover.txt](../handover.txt)  
**Issues:** GitHub Issues  
**Email:** [contact@example.com]  

---

**Released by:** [Your Name/Team]  
**Contact:** [email@example.com]  
**GitHub:** [repository URL]
