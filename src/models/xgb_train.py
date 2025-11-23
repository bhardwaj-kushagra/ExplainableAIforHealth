"""XGBoost training script for cardiovascular admissions prediction (Milestone 3).

Loads processed parquet data, performs time-based train/test split,
trains XGBoost regressor optimized for count data, saves model artifact
and evaluation metrics including MAE, RMSE, and calibration plots.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt

PROCESSED = Path('data_processed/region_daily.parquet')
OUT_DIR = Path('outputs')


def load_and_split(data_path: Path, train_frac: float = 0.8):
    """Load parquet and do time-based train/test split."""
    df = pd.read_parquet(data_path)
    df = df.sort_values('date').reset_index(drop=True)
    
    # Define feature columns (exclude identifiers and target)
    exclude = ['date', 'region_id', 'admissions', 'age_group', 'sex']
    feature_cols = [c for c in df.columns if c not in exclude]
    
    # Time-based split
    split_idx = int(len(df) * train_frac)
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]
    
    X_train = train[feature_cols]
    y_train = train['admissions']
    X_test = test[feature_cols]
    y_test = test['admissions']
    
    return X_train, y_train, X_test, y_test, feature_cols


def train_model(X_train, y_train, X_test, y_test):
    """Train XGBoost with count:poisson objective."""
    params = {
        'objective': 'count:poisson',
        'max_depth': 5,
        'learning_rate': 0.05,
        'n_estimators': 200,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'n_jobs': -1,
        'verbosity': 0
    }
    
    model = xgb.XGBRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    return model


def evaluate_model(model, X_train, y_train, X_test, y_test, output_dir: Path):
    """Compute metrics and save calibration plot."""
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    
    metrics = {
        'train_mae': float(mean_absolute_error(y_train, train_pred)),
        'train_rmse': float(np.sqrt(mean_squared_error(y_train, train_pred))),
        'train_r2': float(r2_score(y_train, train_pred)),
        'test_mae': float(mean_absolute_error(y_test, test_pred)),
        'test_rmse': float(np.sqrt(mean_squared_error(y_test, test_pred))),
        'test_r2': float(r2_score(y_test, test_pred)),
    }
    
    # Calibration plot
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    ax[0].scatter(y_train, train_pred, alpha=0.5, s=10)
    ax[0].plot([y_train.min(), y_train.max()], [y_train.min(), y_train.max()], 'r--', lw=2)
    ax[0].set_xlabel('Actual Admissions (Train)')
    ax[0].set_ylabel('Predicted Admissions')
    ax[0].set_title(f"Train Calibration (MAE={metrics['train_mae']:.2f})")
    
    ax[1].scatter(y_test, test_pred, alpha=0.5, s=10)
    ax[1].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    ax[1].set_xlabel('Actual Admissions (Test)')
    ax[1].set_ylabel('Predicted Admissions')
    ax[1].set_title(f"Test Calibration (MAE={metrics['test_mae']:.2f})")
    
    plt.tight_layout()
    plt.savefig(output_dir / 'xgb_calibration.png', dpi=120)
    plt.close()
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description='Train XGBoost model for admissions prediction')
    parser.add_argument('--data', default=str(PROCESSED))
    parser.add_argument('--output-dir', default=str(OUT_DIR))
    args = parser.parse_args()
    
    data_path = Path(args.data)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print('[xgb_train] Loading and splitting data...')
    X_train, y_train, X_test, y_test, feature_cols = load_and_split(data_path)
    
    print(f'[xgb_train] Training set: {len(X_train)} samples')
    print(f'[xgb_train] Test set: {len(X_test)} samples')
    print(f'[xgb_train] Features: {len(feature_cols)}')
    
    print('[xgb_train] Training XGBoost model...')
    model = train_model(X_train, y_train, X_test, y_test)
    
    # Save model
    model_path = output_dir / 'xgb_model.joblib'
    joblib.dump(model, model_path)
    print(f'[xgb_train] Model saved to {model_path}')
    
    # Evaluate
    print('[xgb_train] Evaluating model...')
    metrics = evaluate_model(model, X_train, y_train, X_test, y_test, output_dir)
    
    # Save metrics
    metrics_path = output_dir / 'metrics.json'
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    print(f'[xgb_train] Metrics saved to {metrics_path}')
    
    print('\n=== Model Performance ===')
    print(f"Test MAE: {metrics['test_mae']:.3f}")
    print(f"Test RMSE: {metrics['test_rmse']:.3f}")
    print(f"Test R²: {metrics['test_r2']:.3f}")


if __name__ == '__main__':
    main()
