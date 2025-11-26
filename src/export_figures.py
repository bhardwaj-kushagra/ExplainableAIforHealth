import argparse
import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Style setup for publication-quality figures
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update({
    "figure.autolayout": True,
    "savefig.bbox": "tight",
    "savefig.dpi": 200,
})


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_data(data_path: Path) -> pd.DataFrame:
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    if data_path.suffix.lower() in {".parquet", ".pq"}:
        try:
            return pd.read_parquet(data_path)
        except Exception:
            # Allow CSV fallback if parquet engines unavailable
            csv_fallback = data_path.with_suffix(".csv")
            if csv_fallback.exists():
                return pd.read_csv(csv_fallback)
            raise
    elif data_path.suffix.lower() in {".csv"}:
        return pd.read_csv(data_path)
    else:
        # Try parquet then csv by default names
        try:
            return pd.read_parquet(data_path)
        except Exception:
            return pd.read_csv(data_path)


def infer_columns(df: pd.DataFrame):
    # Reasonable defaults based on project conventions
    date_col = None
    y_col = None

    for cand in ["date", "Date", "ds"]:
        if cand in df.columns:
            date_col = cand
            break

    for cand in [
        "admissions", "y", "count", "n_admissions", "cvd_admissions", "emergency_admissions"
    ]:
        if cand in df.columns:
            y_col = cand
            break

    # Common climate covariates in project
    x_candidates = [
        "tmean", "tmin", "tmax", "precip", "humidity", "pm25", "wind", "dewpoint",
        "heat_index", "cold_index",
    ]
    x_cols = [c for c in x_candidates if c in df.columns]

    # Extract month/day-of-week if date exists
    if date_col and np.issubdtype(pd.to_datetime(df[date_col], errors='coerce').dtype, np.datetime64):
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    elif date_col:
        try:
            df[date_col] = pd.to_datetime(df[date_col])
        except Exception:
            pass

    return date_col, y_col, x_cols


# ------------------------- Figure Generators -------------------------

def fig_time_series(df: pd.DataFrame, date_col: str, y_col: str, outdir: Path) -> Path:
    fig, ax1 = plt.subplots(figsize=(12, 4))
    df_sorted = df.sort_values(date_col)
    ax1.plot(df_sorted[date_col], df_sorted[y_col].rolling(7, min_periods=1).mean(), color="#1f77b4", label=f"{y_col} (7d MA)")
    ax1.set_ylabel(y_col)
    ax1.set_xlabel("Date")

    # Try to overlay a climate variable if available
    climate_pref = ["tmean", "tmax", "tmin", "heat_index", "cold_index"]
    cvar = next((c for c in climate_pref if c in df.columns), None)
    if cvar:
        ax2 = ax1.twinx()
        ax2.plot(df_sorted[date_col], df_sorted[cvar].rolling(7, min_periods=1).mean(), color="#d62728", alpha=0.6, label=cvar)
        ax2.set_ylabel(cvar)
        ax2.grid(False)

    ax1.set_title("Daily admissions with climate overlay (7-day MA)")
    fig.autofmt_xdate()
    outfile = outdir / "ts_admissions_with_climate.png"
    fig.savefig(outfile)
    plt.close(fig)
    return outfile


def fig_histograms(df: pd.DataFrame, y_col: str, outdir: Path) -> list[Path]:
    paths = []
    # Admissions histogram
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(df[y_col].dropna(), bins=30, kde=True, ax=ax, color="#1f77b4")
    ax.set_title("Distribution of daily admissions")
    ax.set_xlabel(y_col)
    p1 = outdir / "hist_admissions.png"
    fig.savefig(p1)
    plt.close(fig)
    paths.append(p1)

    # Climate histogram if available
    for c in ["tmean", "tmax", "tmin", "precip"]:
        if c in df.columns:
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.histplot(df[c].dropna(), bins=30, kde=True, ax=ax, color="#2ca02c")
            ax.set_title(f"Distribution of {c}")
            ax.set_xlabel(c)
            p = outdir / f"hist_{c}.png"
            fig.savefig(p)
            plt.close(fig)
            paths.append(p)
            break  # only one climate hist to limit count
    return paths


def fig_hexbin(df: pd.DataFrame, y_col: str, outdir: Path) -> Path | None:
    # Pick a climate predictor
    for c in ["tmean", "tmax", "tmin", "heat_index", "cold_index"]:
        if c in df.columns:
            fig, ax = plt.subplots(figsize=(6, 5))
            hb = ax.hexbin(df[c], df[y_col], gridsize=40, cmap="viridis", mincnt=1)
            ax.set_xlabel(c)
            ax.set_ylabel(y_col)
            ax.set_title(f"Admissions vs {c} (hexbin)")
            cb = fig.colorbar(hb, ax=ax)
            cb.set_label("count")
            p = outdir / f"hex_admissions_vs_{c}.png"
            fig.savefig(p)
            plt.close(fig)
            return p
    return None


def fig_corr_heatmap(df: pd.DataFrame, y_col: str, outdir: Path) -> Path:
    cols = [y_col] + [c for c in [
        "tmean", "tmax", "tmin", "precip", "humidity", "pm25", "wind", "dewpoint"
    ] if c in df.columns]
    cdf = df[cols].select_dtypes(include=[np.number]).dropna()
    corr = cdf.corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax, cbar_kws={"shrink": .8})
    ax.set_title("Correlation heatmap")
    p = outdir / "corr_heatmap.png"
    fig.savefig(p)
    plt.close(fig)
    return p


def fig_boxplots_seasonality(df: pd.DataFrame, date_col: str, y_col: str, outdir: Path) -> list[Path]:
    paths = []
    if date_col in df.columns:
        df = df.copy()
        if not np.issubdtype(df[date_col].dtype, np.datetime64):
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df["month"] = df[date_col].dt.month
        df["weekday"] = df[date_col].dt.day_name()

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.boxplot(data=df, x="month", y=y_col, ax=ax)
        ax.set_title("Admissions by month")
        p1 = outdir / "box_admissions_by_month.png"
        fig.savefig(p1)
        plt.close(fig)
        paths.append(p1)

        # Weekday order
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df_week = df[df["weekday"].notna()]
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.boxplot(data=df_week, x="weekday", y=y_col, order=order, ax=ax)
        ax.set_title("Admissions by weekday")
        ax.set_xlabel("")
        p2 = outdir / "box_admissions_by_weekday.png"
        fig.savefig(p2)
        plt.close(fig)
        paths.append(p2)

    return paths


def fig_rolling_mean(df: pd.DataFrame, date_col: str, y_col: str, outdir: Path) -> Path:
    df = df.sort_values(date_col)
    fig, ax = plt.subplots(figsize=(12, 3.8))
    ax.plot(df[date_col], df[y_col], color="#9ecae1", alpha=0.5, linewidth=0.8, label="daily")
    ax.plot(df[date_col], df[y_col].rolling(7, min_periods=1).mean(), color="#08519c", label="7d MA")
    ax.plot(df[date_col], df[y_col].rolling(30, min_periods=1).mean(), color="#de2d26", label="30d MA")
    ax.legend(ncol=3, frameon=True)
    ax.set_title("Admissions moving averages")
    ax.set_xlabel("Date")
    ax.set_ylabel(y_col)
    fig.autofmt_xdate()
    p = outdir / "admissions_moving_averages.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# ------------------------- Collect existing project figures -------------------------

def copy_if_exists(src: Path, dst_dir: Path, new_name: str | None = None) -> Path | None:
    if src.exists():
        dst = dst_dir / (new_name if new_name else src.name)
        shutil.copyfile(src, dst)
        return dst
    return None


def collect_existing_figures(project_root: Path, outdir: Path) -> list[Path]:
    paths = []
    outputs = project_root / "outputs"

    # Core project artifacts
    for name in [
        "risk_calendar.png",
        "threshold_curve.png",
        "xgb_calibration.png",
        "shap_summary.png",
        "shap_force_surge.png",
        "dlnm_exposure_response.png",
        "dlnm_lag_surface.png",
    ]:
        p = copy_if_exists(outputs / name, outdir)
        if p:
            paths.append(p)

    # Copy up to 6 SHAP dependence plots if present
    dep_plots = sorted(outputs.glob("shap_dependence_*.png"))[:6]
    for pth in dep_plots:
        p = copy_if_exists(pth, outdir)
        if p:
            paths.append(p)

    # Copy spatial map HTML if present
    map_html = outputs / "spatial_risk_map.html"
    p = copy_if_exists(map_html, outdir)
    if p:
        paths.append(p)

    return paths


# ------------------------- Main orchestration -------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate and collect paper-ready figures.")
    parser.add_argument("--data", type=str, default=str(Path("data_processed") / "region_daily.parquet"), help="Path to processed data (parquet or csv)")
    parser.add_argument("--out", type=str, default=str(Path("outputs") / "paper_figures"), help="Output directory for figures")
    parser.add_argument("--project-root", type=str, default=str(Path(__file__).resolve().parents[1]), help="Project root to search for existing outputs")
    args = parser.parse_args()

    outdir = Path(args.out)
    ensure_dir(outdir)

    # Load data
    data_path = Path(args.data)
    df = load_data(data_path)

    date_col, y_col, x_cols = infer_columns(df)
    if date_col is None:
        # Try to infer from index
        if isinstance(df.index, pd.DatetimeIndex):
            date_col = "_index_date"
            df[date_col] = df.index
        else:
            raise ValueError("Could not infer date column. Expected a 'date' column or DatetimeIndex.")
    if y_col is None:
        raise ValueError("Could not infer admissions target column (e.g., 'admissions').")

    # Generate new EDA figures
    generated = []
    try:
        generated.append(fig_time_series(df, date_col, y_col, outdir))
    except Exception as e:
        print(f"WARN: time series fig failed: {e}", file=sys.stderr)

    try:
        generated.extend(fig_histograms(df, y_col, outdir))
    except Exception as e:
        print(f"WARN: histograms failed: {e}", file=sys.stderr)

    try:
        p = fig_hexbin(df, y_col, outdir)
        if p:
            generated.append(p)
    except Exception as e:
        print(f"WARN: hexbin failed: {e}", file=sys.stderr)

    try:
        generated.append(fig_corr_heatmap(df, y_col, outdir))
    except Exception as e:
        print(f"WARN: corr heatmap failed: {e}", file=sys.stderr)

    try:
        generated.extend(fig_boxplots_seasonality(df, date_col, y_col, outdir))
    except Exception as e:
        print(f"WARN: seasonality boxplots failed: {e}", file=sys.stderr)

    try:
        generated.append(fig_rolling_mean(df, date_col, y_col, outdir))
    except Exception as e:
        print(f"WARN: rolling mean failed: {e}", file=sys.stderr)

    # Collect existing project figures
    collected = collect_existing_figures(Path(args.project_root), outdir)

    # Write an index JSON with metadata
    index = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "data_path": str(data_path.resolve()),
        "generated": [str(p) for p in generated],
        "collected": [str(p) for p in collected],
    }
    with open(outdir / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    # Emit a simple README with figure list
    try:
        with open(outdir / "README.txt", "w", encoding="utf-8") as f:
            f.write("Paper Figures (auto-generated)\n")
            f.write("=============================\n\n")
            f.write("Generated (EDA)\n")
            for p in generated:
                f.write(f"- {Path(p).name}\n")
            f.write("\nCollected (from outputs)\n")
            for p in collected:
                f.write(f"- {Path(p).name}\n")
            f.write("\nNotes:\n- All PNGs are 200 DPI with tight layout.\n- Consider converting key PNGs to SVG for vector quality in LaTeX.\n")
    except Exception as e:
        print(f"WARN: README write failed: {e}", file=sys.stderr)

    total = len(generated) + len(collected)
    print(f"Done. Generated {len(generated)} new figures and collected {len(collected)} existing ones. Total: {total}.")
    print(f"Output directory: {outdir}")


if __name__ == "__main__":
    main()
