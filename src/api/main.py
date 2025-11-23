"""FastAPI application for climate-CVD risk prediction (Milestone 6).

Endpoints:
- GET /health: Health check
- POST /predict: 5-day forecast risk predictions with SHAP drivers
- POST /alert: Alert trigger check with recommendations
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import joblib
import shap
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .schemas import (
    HealthResponse, PredictRequest, PredictResponse, DayPrediction, DriverFeature,
    AlertRequest, AlertResponse
)

# Paths
MODEL_PATH = Path('outputs/xgb_model.joblib')
PROCESSED = Path('data_processed/region_daily.parquet')
POLICY_JSON = Path('outputs/policy_statement.json')

# Global state
app = FastAPI(
    title="Climate-CVD Risk Prediction API",
    description="Predicts daily cardiovascular admissions from meteorological forecasts",
    version="1.0.0"
)

model = None
feature_cols = None
explainer = None
baseline_data = None
policy_info = None


@app.on_event("startup")
def load_artifacts():
    """Preload model and explainer on startup."""
    global model, feature_cols, explainer, baseline_data, policy_info
    
    if MODEL_PATH.exists():
        model = joblib.load(MODEL_PATH)
        print(f"[api] Loaded model from {MODEL_PATH}")
    
    if PROCESSED.exists():
        df = pd.read_parquet(PROCESSED)
        exclude = ['date', 'region_id', 'admissions', 'age_group', 'sex']
        feature_cols = [c for c in df.columns if c not in exclude]
        baseline_data = df[feature_cols].tail(100)  # Recent data for SHAP baseline
        print(f"[api] Loaded {len(feature_cols)} features")
        
        # Initialize explainer
        if model is not None:
            explainer = shap.Explainer(model.predict, baseline_data.sample(min(50, len(baseline_data)), random_state=42))
            print(f"[api] Initialized SHAP explainer")
    
    if POLICY_JSON.exists():
        import json
        with open(POLICY_JSON, 'r') as f:
            policy_info = json.load(f)
        print(f"[api] Loaded policy info")


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        model_loaded=model is not None,
        data_available=baseline_data is not None
    )


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """Predict risk for 5-day forecast with SHAP driver explanations."""
    if model is None or feature_cols is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if len(request.forecast) == 0:
        raise HTTPException(status_code=400, detail="Forecast data required")
    
    # Build feature dataframe from forecast
    # Use last known values for lag/rolling features from baseline
    predictions = []
    
    for fc_day in request.forecast:
        # Start with median baseline features
        if baseline_data is not None:
            features = baseline_data.median().to_dict()
        else:
            raise HTTPException(status_code=503, detail="Baseline data not loaded")
        
        # Override with forecast values
        features['temp_mean'] = fc_day.temp_mean
        features['rel_humidity'] = fc_day.rel_humidity
        features['pm25'] = fc_day.pm25
        
        # Derived features (simplified - would need proper lag context in production)
        features['temp_mean_lag0'] = fc_day.temp_mean
        features['rel_humidity_lag0'] = fc_day.rel_humidity
        features['pm25_lag0'] = fc_day.pm25
        
        # Create feature vector
        X = pd.DataFrame([features])[feature_cols]
        
        # Predict
        pred = float(model.predict(X)[0])
        
        # Compute SHAP values for top drivers
        if explainer is not None:
            shap_vals = explainer(X)
            shap_array = shap_vals.values[0] if hasattr(shap_vals, 'values') else shap_vals[0]
            top_idx = np.argsort(np.abs(shap_array))[-3:][::-1]
            
            drivers = [
                DriverFeature(
                    feature=feature_cols[i],
                    contribution=float(shap_array[i])
                )
                for i in top_idx
            ]
        else:
            drivers = []
        
        # Normalize risk score (0-1) based on observed range
        risk_score = min(1.0, max(0.0, (pred - 5) / 10))  # Assume 5-15 range
        
        predictions.append(DayPrediction(
            date=fc_day.date,
            risk_score=risk_score,
            expected_admissions=pred,
            top_drivers=drivers
        ))
    
    return PredictResponse(
        region_id=request.region_id,
        predictions=predictions
    )


@app.post("/alert", response_model=AlertResponse)
def check_alert(request: AlertRequest):
    """Check if alert should be triggered based on threshold."""
    if baseline_data is None:
        raise HTTPException(status_code=503, detail="Data not available")
    
    # Use policy threshold or custom
    if request.threshold is None:
        if policy_info and 'threshold' in policy_info:
            threshold = policy_info['threshold']['threshold_value']
        else:
            threshold = baseline_data['temp_mean'].quantile(0.9)
    else:
        threshold = request.threshold
    
    triggered = request.current_temp_mean >= threshold
    
    # Expected admissions if triggered
    if triggered and policy_info and 'threshold' in policy_info:
        expected = policy_info['threshold']['expected_admissions']
    else:
        expected = baseline_data['admissions'].mean() if 'admissions' in baseline_data else 10.0
    
    actions = []
    if triggered:
        actions = [
            "Issue public health advisory 24-48 hours in advance",
            "Increase emergency department staffing",
            "Targeted outreach to vulnerable populations (elderly, chronic CVD)",
            "Coordinate with meteorological services"
        ]
    
    return AlertResponse(
        triggered=triggered,
        threshold_value=threshold,
        current_value=request.current_temp_mean,
        expected_admissions=expected if triggered else baseline_data.get('admissions', pd.Series([10])).mean(),
        recommended_actions=actions
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
