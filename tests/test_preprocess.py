import pandas as pd
from pathlib import Path
import subprocess, sys

PROCESSED = Path('data_processed/region_daily.parquet')
RAW = Path('data_synthetic/region_daily.csv')


def ensure_processed():
    if not PROCESSED.exists():
        subprocess.check_call([sys.executable, 'src/preprocess.py', '--input', str(RAW), '--output', str(PROCESSED)])


def test_preprocess_runs_and_outputs_file():
    ensure_processed()
    assert PROCESSED.exists()


def test_lag_features_present():
    ensure_processed()
    df = pd.read_parquet(PROCESSED)
    for lag in [0,1,7,14,21]:
        assert f'temp_mean_lag{lag}' in df.columns
        assert f'admissions_lag{lag}' in df.columns


def test_no_nulls_in_core_features():
    ensure_processed()
    df = pd.read_parquet(PROCESSED)
    core = ['temp_mean','rel_humidity','pm25','admissions']
    assert not df[core].isna().any().any()


def test_rolling_features_exist():
    ensure_processed()
    df = pd.read_parquet(PROCESSED)
    assert 'temp_mean_rollmean7' in df.columns
    assert 'admissions_rollstd14' in df.columns
