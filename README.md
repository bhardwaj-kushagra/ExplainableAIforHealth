# Explainable AI for Climate-Linked Cardiovascular Admissions

Milestone 0 (Bootstrap) Complete.

## Overview
This project links regional climate variability to daily cardiovascular emergency admissions, estimates causal effects, and exposes policy-ready visualizations and an alerts API. We proceed in iterative milestones. Currently, only the synthetic data generator and minimal ingestion test are implemented.

## Quick Start (Milestone 0)
### 1. Create & Activate Environment (Python 3.11 recommended)
```
pip install -r requirements.txt
```

### 2. Generate Synthetic Data
```
make synthetic
```
This produces `data_synthetic/region_daily.csv` with schema:
```
date,region_id,admissions,age_group,sex,temp_mean,temp_min,temp_max,dew_point,rel_humidity,pm25,is_holiday
```

### 3. Run Tests
```
pytest -q
```

## Synthetic Data Logic
Daily data (multi-year) includes:
- Seasonality in temperature and admissions
- Weekday/weekend and holiday modifiers
- Lagged temperature influence on admissions
- Pollution (pm25) random but seasonally modulated
- Deterministic seed for reproducibility (default 42)

## Makefile Targets (current)
- `make synthetic` – Generate synthetic dataset.

Future milestones will add preprocessing, DLNM causal models (R fallback), ML models (XGBoost/LightGBM), SHAP explainability, visualizations, API, dashboard, Docker reproducibility, provenance tracking, and CI.

## Data Privacy
The synthetic dataset contains no real or identifiable patient information. Replace with real data later following documented governance (to be added in a data datasheet and README section in milestone 7).

## Roadmap
See milestones in issue tracker / specification (summary embedded in user request). Upcoming: Milestone 1 adds ingestion & preprocessing pipeline.

## License
MIT – see `LICENSE`.
