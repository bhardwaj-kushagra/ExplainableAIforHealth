import os
from pathlib import Path
import pandas as pd
from src.ingest import read_and_validate, EXPECTED_COLUMNS

SYN_PATH = Path("data_synthetic/region_daily.csv")

def test_synthetic_file_exists():
    assert SYN_PATH.exists(), "Synthetic data file missing. Run make synthetic first."


def test_schema_and_nonempty():
    df = read_and_validate(SYN_PATH)
    assert list(df.columns) == EXPECTED_COLUMNS
    assert len(df) > 50  # multi-year


def test_basic_value_ranges():
    df = pd.read_csv(SYN_PATH)
    assert df['temp_mean'].between(-10, 40).all()
    assert df['rel_humidity'].between(10, 100).all()
    assert df['admissions'].ge(0).all()
