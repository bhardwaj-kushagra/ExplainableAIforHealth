"""SHAP explainability module (Milestone 3).

Uses SHAP TreeExplainer to compute:
1. Global feature importance (summary plot)
2. Dependence plots for top 5 features
3. Force plot for the highest surge day in test set
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt

PROCESSED = Path('data_processed/region_daily.parquet')
MODEL_PATH = Path('outputs/xgb_model.joblib')
OUT_DIR = Path('outputs')


def load_model_and_data(model_path: Path, data_path: Path, train_frac: float = 0.8):
    """Load trained model and test data."""
    model = joblib.load(model_path)
    df = pd.read_parquet(data_path)
    df = df.sort_values('date').reset_index(drop=True)
    
    exclude = ['date', 'region_id', 'admissions', 'age_group', 'sex']
    feature_cols = [c for c in df.columns if c not in exclude]
    
    split_idx = int(len(df) * train_frac)
    test = df.iloc[split_idx:]
    
    X_test = test[feature_cols]
    y_test = test['admissions']
    dates_test = test['date']
    
    return model, X_test, y_test, dates_test, feature_cols


def compute_shap_values(model, X_test):
    """Compute SHAP values using Explainer with predict function."""
    print('[explainers] Computing SHAP values...')
    # Use SHAP Explainer with model.predict as callable
    # Subsample for computational efficiency
    X_sample = X_test.sample(min(100, len(X_test)), random_state=42)
    explainer = shap.Explainer(model.predict, X_sample)
    shap_values = explainer(X_test)
    return explainer, shap_values


def plot_summary(shap_values, X_test, output_dir: Path):
    """Generate and save SHAP summary plot."""
    plt.figure(figsize=(10, 8))
    # Handle both Explanation objects and raw arrays
    if hasattr(shap_values, 'values'):
        shap.summary_plot(shap_values.values, X_test, show=False, max_display=20)
    else:
        shap.summary_plot(shap_values, X_test, show=False, max_display=20)
    plt.tight_layout()
    plt.savefig(output_dir / 'shap_summary.png', dpi=120, bbox_inches='tight')
    plt.close()
    print(f'[explainers] Saved SHAP summary plot')


def plot_dependence(shap_values, X_test, output_dir: Path, top_n: int = 5):
    """Generate dependence plots for top N features by mean absolute SHAP value."""
    # Extract values if Explanation object
    vals = shap_values.values if hasattr(shap_values, 'values') else shap_values
    mean_abs_shap = np.abs(vals).mean(axis=0)
    top_indices = np.argsort(mean_abs_shap)[-top_n:][::-1]
    feature_names = X_test.columns.tolist()
    
    for idx in top_indices:
        feature = feature_names[idx]
        plt.figure(figsize=(8, 5))
        shap.dependence_plot(idx, vals, X_test, show=False)
        plt.tight_layout()
        safe_name = feature.replace('/', '_').replace('\\', '_')
        plt.savefig(output_dir / f'shap_dependence_{safe_name}.png', dpi=120, bbox_inches='tight')
        plt.close()
    
    print(f'[explainers] Saved {top_n} dependence plots')
    return [feature_names[i] for i in top_indices]


def plot_force_surge_day(explainer, shap_values, X_test, y_test, dates_test, output_dir: Path):
    """Generate force plot for the day with highest admissions in test set."""
    surge_idx = y_test.argmax()
    surge_date = dates_test.iloc[surge_idx]
    surge_admissions = y_test.iloc[surge_idx]
    
    # Extract values and expected value
    vals = shap_values.values if hasattr(shap_values, 'values') else shap_values
    base_val = shap_values.base_values if hasattr(shap_values, 'base_values') else explainer.expected_value
    if isinstance(base_val, np.ndarray):
        base_val = base_val[0] if len(base_val) > 0 else base_val
    
    # Force plot
    try:
        force_plot = shap.force_plot(
            base_val,
            vals[surge_idx, :],
            X_test.iloc[surge_idx, :],
            matplotlib=True,
            show=False
        )
        plt.tight_layout()
        plt.savefig(output_dir / 'shap_force_surge.png', dpi=120, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f'[explainers] Force plot generation skipped due to: {e}')
        # Create placeholder
        plt.figure(figsize=(10, 3))
        plt.text(0.5, 0.5, f'Force plot for surge day\n{surge_date}\nAdmissions: {surge_admissions}',
                ha='center', va='center', fontsize=12)
        plt.axis('off')
        plt.savefig(output_dir / 'shap_force_surge.png', dpi=120, bbox_inches='tight')
        plt.close()
    
    print(f'[explainers] Saved force plot for surge day: {surge_date} (admissions={surge_admissions})')
    return surge_date, surge_admissions


def save_top_features_summary(top_features: list[str], output_dir: Path):
    """Save text summary of top SHAP features."""
    summary_path = output_dir / 'shap_top_features.txt'
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('Top 5 Features by SHAP Importance\n')
        f.write('=' * 40 + '\n\n')
        for i, feat in enumerate(top_features, 1):
            f.write(f'{i}. {feat}\n')
    print(f'[explainers] Saved top features summary')


def main():
    parser = argparse.ArgumentParser(description='Generate SHAP explanations')
    parser.add_argument('--model', default=str(MODEL_PATH))
    parser.add_argument('--data', default=str(PROCESSED))
    parser.add_argument('--output-dir', default=str(OUT_DIR))
    args = parser.parse_args()
    
    model_path = Path(args.model)
    data_path = Path(args.data)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print('[explainers] Loading model and data...')
    model, X_test, y_test, dates_test, feature_cols = load_model_and_data(model_path, data_path)
    
    # Compute SHAP
    explainer, shap_values = compute_shap_values(model, X_test)
    
    # Generate plots
    plot_summary(shap_values, X_test, output_dir)
    top_features = plot_dependence(shap_values, X_test, output_dir, top_n=5)
    plot_force_surge_day(explainer, shap_values, X_test, y_test, dates_test, output_dir)
    
    # Save summary
    save_top_features_summary(top_features, output_dir)
    
    print('[explainers] Complete.')


if __name__ == '__main__':
    main()
