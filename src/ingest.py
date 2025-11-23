"""Ingestion module (Milestone 1)

Responsibilities:
1. Validate CSV schema and types.
2. Parse dates and enforce ordering.
3. Copy or move raw file into `data_raw/` if provided elsewhere.
4. Emit provenance log (`outputs/data_provenance.json`) recording source, row count,
   data range, missing columns, and any imputations performed.

Note: For synthetic data we only *copy* into raw to avoid destructive moves.
"""
from __future__ import annotations
from pathlib import Path
import json
import datetime as dt
import pandas as pd

EXPECTED_COLUMNS = [
    "date","region_id","admissions","age_group","sex","temp_mean","temp_min",
    "temp_max","dew_point","rel_humidity","pm25","is_holiday"
]

def read_and_validate(path: str | Path) -> pd.DataFrame:
    """Load CSV and validate exact schema.

    Raises:
        FileNotFoundError: if path missing
        ValueError: if schema mismatch
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    df = pd.read_csv(p)
    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError("Schema mismatch: got %s" % df.columns.tolist())
    return df

def parse_and_sort(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if df['date'].isna().any():
        raise ValueError("Date parsing failed for some rows.")
    df = df.sort_values('date').reset_index(drop=True)
    return df

def write_provenance(source: Path, df: pd.DataFrame, output: Path, extra: dict | None = None) -> None:
    prov_path = Path('outputs') / 'data_provenance.json'
    prov = {
        'timestamp': dt.datetime.utcnow().isoformat() + 'Z',
        'source_file': str(source),
        'stored_raw': str(output),
        'rows': int(len(df)),
        'date_range': [df['date'].min().date().isoformat(), df['date'].max().date().isoformat()],
        'columns': list(df.columns),
        'missing_expected_columns': [c for c in EXPECTED_COLUMNS if c not in df.columns],
        'imputations': [],
        'warnings': []
    }
    if 'pm25' not in df.columns:
        prov['warnings'].append('pm25 missing: pollution confounder absent')
    if extra:
        prov.update(extra)
    with open(prov_path, 'w', encoding='utf-8') as f:
        json.dump(prov, f, indent=2)

def ingest(input_path: str | Path, raw_store: str | Path = 'data_raw/region_daily.csv') -> Path:
    """Full ingestion: validate, parse dates, persist a raw copy, and log provenance.

    Returns path to stored raw file.
    """
    src = Path(input_path)
    df = read_and_validate(src)
    df = parse_and_sort(df)
    raw_dest = Path(raw_store)
    raw_dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_dest, index=False)
    write_provenance(src, df, raw_dest)
    return raw_dest

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Ingest climate & admissions CSV')
    ap.add_argument('--input', default='data_synthetic/region_daily.csv')
    ap.add_argument('--raw-dest', default='data_raw/region_daily.csv')
    args = ap.parse_args()
    stored = ingest(args.input, args.raw_dest)
    print(f"[ingest] stored raw copy at {stored}")
