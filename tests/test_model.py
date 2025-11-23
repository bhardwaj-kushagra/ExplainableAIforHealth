"""Unit tests for ML model training and SHAP generation (Milestone 3)."""
import subprocess
import sys
from pathlib import Path
import joblib
import pandas as pd
import json

MODEL_PATH = Path('outputs/xgb_model.joblib')
METRICS_PATH = Path('outputs/metrics.json')
SHAP_SUMMARY = Path('outputs/shap_summary.png')
PROCESSED = Path('data_processed/region_daily.parquet')


def ensure_model_trained():
    if not MODEL_PATH.exists():
        subprocess.check_call([sys.executable, 'src/models/xgb_train.py'])


def test_model_artifact_exists():
    ensure_model_trained()
    assert MODEL_PATH.exists()


def test_model_loads():
    ensure_model_trained()
    model = joblib.load(MODEL_PATH)
    assert model is not None
    assert hasattr(model, 'predict')


def test_metrics_file_exists():
    ensure_model_trained()
    assert METRICS_PATH.exists()


def test_metrics_reasonable():
    ensure_model_trained()
    with open(METRICS_PATH, 'r') as f:
        metrics = json.load(f)
    
    # Check keys present
    assert 'test_mae' in metrics
    assert 'test_rmse' in metrics
    assert 'test_r2' in metrics
    
    # Reasonable ranges for synthetic data
    assert 0 < metrics['test_mae'] < 10
    assert 0 < metrics['test_rmse'] < 15
    assert -1 < metrics['test_r2'] < 1


def test_model_prediction_shape():
    ensure_model_trained()
    model = joblib.load(MODEL_PATH)
    df = pd.read_parquet(PROCESSED)
    exclude = ['date', 'region_id', 'admissions', 'age_group', 'sex']
    feature_cols = [c for c in df.columns if c not in exclude]
    X_sample = df[feature_cols].iloc[:10]
    preds = model.predict(X_sample)
    assert len(preds) == 10
    assert all(preds >= 0)  # Count predictions should be non-negative


def test_shap_artifacts_exist():
    # Run explainer if needed
    if not SHAP_SUMMARY.exists():
        subprocess.check_call([sys.executable, 'src/explainers.py'])
    
    assert SHAP_SUMMARY.exists()
    assert Path('outputs/shap_top_features.txt').exists()
