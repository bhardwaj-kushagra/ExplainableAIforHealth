#!/usr/bin/env python
"""Generate synthetic multi-year daily cardiovascular admissions + meteorology data.
Schema:
 date,region_id,admissions,age_group,sex,temp_mean,temp_min,temp_max,dew_point,rel_humidity,pm25,is_holiday

Deterministic with provided seed. Injects:
- Seasonal temperature using sinusoidal pattern
- Random daily weather variation
- Humidity correlated with dew point
- Admissions driven by base rate + temp extremes (U-shaped) + pollution + day-of-week + holiday effect + short lag (previous 1-3 day heat influence)
- Holidays (simple list) reduce admissions slightly

Outputs CSV to data_synthetic/region_daily.csv
"""
from __future__ import annotations
import argparse
import math
import numpy as np
import pandas as pd
from datetime import date, timedelta

COLUMNS = ["date","region_id","admissions","age_group","sex","temp_mean","temp_min","temp_max","dew_point","rel_humidity","pm25","is_holiday"]

HOLIDAYS = {"01-01","07-04","12-25"}  # simplistic US style placeholders
AGE_GROUPS = ["45-54","55-64","65-74","75-84","85+"]
SEXES = ["M","F"]

def dew_point_from_temp_rh(temp_c: float, rh: float) -> float:
    # Approximation using Magnus formula
    a, b = 17.62, 243.12
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh/100.0)
    return (b * alpha) / (a - alpha)

def generate(start: date, end: date, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    days = (end - start).days + 1
    records = []
    prev_temps = []
    for i in range(days):
        d = start + timedelta(days=i)
        doy = d.timetuple().tm_yday
        # Seasonal mean temperature pattern (peak mid-year)
        seasonal_temp = 15 + 10 * math.sin(2 * math.pi * (doy - 180) / 365)
        temp_mean = seasonal_temp + rng.normal(0, 3)
        temp_min = temp_mean - abs(rng.normal(5, 1))
        temp_max = temp_mean + abs(rng.normal(5, 1))
        rel_humidity = np.clip(60 + rng.normal(0, 15), 15, 95)
        dew_point = dew_point_from_temp_rh(temp_mean, rel_humidity)
        # Pollution seasonal baseline + noise
        pm25 = max(5, 20 + 10 * math.sin(2 * math.pi * (doy + 30) / 365) + rng.normal(0,5))
        is_holiday = 1 if f"{d.month:02d}-{d.day:02d}" in HOLIDAYS else 0
        # Admissions base
        base_rate = 10
        # Temperature U-shaped risk (heat & cold)
        temp_risk = 0.15 * (abs(temp_mean - 20))  # minimal at 20C
        # Pollution effect
        pollution_risk = 0.02 * pm25
        # Day of week effect (weekends slightly lower)
        dow = d.weekday()
        dow_adj = -1.5 if dow >= 5 else 0
        holiday_adj = -2 if is_holiday else 0
        # Lagged heat influence from previous 1-3 day average temps above 25C
        prev_temps.append(temp_mean)
        lag_heat = 0
        if len(prev_temps) > 3:
            recent = prev_temps[-4:-1]  # 1-3 days ago
            lag_heat = 0.1 * sum(max(0, t - 25) for t in recent)
        mean_adm = base_rate + temp_risk + pollution_risk + dow_adj + holiday_adj + lag_heat
        # Age/sex stratified sampling: we emit one record per sex-age group pair aggregated? Simplify: choose representative age+sex per day.
        age_group = rng.choice(AGE_GROUPS)
        sex = rng.choice(SEXES)
        admissions = rng.poisson(max(1, mean_adm))
        records.append([d.isoformat(),"R1",admissions,age_group,sex,round(temp_mean,1),round(temp_min,1),round(temp_max,1),round(dew_point,1),int(rel_humidity),round(pm25,1),is_holiday])
    df = pd.DataFrame(records, columns=COLUMNS)
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, default="2020-01-01")
    parser.add_argument("--end", type=str, default="2022-12-31")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="data_synthetic/region_daily.csv")
    args = parser.parse_args()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    df = generate(start, end, seed=args.seed)
    df.to_csv(args.output, index=False)
    print(f"[synthetic] wrote {args.output} rows={len(df)} seed={args.seed}")

if __name__ == "__main__":
    main()
