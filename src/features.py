"""Feature engineering utilities for preprocessing pipeline (Milestone 1).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

# Heat index formula (NOAA) expects Fahrenheit; convert inputs from Celsius.
# If temperature or humidity missing returns NaN.

def heat_index_c(temp_c: pd.Series, rh: pd.Series) -> pd.Series:
    t_f = temp_c * 9/5 + 32
    # Constants NOAA
    c1 = -42.379; c2 = 2.04901523; c3 = 10.14333127
    c4 = -0.22475541; c5 = -6.83783e-3; c6 = -5.481717e-2
    c7 = 1.22874e-3; c8 = 8.5282e-4; c9 = -1.99e-6
    hi_f = (c1 + c2*t_f + c3*rh + c4*t_f*rh + c5*(t_f**2) + c6*(rh**2) + c7*(t_f**2)*rh + c8*t_f*(rh**2) + c9*(t_f**2)*(rh**2))
    hi_c = (hi_f - 32) * 5/9
    return hi_c

# Apparent temperature (simplified) using Australian Bureau formula variant.
# AT = T + 0.33*e - 0.7*wind - 4; we lack wind, approximate wind=1.5 constant.
# e: water vapour pressure (hPa) approximated from dew point.

def apparent_temperature_c(temp_c: pd.Series, dew_point_c: pd.Series) -> pd.Series:
    # Magnus approximation for vapour pressure from dew point
    e = 6.105 * np.exp(17.27 * dew_point_c / (237.7 + dew_point_c))
    at = temp_c + 0.33*e - 0.7*1.5 - 4
    return at


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['day_of_week'] = df['date'].dt.weekday
    df['month'] = df['date'].dt.month
    df['day_of_year'] = df['date'].dt.dayofyear
    return df


def add_weather_derivatives(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['heat_index_c'] = heat_index_c(df['temp_mean'], df['rel_humidity'])
    df['apparent_temp_c'] = apparent_temperature_c(df['temp_mean'], df['dew_point'])
    return df


def add_lag_features(df: pd.DataFrame, cols: list[str], max_lag: int = 21) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        for lag in range(0, max_lag+1):
            out[f'{col}_lag{lag}'] = out[col].shift(lag)
    return out


def add_rolling_features(df: pd.DataFrame, cols: list[str], windows=(3,7,14)) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        for w in windows:
            out[f'{col}_rollmean{w}'] = out[col].rolling(window=w, min_periods=1).mean()
            out[f'{col}_rollstd{w}'] = out[col].rolling(window=w, min_periods=1).std(ddof=0)
    return out

__all__ = [
    'heat_index_c','apparent_temperature_c','add_time_features','add_weather_derivatives',
    'add_lag_features','add_rolling_features'
]
