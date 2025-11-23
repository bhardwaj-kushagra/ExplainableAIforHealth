"""Wrapper to run canonical R DLNM script or fallback Python implementation.
Outputs: dlnm_exposure_response.png, dlnm_lag_surface.png, dlnm_effect_summary.txt
"""
from __future__ import annotations
import subprocess
import shutil
from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from patsy import dmatrix

R_SCRIPT = Path('src/models/dlnm_r_script.R')
PROCESSED = Path('data_processed/region_daily.parquet')
OUT_DIR = Path('outputs')


def run_r_version():
    if shutil.which('Rscript') is None:
        return False
    if not R_SCRIPT.exists():
        return False
    try:
        cmd = ['Rscript', str(R_SCRIPT), str(PROCESSED)]
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError:
        return False


def python_fallback():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED)
    df = df.sort_values('date')
    # Build lagged temp up to 21 days for simple cumulative effect
    for lag in range(0, 22):
        df[f'temp_mean_lag{lag}'] = df['temp_mean'].shift(lag)
    df = df.dropna().reset_index(drop=True)
    # Natural spline for temp_mean + distributed lag via average of lags 0-3,4-7,8-14,15-21
    df['temp_block1'] = df[[f'temp_mean_lag{i}' for i in range(0,4)]].mean(axis=1)
    df['temp_block2'] = df[[f'temp_mean_lag{i}' for i in range(4,8)]].mean(axis=1)
    df['temp_block3'] = df[[f'temp_mean_lag{i}' for i in range(8,15)]].mean(axis=1)
    df['temp_block4'] = df[[f'temp_mean_lag{i}' for i in range(15,22)]].mean(axis=1)
    spline = dmatrix("bs(temp_mean, df=5, degree=3)", data=df, return_type='dataframe')
    X = pd.concat([spline, df[['temp_block1','temp_block2','temp_block3','temp_block4','rel_humidity']]], axis=1)
    X = sm.add_constant(X)
    y = df['admissions']
    model = sm.GLM(y, X, family=sm.families.Poisson()).fit()
    # Exposure-response: vary temp_mean across observed range holding humidity median
    temps = np.linspace(df.temp_mean.min(), df.temp_mean.max(), 50)
    hum = float(df.rel_humidity.median())
    ex_df = pd.DataFrame({'temp_mean': temps})
    spline_ex = dmatrix("bs(temp_mean, df=5, degree=3)", data=ex_df, return_type='dataframe')
    blocks = {
        'temp_block1': temps,
        'temp_block2': temps,
        'temp_block3': temps,
        'temp_block4': temps,
        'rel_humidity': hum
    }
    ex_X = pd.concat([spline_ex, pd.DataFrame(blocks)], axis=1)
    # Align columns with training design matrix
    train_cols = X.columns.tolist()
    # Add constant if missing in training columns
    if 'const' not in train_cols:
        X_const = sm.add_constant(X)
        model_const = sm.GLM(y, X_const, family=sm.families.Poisson()).fit()
        model = model_const
        train_cols = X_const.columns.tolist()
    # Build prediction frame with same columns
    if 'const' in train_cols:
        ex_X.insert(0, 'const', 1.0)
    # Ensure ordering
    ex_X = ex_X[train_cols]
    preds = model.predict(ex_X)
    plt.figure(figsize=(9,6))
    plt.plot(temps, preds, label='Expected admissions')
    plt.xlabel('Mean Temperature (C)')
    plt.ylabel('Expected Admissions')
    plt.title('Fallback Exposure-Response (Temperature)')
    plt.legend()
    plt.savefig(OUT_DIR/'dlnm_exposure_response.png', dpi=120)
    plt.close()
    # Lag surface approximation: show effect by blocks vs temp
    block_effects = [model.params.get(col, np.nan) for col in ['temp_block1','temp_block2','temp_block3','temp_block4']]
    plt.figure(figsize=(9,6))
    plt.bar(['0-3','4-7','8-14','15-21'], block_effects)
    plt.xlabel('Lag Window (days)')
    plt.ylabel('Coefficient')
    plt.title('Fallback Lag Effect Blocks (Temperature)')
    plt.savefig(OUT_DIR/'dlnm_lag_surface.png', dpi=120)
    plt.close()
    # Effect size +3C
    ref_temp = 20.0
    delta = 3.0
    ref_idx = (np.abs(temps - ref_temp)).argmin()
    delta_idx = (np.abs(temps - (ref_temp + delta))).argmin()
    rr_change = preds[delta_idx] / preds[ref_idx]
    with open(OUT_DIR/'dlnm_effect_summary.txt','w',encoding='utf-8') as f:
        f.write(f"Reference temp: {ref_temp}\nIncrease (C): {delta}\nRelative Rate Change (approx): {rr_change:.3f}\nModel type: Python fallback GLM (Poisson spline)\n")
    print('[dlnm-fallback] wrote outputs')


def main():
    used_r = run_r_version()
    if not used_r:
        print('[dlnm] R unavailable or script failed – using Python fallback.')
        python_fallback()
    else:
        print('[dlnm] R version completed.')

if __name__ == '__main__':
    main()
