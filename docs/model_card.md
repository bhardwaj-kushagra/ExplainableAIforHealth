# Model Card: Climate-Linked Cardiovascular Risk Predictor

## Model Details

**Developer:** Explainable AI for Health Project  
**Model Date:** November 2025  
**Model Version:** 1.0.0  
**Model Type:** XGBoost Regressor (count:poisson objective)  
**License:** MIT

## Intended Use

### Primary Use Cases
- Daily prediction of cardiovascular emergency admissions based on meteorological forecasts
- Early warning system for public health authorities
- Research tool for understanding climate-health relationships

### Intended Users
- Public health officials and emergency planners
- Hospital administrators for resource allocation
- Climate health researchers
- Policy makers developing adaptation strategies

### Out-of-Scope Uses
- Individual patient diagnosis or treatment decisions
- Real-time emergency response (model requires 24-48 hour lead time)
- Regions with significantly different climate profiles than training data
- Financial or insurance risk assessment without domain expert validation

## Factors

### Relevant Factors
- **Geographic:** Single-region model (R1); generalization to other regions requires retraining
- **Temporal:** Trained on 2020-2022 data; performance may degrade over time due to climate change
- **Demographic:** Aggregates across all age groups and sexes; does not predict individual risk
- **Seasonal:** Captures seasonal patterns in temperature and admissions

### Evaluation Factors
- Model evaluated on time-based holdout (last 20% chronologically)
- Performance metrics computed for different temperature ranges
- SHAP values used to identify feature importance across subgroups

## Metrics

### Model Performance (Synthetic Data)
- **Test MAE:** 0.897 admissions/day
- **Test RMSE:** 0.938 admissions/day
- **Test R²:** 0.903
- **Calibration:** Well-calibrated across prediction range (see outputs/xgb_calibration.png)

### Decision Thresholds
- **Risk Score:** 0-1 normalized scale (>0.7 = high risk)
- **Temperature Threshold:** 90th percentile (region-specific)
- **Alert Trigger:** Expected admissions > 1.2× baseline

### Performance Across Factors
- Model performs consistently across weekdays vs. weekends
- Higher uncertainty during extreme weather events (tail of distribution)
- Lag features (1-3 days) show strongest predictive power

## Training Data

### Source
**Current Version:** Synthetic data generated for demonstration (deterministic seed=42)  
**Production Requirement:** Replace with de-identified hospital admissions data

### Data Schema
- Daily admissions counts (cardiovascular emergencies)
- Meteorological variables: temperature (mean/min/max), humidity, dew point
- Air quality: PM2.5 concentrations
- Temporal features: day of week, holidays, seasonality
- Engineered features: lag (0-21 days), rolling statistics (3/7/14 day windows)

### Data Size
- Training: 876 days (80%)
- Testing: 220 days (20%)
- Total: 1,096 days (3 years)

### Preprocessing
- Date parsing and sorting
- Lag feature generation (0-21 days)
- Rolling mean and standard deviation (3, 7, 14 day windows)
- Heat index and apparent temperature calculation
- Missing value handling: forward fill for initial lags

## Evaluation Data

- **Split Method:** Time-based (chronological)
- **Test Period:** Last 20% of data (most recent ~7 months)
- **Distribution:** Representative of seasonal variation
- **No Data Leakage:** Strict temporal ordering maintained

## Ethical Considerations

### Risks and Limitations

1. **Data Privacy:**
   - Current version uses synthetic data
   - Real deployment requires HIPAA-compliant data handling
   - No patient-level identifiers should be stored

2. **Fairness:**
   - Aggregated predictions may mask disparities across demographic groups
   - Vulnerable populations (elderly, low-income) may be underrepresented
   - Recommend disaggregated analysis for equity assessment

3. **Environmental Justice:**
   - Air pollution (PM2.5) impacts vary by neighborhood
   - Model should be stratified by socioeconomic status where possible
   - Alert systems should prioritize vulnerable communities

4. **Uncertainty Communication:**
   - Predictions are probabilistic, not deterministic
   - Confidence intervals should be communicated to decision-makers
   - Model performs best for typical conditions, not extreme events

### Recommendations for Deployment

- Validate on local data before operational use
- Establish human-in-the-loop review for high-risk alerts
- Regular model retraining (quarterly) to capture trends
- Disaggregate by demographic factors to assess equity
- Partner with community organizations for alert dissemination

## Caveats and Recommendations

### Known Limitations

1. **Synthetic Data:** Current model trained on simulated data; real-world performance unknown
2. **Single Region:** Generalization to other geographies requires retraining
3. **Confounding:** May not capture all relevant factors (e.g., influenza, extreme weather events)
4. **Climate Change:** Historical relationships may not hold under future climate scenarios

### Recommended Actions Before Production

- [ ] Replace synthetic data with de-identified hospital records
- [ ] Validate on external test set from different time period
- [ ] Conduct bias audit across demographic subgroups
- [ ] Establish monitoring dashboard for prediction drift
- [ ] Document data governance and access controls
- [ ] Obtain institutional review board (IRB) approval if required
- [ ] Develop standard operating procedures for alert response

### Update Frequency

- **Model Retraining:** Quarterly (or when drift detected)
- **Feature Updates:** As new meteorological data sources become available
- **Performance Monitoring:** Daily (automated alerts for degradation)

## Contact

For questions or issues, contact: [Add contact information]

**Model Artifacts:**
- Model file: `outputs/xgb_model.joblib`
- Metrics: `outputs/metrics.json`
- SHAP explanations: `outputs/shap_summary.png`
- Policy statement: `outputs/policy_statement.txt`

---

*This model card follows the framework proposed by Mitchell et al. (2019): "Model Cards for Model Reporting"*
