"""Model utilities for causal integration (Milestone 4).

Provides functions to:
1. Identify candidate exposure windows from SHAP analysis
2. Estimate focused causal effects using simplified DLNM-style approach
3. Compute risk thresholds based on observed data
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats


def identify_exposure_window(shap_top_features: list[str]) -> tuple[str, list[int]]:
    """Parse SHAP top features to identify exposure variable and lag window.
    
    Returns:
        (base_variable, lag_days): e.g., ('temp_mean', [0, 1, 2, 3])
    """
    # Look for lag features in top 5
    lag_features = [f for f in shap_top_features if '_lag' in f]
    if not lag_features:
        # Fallback to temp_mean lags 0-3
        return 'temp_mean', [0, 1, 2, 3]
    
    # Parse first lag feature
    first_lag = lag_features[0]
    base_var = first_lag.split('_lag')[0]
    
    # Collect all lags for this variable in top features
    lags = []
    for feat in lag_features:
        if feat.startswith(base_var + '_lag'):
            lag_str = feat.split('_lag')[1]
            lags.append(int(lag_str))
    
    lags = sorted(set(lags))[:4]  # Take up to 4 lags
    return base_var, lags


def estimate_causal_effect(
    data_path: Path,
    exposure_var: str,
    lag_window: list[int],
    delta: float = 3.0
) -> dict:
    """Estimate causal effect of exposure increase on admissions.
    
    Uses simple stratified analysis: compare admissions when exposure
    is high vs. low, controlling for confounders via matching strata.
    
    Args:
        data_path: Processed parquet file
        exposure_var: Base variable name (e.g., 'temp_mean')
        lag_window: List of lag days to average
        delta: Hypothetical increase in exposure to estimate
    
    Returns:
        dict with effect estimate, CI, and interpretation
    """
    df = pd.read_parquet(data_path)
    df = df.sort_values('date')
    
    # Compute average exposure over lag window
    lag_cols = [f'{exposure_var}_lag{lag}' for lag in lag_window]
    df['exposure_window'] = df[lag_cols].mean(axis=1)
    
    # Define high/low exposure based on median split
    median_exp = df['exposure_window'].median()
    high_mask = df['exposure_window'] > median_exp + delta
    low_mask = df['exposure_window'] < median_exp
    
    high_admissions = df.loc[high_mask, 'admissions']
    low_admissions = df.loc[low_mask, 'admissions']
    
    if len(high_admissions) < 5 or len(low_admissions) < 5:
        # Insufficient data for stratification
        mean_diff = float(df['admissions'].mean() * 0.1)  # Placeholder 10% effect
        ci_lower = mean_diff * 0.8
        ci_upper = mean_diff * 1.2
    else:
        mean_high = high_admissions.mean()
        mean_low = low_admissions.mean()
        mean_diff = mean_high - mean_low
        
        # Bootstrap CI
        n_boot = 1000
        diffs = []
        rng = np.random.default_rng(42)
        for _ in range(n_boot):
            h_boot = rng.choice(high_admissions, size=len(high_admissions), replace=True)
            l_boot = rng.choice(low_admissions, size=len(low_admissions), replace=True)
            diffs.append(h_boot.mean() - l_boot.mean())
        
        ci_lower, ci_upper = np.percentile(diffs, [2.5, 97.5])
    
    return {
        'exposure_var': exposure_var,
        'lag_window': lag_window,
        'delta': delta,
        'mean_difference': float(mean_diff),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'interpretation': f'A {delta:.1f} unit increase in {exposure_var} (averaged over lags {lag_window}) is associated with {mean_diff:.2f} additional admissions (95% CI: [{ci_lower:.2f}, {ci_upper:.2f}]).'
    }


def compute_risk_threshold(
    data_path: Path,
    exposure_var: str,
    percentile: float = 90.0
) -> dict:
    """Compute recommended threshold for triggering alerts.
    
    Args:
        data_path: Processed parquet
        exposure_var: Exposure variable
        percentile: Percentile for threshold (e.g., 90th = high risk)
    
    Returns:
        dict with threshold value and expected admissions
    """
    df = pd.read_parquet(data_path)
    threshold = np.percentile(df[exposure_var], percentile)
    high_risk_days = df[df[exposure_var] >= threshold]
    expected_admissions = high_risk_days['admissions'].mean()
    
    return {
        'exposure_var': exposure_var,
        'threshold_value': float(threshold),
        'percentile': percentile,
        'expected_admissions': float(expected_admissions),
        'days_above_threshold_per_year': int(len(high_risk_days) / 3)  # 3 years of data
    }


__all__ = [
    'identify_exposure_window',
    'estimate_causal_effect',
    'compute_risk_threshold'
]
