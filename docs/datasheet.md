# Datasheet: Climate-Cardiovascular Admissions Dataset

**Dataset Name:** Climate-Linked Cardiovascular Emergency Admissions  
**Version:** 1.0.0 (Synthetic)  
**Date:** November 2025  
**License:** MIT  

---

## Motivation

### For what purpose was the dataset created?

This dataset was created to:
1. Demonstrate the feasibility of linking regional climate variability to cardiovascular emergency admissions
2. Develop and validate predictive models for early warning systems
3. Support research on climate-health relationships
4. Enable causal inference of weather exposure on health outcomes

### Who created the dataset?

Created by the Explainable AI for Health Project as a synthetic demonstration dataset. Production use requires replacement with de-identified hospital administrative data.

### Who funded the creation of the dataset?

Internal project (demonstration). Real-world deployment would require institutional data sharing agreements.

---

## Composition

### What do the instances that comprise the dataset represent?

Each instance represents one day's aggregated data for a single geographic region:
- Daily count of cardiovascular emergency admissions
- Daily meteorological measurements (temperature, humidity, dew point)
- Daily air quality measurements (PM2.5)
- Temporal identifiers (date, day of week, holiday indicator)

### How many instances are there in total?

**Current (Synthetic):** 1,096 daily records (3 years: 2020-2022)  
**Production Target:** Minimum 3-5 years of historical data recommended

### Does the dataset contain all possible instances or is it a sample?

- **Coverage:** Complete daily records for the specified time period (no gaps)
- **Geographic Scope:** Single region (R1)
- **Demographic Scope:** Aggregated across all ages, sexes, and demographics

### What data does each instance consist of?

**Raw Fields (12 columns):**
- `date` (YYYY-MM-DD)
- `region_id` (categorical: R1)
- `admissions` (integer: daily count)
- `temp_mean_c` (float: mean temperature, °C)
- `temp_min_c` (float: minimum temperature, °C)
- `temp_max_c` (float: maximum temperature, °C)
- `relative_humidity_pct` (float: percent)
- `dew_point_c` (float: °C)
- `pm25_ugm3` (float: micrograms per cubic meter)
- `day_of_week` (integer: 0=Monday, 6=Sunday)
- `is_holiday` (boolean: 0/1)
- `season` (categorical: Winter/Spring/Summer/Fall)

**Engineered Features (117 additional columns):**
- Lag features: 0-21 day lags for all weather variables
- Rolling statistics: 3/7/14-day means and standard deviations
- Derived variables: heat index, apparent temperature, temperature range
- Time features: month, year, day of year

### Is there a label or target associated with the instances?

Yes, `admissions` is the target variable for supervised learning.

### Is any information missing from individual instances?

**Synthetic Data:** No missing values (complete by design)  
**Real Data Expectations:** 
- Weather data: Typically complete from meteorological services
- Admissions: Potential gaps on system downtime (should be imputed or flagged)
- Air quality: May have sensor outages (use interpolation or mark as missing)

### Are relationships between individual instances made explicit?

Yes:
- **Temporal:** Sequential daily records with date ordering
- **Lagged:** Engineered features create explicit temporal dependencies
- **Seasonal:** Cyclical patterns encoded in time features

### Are there recommended data splits?

**Yes (Time-Based):**
- Training: First 80% chronologically (876 days)
- Testing: Last 20% chronologically (220 days)
- **Critical:** Never shuffle; maintain temporal ordering to prevent leakage

### Are there any errors, sources of noise, or redundancies?

**Synthetic Data:** 
- Noise added to simulate measurement error (~10% coefficient of variation)
- Simplified relationships (may not capture real-world complexity)

**Real Data Considerations:**
- Weather measurement error (±0.5°C typical for temperature)
- PM2.5 sensor calibration drift
- Admissions coding errors (e.g., misclassified diagnoses)
- Weekend/holiday reporting delays

### Is the dataset self-contained, or does it link to or rely on external resources?

Self-contained in current form. Production version may link to:
- Meteorological service APIs (historical and forecast data)
- Hospital information systems (admissions data)
- Air quality monitoring networks (EPA AQI data)

---

## Collection Process

### How was the data associated with each instance acquired?

**Current (Synthetic):**
- Generated algorithmically using `data_synthetic/generate_synthetic.py`
- Deterministic (seed=42) for reproducibility
- Simulates realistic seasonal patterns and lag effects

**Real Data Acquisition (Production):**
- **Admissions:** Electronic health records (EHR) extraction with ICD-10 codes I00-I99 (cardiovascular)
- **Weather:** National Weather Service or equivalent meteorological service
- **Air Quality:** EPA Air Quality System (AQS) or equivalent monitoring network

### What mechanisms or procedures were used to collect the data?

**Synthetic:**
- Seasonal temperature pattern: `temp_mean_c = 15 + 12 * sin(2π * day_of_year / 365 - π/2)`
- Admissions model: Poisson with temperature and PM2.5 effects, 1-3 day lags

**Real Data (Expected):**
- Automated EHR query (daily batch export)
- Meteorological API polling (daily at midnight)
- Air quality sensor telemetry (hourly aggregated to daily mean)

### Who was involved in the data collection process?

**Synthetic:** Data scientists and public health researchers  
**Real Data (Expected):** 
- Hospital IT administrators
- Meteorological data engineers
- Public health data stewards

### Over what timeframe was the data collected?

**Synthetic:** 2020-01-01 to 2022-12-31 (3 years)  
**Real Data:** Recommend minimum 5 years for sufficient seasonal variation

### Were any ethical review processes conducted?

Not applicable for synthetic data. Real data requires:
- Institutional Review Board (IRB) approval
- Data Use Agreement (DUA) between hospital and research institution
- HIPAA compliance certification
- Community advisory board consultation (optional but recommended)

---

## Preprocessing / Cleaning / Labeling

### Was any preprocessing/cleaning/labeling of the data done?

**Yes:**
1. **Date Parsing:** String to datetime conversion
2. **Sorting:** Chronological ordering enforced
3. **Validation:** Schema checks for expected types and ranges
4. **Feature Engineering:** 
   - Lag features (0-21 days)
   - Rolling statistics (3/7/14 day windows)
   - Derived weather indices (heat index, apparent temperature)
   - Temporal encodings (day of week, month, season)

**Output:** `data_processed/region_daily.parquet` (1,096 rows × 129 columns)

### Was the "raw" data saved in addition to the preprocessed/cleaned/labeled data?

**Yes:**
- Raw synthetic data: `data_synthetic/synthetic_data.csv`
- Processed data: `data_processed/region_daily.parquet`
- Provenance log: `outputs/data_provenance.json`

### Is the software used to preprocess/clean/label the instances available?

**Yes:** All preprocessing code in `src/` directory:
- `src/ingest.py`: Validation and ingestion
- `src/features.py`: Feature engineering functions
- `src/preprocess.py`: Full pipeline orchestration

Dependencies in `requirements.txt`

---

## Uses

### Has the dataset been used for any tasks already?

**Yes:**
1. **Predictive Modeling:** XGBoost regressor (R²=0.903)
2. **Causal Inference:** Distributed lag non-linear models (DLNM)
3. **Explainability:** SHAP value analysis
4. **Visualization:** Risk calendars and threshold curves
5. **Policy Analysis:** Automated policy statement generation

### Is there a repository that links to any papers or systems that use the dataset?

Repository: [Add GitHub URL]  
Documentation: See `README.md` and `docs/model_card.md`

### What (other) tasks could the dataset be used for?

- **Anomaly Detection:** Identify unusual admission spikes
- **Forecasting:** Multi-day ahead predictions
- **Stratification:** Subgroup analysis by demographics (if disaggregated data available)
- **Comparative Studies:** Multi-region benchmarking
- **Climate Change Impact:** Project future burden under warming scenarios

### Are there tasks for which the dataset should not be used?

**Do Not Use For:**
- Individual patient diagnosis or prognosis
- Financial decisions without actuarial validation
- Real-time emergency dispatch (model not designed for <24 hour lead time)
- Regions outside training geography without retraining
- Legal or regulatory compliance determinations

---

## Distribution

### Will the dataset be distributed to third parties outside of the entity?

**Current (Synthetic):** Publicly available via repository under MIT license  
**Real Data:** Restricted access due to privacy and data use agreements

### How will the dataset be distributed?

**Synthetic:** GitHub repository  
**Real Data:** Secure data enclave with approved access only

### When will the dataset be distributed?

**Synthetic:** Immediately available  
**Real Data:** Subject to IRB approval and DUA execution

### Will the dataset be distributed under a copyright or other intellectual property license?

**Synthetic:** MIT License (permissive)  
**Real Data:** Proprietary (hospital/institution retains ownership)

### Have any third parties imposed IP-based or other restrictions?

Not applicable for synthetic data. Real data subject to HIPAA and institutional policies.

### Do any export controls or other regulatory restrictions apply?

**Synthetic:** No  
**Real Data:** Yes (HIPAA, institutional review, potentially state health privacy laws)

---

## Maintenance

### Who will be supporting/hosting/maintaining the dataset?

**Synthetic:** Project maintainers  
**Real Data:** Institutional data steward and IT infrastructure team

### How can the owner/curator/manager be contacted?

See `README.md` for contact information.

### Is there an erratum?

Changelog maintained in repository. Known issues tracked in GitHub Issues.

### Will the dataset be updated?

**Synthetic:** Static (v1.0.0)  
**Real Data:** Recommend quarterly updates with new admissions data

### If the dataset relates to people, are there limits on retention?

**Synthetic:** Not applicable (no real individuals)  
**Real Data:** Subject to institutional retention policies (typically 7 years minimum for health data)

### Will older versions be supported/hosted/maintained?

Yes, versioned releases via Git tags. Archived versions available indefinitely.

### If others want to extend/augment/build on/contribute to the dataset, is there a mechanism?

**Yes:**
- Fork repository and submit pull requests
- Contact maintainers for data sharing proposals
- Follow contribution guidelines in `CONTRIBUTING.md` (if created)

---

## References

**Datasheets Framework:**  
Gebru, T., et al. (2021). "Datasheets for Datasets." *Communications of the ACM*, 64(12), 86-92.

**Data Governance:**  
See `README.md` and institutional data use policies for production deployment.

---

*Last Updated: November 2025*
