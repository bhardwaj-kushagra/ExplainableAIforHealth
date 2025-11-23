"""Generate policy statement combining ML and causal signals (Milestone 4).

Produces a concise text document for policymakers summarizing:
1. Top drivers from SHAP analysis
2. Causal effect estimates with confidence intervals
3. Recommended trigger thresholds and expected outcomes
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json

# Import from sibling modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.model_utils import identify_exposure_window, estimate_causal_effect, compute_risk_threshold


PROCESSED = Path('data_processed/region_daily.parquet')
OUT_DIR = Path('outputs')


def load_shap_top_features(output_dir: Path) -> list[str]:
    """Load top features from SHAP analysis."""
    shap_file = output_dir / 'shap_top_features.txt'
    if not shap_file.exists():
        # Fallback defaults if file missing
        return ['temp_mean_lag1', 'temp_mean_lag0', 'pm25_lag0', 'rel_humidity_lag0', 'admissions_lag1']
    
    with open(shap_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    features = []
    for line in lines:
        if line.strip() and line[0].isdigit():
            feat = line.split('. ', 1)[-1].strip()
            features.append(feat)
    
    return features[:5]


def generate_policy_statement(data_path: Path, output_dir: Path):
    """Generate comprehensive policy statement."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load SHAP top features
    print('[policy] Loading SHAP top features...')
    top_features = load_shap_top_features(output_dir)
    
    # Identify exposure window
    print('[policy] Identifying exposure window...')
    exposure_var, lag_window = identify_exposure_window(top_features)
    
    # Estimate causal effect
    print('[policy] Estimating causal effect...')
    causal_est = estimate_causal_effect(data_path, exposure_var, lag_window, delta=3.0)
    
    # Compute risk threshold
    print('[policy] Computing risk threshold...')
    threshold = compute_risk_threshold(data_path, exposure_var, percentile=90.0)
    
    # Write policy statement
    policy_path = output_dir / 'policy_statement.txt'
    with open(policy_path, 'w', encoding='utf-8') as f:
        f.write('=' * 70 + '\n')
        f.write('CLIMATE-CARDIOVASCULAR RISK POLICY STATEMENT\n')
        f.write('=' * 70 + '\n\n')
        
        f.write('EXECUTIVE SUMMARY\n')
        f.write('-' * 70 + '\n')
        f.write('This analysis links daily climate variability to cardiovascular\n')
        f.write('emergency admissions using machine learning (XGBoost) and causal\n')
        f.write('inference (DLNM-style models). Results provide actionable thresholds\n')
        f.write('for public health early warning systems.\n\n')
        
        f.write('TOP DRIVERS (SHAP Analysis)\n')
        f.write('-' * 70 + '\n')
        for i, feat in enumerate(top_features, 1):
            f.write(f'{i}. {feat}\n')
        f.write('\n')
        
        f.write('CAUSAL EFFECT ESTIMATE\n')
        f.write('-' * 70 + '\n')
        f.write(f"Exposure Variable: {causal_est['exposure_var']}\n")
        f.write(f"Lag Window: {causal_est['lag_window']} days\n")
        f.write(f"Hypothetical Increase: +{causal_est['delta']:.1f} units\n\n")
        f.write(f"Expected Additional Admissions: {causal_est['mean_difference']:.2f}\n")
        f.write(f"95% Confidence Interval: [{causal_est['ci_lower']:.2f}, {causal_est['ci_upper']:.2f}]\n\n")
        f.write(f"Interpretation:\n{causal_est['interpretation']}\n\n")
        
        f.write('RECOMMENDED TRIGGER THRESHOLD\n')
        f.write('-' * 70 + '\n')
        f.write(f"Trigger: {threshold['exposure_var']} >= {threshold['threshold_value']:.1f}\n")
        f.write(f"Rationale: 90th percentile of observed distribution\n")
        f.write(f"Expected Admissions When Triggered: {threshold['expected_admissions']:.1f} per day\n")
        f.write(f"Frequency: ~{threshold['days_above_threshold_per_year']} days per year\n\n")
        
        f.write('RECOMMENDED ACTIONS\n')
        f.write('-' * 70 + '\n')
        f.write('1. Issue public health advisory 24-48 hours before threshold.\n')
        f.write('2. Increase staffing in emergency departments during risk periods.\n')
        f.write('3. Targeted outreach to vulnerable populations (elderly, chronic CVD).\n')
        f.write('4. Coordinate with meteorological services for forecast integration.\n\n')
        
        f.write('METHODOLOGY NOTES\n')
        f.write('-' * 70 + '\n')
        f.write('- ML Model: XGBoost with count:poisson objective\n')
        f.write('- Explainability: SHAP (TreeExplainer)\n')
        f.write('- Causal Inference: Stratified analysis with bootstrap CI\n')
        f.write('- Data: Synthetic 3-year daily admissions + meteorology\n')
        f.write('- For production use, replace with real hospital data.\n\n')
        
        f.write('LIMITATIONS\n')
        f.write('-' * 70 + '\n')
        f.write('- Current model uses synthetic data for demonstration.\n')
        f.write('- Confounding by air pollution (PM2.5) included but may be incomplete.\n')
        f.write('- Spatial heterogeneity not modeled (single-region analysis).\n')
        f.write('- Recommend validation with external hospital datasets.\n\n')
        
        f.write('CONTACT & DATA GOVERNANCE\n')
        f.write('-' * 70 + '\n')
        f.write('Model artifacts: outputs/xgb_model.joblib\n')
        f.write('Provenance log: outputs/data_provenance.json\n')
        f.write('For real data integration, see README.md data governance section.\n')
        f.write('=' * 70 + '\n')
    
    print(f'[policy] Policy statement saved to {policy_path}')
    
    # Also save machine-readable JSON
    policy_json = output_dir / 'policy_statement.json'
    with open(policy_json, 'w', encoding='utf-8') as f:
        json.dump({
            'top_features': top_features,
            'causal_effect': causal_est,
            'threshold': threshold
        }, f, indent=2)
    print(f'[policy] Machine-readable version saved to {policy_json}')


def main():
    parser = argparse.ArgumentParser(description='Generate policy statement')
    parser.add_argument('--data', default=str(PROCESSED))
    parser.add_argument('--output-dir', default=str(OUT_DIR))
    args = parser.parse_args()
    
    data_path = Path(args.data)
    output_dir = Path(args.output_dir)
    
    generate_policy_statement(data_path, output_dir)


if __name__ == '__main__':
    main()
