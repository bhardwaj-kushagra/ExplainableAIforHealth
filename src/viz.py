"""Visualization module (Milestone 5).

Generates policy-ready visualizations:
1. Risk calendar heatmap (year-by-year)
2. Threshold response curves with confidence intervals
3. Spatial risk map (HTML with folium)
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
import json

PROCESSED = Path('data_processed/region_daily.parquet')
OUT_DIR = Path('outputs')


def load_data(data_path: Path) -> pd.DataFrame:
    """Load processed data."""
    df = pd.read_parquet(data_path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def create_risk_calendar(df: pd.DataFrame, output_dir: Path):
    """Generate risk calendar heatmap showing daily admissions by year."""
    df = df.copy()
    df['year'] = df['date'].dt.year
    df['day_of_year'] = df['date'].dt.dayofyear
    
    # Pivot to year x day matrix
    years = sorted(df['year'].unique())
    
    fig, axes = plt.subplots(len(years), 1, figsize=(14, 3 * len(years)))
    if len(years) == 1:
        axes = [axes]
    
    for ax, year in zip(axes, years):
        year_data = df[df['year'] == year]
        # Create calendar grid (approximate weeks)
        pivot = year_data.pivot_table(
            values='admissions',
            index=year_data['date'].dt.isocalendar().week,
            columns=year_data['date'].dt.dayofweek,
            aggfunc='mean'
        )
        
        sns.heatmap(
            pivot, 
            cmap='YlOrRd', 
            cbar_kws={'label': 'Admissions'},
            linewidths=0.5,
            ax=ax,
            vmin=df['admissions'].quantile(0.1),
            vmax=df['admissions'].quantile(0.9)
        )
        ax.set_title(f'Risk Calendar {year}')
        ax.set_xlabel('Day of Week (0=Mon)')
        ax.set_ylabel('ISO Week')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'risk_calendar.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f'[viz] Saved risk calendar')


def create_threshold_curves(df: pd.DataFrame, output_dir: Path):
    """Generate threshold response curves for temperature with confidence intervals."""
    # Temperature bins
    temp_bins = np.arange(df['temp_mean'].min(), df['temp_mean'].max(), 2)
    df['temp_bin'] = pd.cut(df['temp_mean'], bins=temp_bins)
    
    # Compute mean and CI for each bin
    grouped = df.groupby('temp_bin')['admissions'].agg(['mean', 'std', 'count'])
    grouped = grouped.dropna()
    grouped['se'] = grouped['std'] / np.sqrt(grouped['count'])
    grouped['ci_lower'] = grouped['mean'] - 1.96 * grouped['se']
    grouped['ci_upper'] = grouped['mean'] + 1.96 * grouped['se']
    
    # Extract bin midpoints
    bin_centers = [interval.mid for interval in grouped.index]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(bin_centers, grouped['mean'], 'b-', linewidth=2, label='Mean Admissions')
    ax.fill_between(
        bin_centers,
        grouped['ci_lower'],
        grouped['ci_upper'],
        alpha=0.3,
        label='95% CI'
    )
    ax.axhline(df['admissions'].mean(), color='gray', linestyle='--', alpha=0.5, label='Overall Mean')
    ax.set_xlabel('Mean Temperature (°C)', fontsize=12)
    ax.set_ylabel('Daily Admissions', fontsize=12)
    ax.set_title('Temperature-Response Curve with 95% Confidence Intervals', fontsize=14)
    ax.legend()
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'threshold_curve.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f'[viz] Saved threshold curve')


def create_spatial_risk_map(df: pd.DataFrame, output_dir: Path):
    """Generate spatial risk map HTML using folium.
    
    Uses sample single-region data; for multi-region would need real GeoJSON.
    """
    # For single region, create a simple placeholder map
    # Center on a default location (example: continental US center)
    center_lat, center_lon = 39.8283, -98.5795
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    
    # Add a marker for region R1
    risk_level = df['admissions'].mean()
    popup_text = f"Region: R1<br>Mean Admissions: {risk_level:.2f}<br>Risk Level: {'High' if risk_level > 10 else 'Moderate'}"
    
    folium.CircleMarker(
        location=[center_lat, center_lon],
        radius=20,
        popup=popup_text,
        color='red' if risk_level > 10 else 'orange',
        fill=True,
        fillColor='red' if risk_level > 10 else 'orange',
        fillOpacity=0.6
    ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <b>Risk Level</b><br>
    <i style="background: red; width: 20px; height: 20px; display: inline-block;"></i> High (>10 admissions)<br>
    <i style="background: orange; width: 20px; height: 20px; display: inline-block;"></i> Moderate (5-10)<br>
    </div>
    '''
    root = m.get_root()
    if hasattr(root, 'html'):
        root.html.add_child(folium.Element(legend_html))  # type: ignore
    else:
        # Fallback for different folium versions
        from branca.element import Element
        root.add_child(Element(legend_html))
    
    map_path = output_dir / 'spatial_risk_map.html'
    m.save(str(map_path))
    print(f'[viz] Saved spatial risk map to {map_path}')


def main():
    parser = argparse.ArgumentParser(description='Generate policy-ready visualizations')
    parser.add_argument('--data', default=str(PROCESSED))
    parser.add_argument('--output-dir', default=str(OUT_DIR))
    args = parser.parse_args()
    
    data_path = Path(args.data)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print('[viz] Loading data...')
    df = load_data(data_path)
    
    print('[viz] Creating risk calendar...')
    create_risk_calendar(df, output_dir)
    
    print('[viz] Creating threshold curves...')
    create_threshold_curves(df, output_dir)
    
    print('[viz] Creating spatial risk map...')
    create_spatial_risk_map(df, output_dir)
    
    print('[viz] All visualizations complete.')


if __name__ == '__main__':
    main()
