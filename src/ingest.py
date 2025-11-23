"""Ingestion stub for Milestone 0.
Will be expanded in Milestone 1 to validate schema, parse dates, and move raw to processed.
Currently provides a function to read the synthetic CSV and validate column order.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

EXPECTED_COLUMNS = [
    "date","region_id","admissions","age_group","sex","temp_mean","temp_min",
    "temp_max","dew_point","rel_humidity","pm25","is_holiday"
]

def read_and_validate(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    df = pd.read_csv(p)
    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError("Schema mismatch: got %s" % df.columns.tolist())
    return df

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data_synthetic/region_daily.csv")
    args = ap.parse_args()
    df = read_and_validate(args.input)
    print(df.head())
