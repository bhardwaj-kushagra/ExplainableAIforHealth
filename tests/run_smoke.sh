#!/bin/bash
# Smoke Test Script - Validates end-to-end pipeline
# Usage: ./tests/run_smoke.sh

set -e  # Exit on first error

echo "==================================="
echo "🔥 SMOKE TEST - Full Pipeline"
echo "==================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function for test assertions
assert_file_exists() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} File exists: $1"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} Missing file: $1"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_dir_exists() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} Directory exists: $1"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} Missing directory: $1"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_command_success() {
    if eval "$1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Command succeeded: $1"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} Command failed: $1"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "Step 1: Verify directory structure"
echo "-----------------------------------"
assert_dir_exists "src"
assert_dir_exists "tests"
assert_dir_exists "data_synthetic"
assert_file_exists "requirements.txt"
assert_file_exists "Makefile"
echo ""

echo "Step 2: Generate synthetic data"
echo "--------------------------------"
if python data_synthetic/generate_synthetic.py; then
    echo -e "${GREEN}✓${NC} Synthetic data generated"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Data generation failed"
    ((TESTS_FAILED++))
    exit 1
fi

assert_file_exists "data_synthetic/synthetic_data.csv"

# Check CSV has expected row count (1096 days for 3 years)
ROW_COUNT=$(wc -l < data_synthetic/synthetic_data.csv)
if [ "$ROW_COUNT" -gt 1095 ]; then
    echo -e "${GREEN}✓${NC} Data has expected row count: $ROW_COUNT"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Unexpected row count: $ROW_COUNT (expected ~1096)"
    ((TESTS_FAILED++))
fi
echo ""

echo "Step 3: Preprocess data"
echo "-----------------------"
if python src/preprocess.py; then
    echo -e "${GREEN}✓${NC} Preprocessing completed"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Preprocessing failed"
    ((TESTS_FAILED++))
    exit 1
fi

assert_file_exists "data_processed/region_daily.parquet"
assert_file_exists "outputs/data_provenance.json"

# Verify parquet has expected columns (129 after feature engineering)
PARQUET_CHECK=$(python -c "import pandas as pd; df = pd.read_parquet('data_processed/region_daily.parquet'); print(df.shape[1])")
if [ "$PARQUET_CHECK" -ge 120 ]; then
    echo -e "${GREEN}✓${NC} Parquet has expected feature count: $PARQUET_CHECK columns"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Unexpected column count: $PARQUET_CHECK (expected ~129)"
    ((TESTS_FAILED++))
fi
echo ""

echo "Step 4: Train XGBoost model"
echo "---------------------------"
if python src/models/xgb_train.py; then
    echo -e "${GREEN}✓${NC} Model training completed"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Model training failed"
    ((TESTS_FAILED++))
    exit 1
fi

assert_file_exists "outputs/xgb_model.joblib"
assert_file_exists "outputs/metrics.json"
assert_file_exists "outputs/xgb_calibration.png"

# Check model performance (R² should be > 0.8 for synthetic data)
R2_SCORE=$(python -c "import json; print(json.load(open('outputs/metrics.json'))['test_r2'])")
echo "Test R² score: $R2_SCORE"
if (( $(echo "$R2_SCORE > 0.80" | bc -l) )); then
    echo -e "${GREEN}✓${NC} Model R² above threshold (>0.80)"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Model R² below expected: $R2_SCORE"
    ((TESTS_FAILED++))
fi
echo ""

echo "Step 5: Generate SHAP explanations"
echo "-----------------------------------"
if python src/explainers.py; then
    echo -e "${GREEN}✓${NC} SHAP analysis completed"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} SHAP analysis failed"
    ((TESTS_FAILED++))
fi

assert_file_exists "outputs/shap_summary.png"
assert_file_exists "outputs/shap_top_features.txt"

# Count SHAP dependence plots (should be 5)
SHAP_PLOTS=$(ls outputs/shap_dependence_*.png 2>/dev/null | wc -l)
if [ "$SHAP_PLOTS" -ge 5 ]; then
    echo -e "${GREEN}✓${NC} SHAP dependence plots generated: $SHAP_PLOTS"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Expected 5 dependence plots, found: $SHAP_PLOTS"
    ((TESTS_FAILED++))
fi
echo ""

echo "Step 6: Generate visualizations"
echo "--------------------------------"
if python src/viz.py; then
    echo -e "${GREEN}✓${NC} Visualizations completed"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Visualization generation failed"
    ((TESTS_FAILED++))
fi

assert_file_exists "outputs/risk_calendar.png"
assert_file_exists "outputs/threshold_curve.png"
assert_file_exists "outputs/spatial_risk_map.html"
echo ""

echo "Step 7: Generate policy statement"
echo "----------------------------------"
if python src/models/produce_policy_statement.py; then
    echo -e "${GREEN}✓${NC} Policy statement generated"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Policy statement generation failed"
    ((TESTS_FAILED++))
fi

assert_file_exists "outputs/policy_statement.txt"
assert_file_exists "outputs/policy_statement.json"

# Check policy statement has content
POLICY_SIZE=$(wc -c < outputs/policy_statement.txt)
if [ "$POLICY_SIZE" -gt 100 ]; then
    echo -e "${GREEN}✓${NC} Policy statement has content: $POLICY_SIZE bytes"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Policy statement too short: $POLICY_SIZE bytes"
    ((TESTS_FAILED++))
fi
echo ""

echo "Step 8: Test API startup"
echo "------------------------"
# Start API in background and test health endpoint
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
API_PID=$!
echo "API started with PID: $API_PID"

# Wait for API to start
sleep 3

# Test health endpoint
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✓${NC} API health check passed"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} API health check failed"
    ((TESTS_FAILED++))
fi

# Test predict endpoint (using example payload)
PREDICT_PAYLOAD='{
  "forecast_days": [{
    "date": "2023-01-15",
    "temp_mean_c": 28.5,
    "temp_min_c": 22.0,
    "temp_max_c": 35.0,
    "relative_humidity_pct": 65.0,
    "dew_point_c": 18.5,
    "pm25_ugm3": 35.0,
    "day_of_week": 0,
    "is_holiday": false,
    "season": "Summer"
  }]
}'

if curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d "$PREDICT_PAYLOAD" | grep -q "predicted_admissions"; then
    echo -e "${GREEN}✓${NC} API predict endpoint working"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} API predict endpoint failed"
    ((TESTS_FAILED++))
fi

# Cleanup API process
kill $API_PID 2>/dev/null || true
echo ""

echo "Step 9: Test dashboard import"
echo "------------------------------"
# Check if dashboard script has no syntax errors
if python -c "import src.dashboard.app" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Dashboard imports successfully"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Dashboard import check failed (may be okay if streamlit not installed)"
    # Don't increment TESTS_FAILED for optional dashboard
fi
echo ""

echo "Step 10: Run unit tests"
echo "-----------------------"
if pytest tests/ -q --tb=short; then
    echo -e "${GREEN}✓${NC} All pytest tests passed"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Some pytest tests failed"
    ((TESTS_FAILED++))
fi
echo ""

# Final report
echo "==================================="
echo "📊 SMOKE TEST SUMMARY"
echo "==================================="
echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Failed:${NC} $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL SMOKE TESTS PASSED!${NC}"
    echo "System is ready for production deployment."
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "Review errors above before deployment."
    exit 1
fi
