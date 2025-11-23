"""Preprocessing script (Milestone 1)
Loads raw or synthetic CSV, performs feature engineering, writes parquet.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from features import (
    add_time_features, add_weather_derivatives, add_lag_features, add_rolling_features
)
from ingest import ingest

DEF_LAG_COLS = ['temp_mean','rel_humidity','pm25','admissions']


def preprocess(input_csv: str, output_parquet: str) -> Path:
    # Ingest (validate + provenance)
    raw_path = ingest(input_csv, 'data_raw/region_daily.csv')
    df = pd.read_csv(raw_path)
    df['date'] = pd.to_datetime(df['date'])

    # Time features
    df = add_time_features(df)
    # Weather derivatives
    df = add_weather_derivatives(df)
    # Lag features
    df = add_lag_features(df, DEF_LAG_COLS, max_lag=21)
    # Rolling window stats
    df = add_rolling_features(df, DEF_LAG_COLS, windows=(3,7,14))

    # Impute early lag NaNs by forward fill (policy: minimal) then drop remaining if any
    lag_cols = [c for c in df.columns if c.endswith(tuple([f'lag{i}' for i in range(22)]))]
    df[lag_cols] = df[lag_cols].ffill()

    # Ensure no remaining NA in core engine features except allowed initial rows
    if df[DEF_LAG_COLS].isna().any().any():
        raise ValueError('Unexpected NA after preprocessing in core columns.')

    out_path = Path(output_parquet)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    print(f"[preprocess] wrote {out_path} rows={len(df)} cols={len(df.columns)}")
    return out_path


def main():
    ap = argparse.ArgumentParser(description='Preprocess raw admissions + meteorology')
    ap.add_argument('--input', default='data_synthetic/region_daily.csv')
    ap.add_argument('--output', default='data_processed/region_daily.parquet')
    args = ap.parse_args()
    preprocess(args.input, args.output)

if __name__ == '__main__':
    main()
