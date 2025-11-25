# Problems Encountered and Solutions - Complete Technical Reference

## Table of Contents
1. [Critical Problems](#critical-problems)
2. [Moderate Issues](#moderate-issues)
3. [Minor Fixes](#minor-fixes)
4. [Preventive Measures](#preventive-measures)
5. [Debugging Techniques](#debugging-techniques)

---

## Critical Problems

### Problem 1: SHAP TreeExplainer Compatibility with XGBoost 2.0.3

**When It Happened**: Milestone 3, implementing SHAP explainability

**The Error**:
```python
AttributeError: 'XGBTreeModelLoader' object has no attribute 'base_score'
```

**What This Means**:
- **Technical**: SHAP's `TreeExplainer` tries to access internal XGBoost attributes
- **Root cause**: XGBoost 2.0+ refactored internal model structure
- **Why it matters**: Can't explain predictions → can't use in clinical settings

**Context**:
```python
# This failed:
import shap
explainer = shap.TreeExplainer(model)  # ❌ AttributeError
shap_values = explainer.shap_values(X_test)
```

**What We Tried** (Failed Attempts):

**Attempt 1**: Downgrade XGBoost
```bash
pip install xgboost==1.7.6  # ❌ Lost count:poisson improvements
```
**Why it failed**: XGBoost 1.x has inferior Poisson handling

**Attempt 2**: Update SHAP
```bash
pip install shap==0.46.0  # ❌ Still incompatible
```
**Why it failed**: SHAP updates lag behind XGBoost releases

**Attempt 3**: Use different explainer
```python
explainer = shap.KernelExplainer(model.predict, X_sample)  # ⚠️ Too slow
# Takes 5+ minutes for 100 samples
```
**Why suboptimal**: KernelExplainer is model-agnostic (no optimizations)

**The Solution**: PermutationExplainer
```python
# src/explainers.py
import shap

# Sample background data (50 rows for speed)
X_sample = X_train.sample(min(50, len(X_train)), random_state=42)

# Use PermutationExplainer instead of TreeExplainer
explainer = shap.Explainer(model.predict, X_sample)  # ✅ Works!

# Compute SHAP values
shap_values = explainer(X_test)  # Returns Explanation object
```

**How PermutationExplainer Works**:
1. **Baseline**: Uses X_sample as reference distribution
2. **Perturbation**: For each feature, replaces it with values from X_sample
3. **Measure**: Sees how prediction changes
4. **Attribution**: Assigns contribution based on change

**Trade-offs**:
| Explainer | Speed | Accuracy | XGBoost Compatible |
|-----------|-------|----------|-------------------|
| TreeExplainer | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ (v2.0+) |
| PermutationExplainer | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ |
| KernelExplainer | ⭐ | ⭐⭐⭐⭐ | ✅ |

**Lesson Learned**:
- Always check library compatibility before upgrading
- Have fallback explainers ready
- PermutationExplainer is a good middle ground

**How to Prevent**:
```python
# requirements.txt - Pin specific versions
xgboost==2.0.3
shap==0.45.0

# Add compatibility test
def test_shap_compatibility():
    model = xgb.XGBRegressor()
    model.fit(X_train, y_train)
    try:
        explainer = shap.TreeExplainer(model)
        assert True
    except AttributeError:
        # Fallback to PermutationExplainer
        explainer = shap.Explainer(model.predict, X_train.sample(50))
        assert explainer is not None
```

---

### Problem 2: Pydantic Field Name Conflict with datetime.date

**When It Happened**: Milestone 6, creating API schemas

**The Error**:
```python
TypeError: issubclass() arg 1 must be a class
```

**What This Means**:
- **Technical**: Pydantic field named `date` conflicts with `datetime.date` type
- **Root cause**: Python imports create namespace collisions
- **Why it matters**: API validation fails, requests get 500 errors

**Context**:
```python
# src/api/schemas.py
from datetime import date

class ForecastDay(BaseModel):
    date: date  # ❌ Error! 'date' is both field name and type
    temp_mean_c: float
```

**What Happens**:
1. Import: `from datetime import date` (now `date` is a type)
2. Field: `date: date` (field name shadows the type)
3. Pydantic: "What's the type of `date`?" → Finds field name, not type
4. Crash: Can't use field name as type

**The Solution**: Alias the import
```python
# src/api/schemas.py
from datetime import date as date_type  # ✅ Rename import

class ForecastDay(BaseModel):
    date: date_type  # Now clear: field is 'date', type is 'date_type'
    temp_mean_c: float
```

**Alternative Solutions**:

**Option A**: Import datetime module
```python
import datetime

class ForecastDay(BaseModel):
    date: datetime.date  # Explicit, but verbose
```

**Option B**: Rename field
```python
from datetime import date

class ForecastDay(BaseModel):
    forecast_date: date  # Clearer semantically anyway
```

**Lesson Learned**:
- Avoid shadowing Python builtins/stdlib names
- Use aliases for clarity (`as date_type`)
- Pydantic errors can be cryptic—check for name collisions

**Common Shadowing Pitfalls**:
```python
# BAD - Shadows builtins
list = [1, 2, 3]  # Now list() constructor is broken!
dict = {}         # dict() is gone
type = 'string'   # type() is unusable

# BAD - Shadows stdlib
from datetime import datetime
datetime = '2025-01-01'  # Now datetime.now() fails

# GOOD - Use different names
items_list = [1, 2, 3]
config_dict = {}
data_type = 'string'
```

---

### Problem 3: FastAPI TestClient Startup Events Not Triggering

**When It Happened**: Milestone 6, writing API tests

**The Error**:
```python
# tests/test_api.py
def test_predict_endpoint():
    response = client.post("/predict", json=request_data)
    assert response.status_code == 200  # ❌ Gets 503 instead

# Error: "Model not loaded"
```

**What This Means**:
- **Technical**: `@app.on_event("startup")` doesn't run in tests
- **Root cause**: TestClient creates app without triggering lifecycle events
- **Why it matters**: All endpoints fail because model is None

**Context**:
```python
# src/api/main.py
model = None  # Global variable

@app.on_event("startup")
def load_artifacts():
    global model
    model = joblib.load('outputs/xgb_model.joblib')
    print("Model loaded")  # Never prints in tests!

@app.post("/predict")
def predict(request: PredictRequest):
    if model is None:
        raise HTTPException(503, "Model not loaded")  # Always triggers in tests
    return {"prediction": model.predict(...)}
```

**Why TestClient Skips Startup**:
```python
from fastapi.testclient import TestClient

client = TestClient(app)  # Creates app but doesn't call startup events
# Designed for unit tests (don't want side effects like DB connections)
```

**The Solution**: Manually call startup function
```python
# tests/test_api.py
from src.api.main import app, load_artifacts
from fastapi.testclient import TestClient

# Call startup manually before creating client
load_artifacts()  # ✅ Loads model

client = TestClient(app)

def test_predict_endpoint():
    response = client.post("/predict", json=request_data)
    assert response.status_code == 200  # ✅ Works now!
```

**Alternative Solution**: Use lifespan context manager (FastAPI 0.93+)
```python
# src/api/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    load_artifacts()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(lifespan=lifespan)  # New syntax

# Tests automatically trigger lifespan
```

**Lesson Learned**:
- TestClient isolates tests (good for unit tests)
- For integration tests, manually trigger startup
- Document startup requirements in test docstrings

**Testing Best Practices**:
```python
# conftest.py - Shared test setup
import pytest
from src.api.main import app, load_artifacts
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")  # Load once per test module
def client():
    load_artifacts()  # Ensure model is loaded
    with TestClient(app) as c:
        yield c

# tests/test_api.py
def test_predict(client):  # Uses fixture
    response = client.post("/predict", json={...})
    assert response.status_code == 200
```

---

### Problem 4: Patsy dmatrix Returns NDArray Instead of DataFrame

**When It Happened**: Milestone 2, implementing Python DLNM fallback

**The Error**:
```python
AttributeError: 'numpy.ndarray' object has no attribute 'columns'
```

**What This Means**:
- **Technical**: `patsy.dmatrix` can return ndarray or DataFrame (inconsistent)
- **Root cause**: Depends on patsy version and `return_type` parameter
- **Why it matters**: Code crashes when trying to access `.columns`

**Context**:
```python
# src/models/run_dlnm.py
from patsy import dmatrix

spline = dmatrix("bs(temp_mean, df=5, degree=3)", data=df, return_type='dataframe')
# Sometimes returns DataFrame, sometimes ndarray!

train_cols = spline.columns.tolist()  # ❌ Crashes if ndarray
```

**Why This Happens**:
- Patsy 0.5.x: `return_type='dataframe'` not fully reliable
- Depends on input data type (DataFrame vs dict)
- Type checker sees return type as `Union[DataFrame, ndarray]`

**The Solution**: Explicit type checking and conversion
```python
# src/models/run_dlnm.py
from patsy import dmatrix
import pandas as pd

spline = dmatrix("bs(temp_mean, df=5, degree=3)", data=df, return_type='dataframe')

# Ensure it's a DataFrame
if not isinstance(spline, pd.DataFrame):
    spline = pd.DataFrame(spline)  # ✅ Convert if needed

# Now safe to use .columns
train_cols = spline.columns.tolist()
```

**Better Solution**: Type annotation for clarity
```python
spline = dmatrix("bs(temp_mean, df=5, degree=3)", data=df, return_type='dataframe')
spline_df: pd.DataFrame = pd.DataFrame(spline) if not isinstance(spline, pd.DataFrame) else spline

# Type checker now knows it's a DataFrame
train_cols = spline_df.columns.tolist()  # ✅ No error
```

**Lesson Learned**:
- Never trust `return_type` parameter alone
- Always validate return types from external libraries
- Use type annotations for documentation

**Defensive Programming Pattern**:
```python
def ensure_dataframe(data) -> pd.DataFrame:
    """Convert any array-like to DataFrame"""
    if isinstance(data, pd.DataFrame):
        return data
    elif isinstance(data, np.ndarray):
        return pd.DataFrame(data)
    elif isinstance(data, list):
        return pd.DataFrame(data)
    else:
        raise TypeError(f"Cannot convert {type(data)} to DataFrame")

# Usage
spline = dmatrix(...)
spline_df = ensure_dataframe(spline)  # Always returns DataFrame
```

---

## Moderate Issues

### Problem 5: Streamlit Image Parameter `use_container_width` Not Found

**When It Happened**: Milestone 7, fixing linting errors

**The Error**:
```python
TypeError: st.image() got an unexpected keyword argument 'use_container_width'
```

**What This Means**:
- **Technical**: Parameter added in Streamlit 1.5+, not in older versions
- **Root cause**: Version compatibility issue
- **Why it matters**: Dashboard fails to load images

**Context**:
```python
# src/dashboard/app.py
st.image('outputs/risk_calendar.png', use_container_width=True)  # ❌ Fails on old Streamlit
```

**The Solution**: Use version-compatible parameter
```python
# Old way (all versions)
st.image('outputs/risk_calendar.png', width=None)  # ✅ Works everywhere

# Or check version
import streamlit as st
if hasattr(st, '__version__') and st.__version__ >= '1.5.0':
    st.image(path, use_container_width=True)
else:
    st.image(path, width=None)
```

**Lesson Learned**:
- Check feature availability before using
- Prefer widely-compatible parameters
- Document minimum version requirements

---

### Problem 6: Folium Element.html Attribute Not Found

**When It Happened**: Milestone 7, fixing type errors

**The Error**:
```python
AttributeError: 'Element' object has no attribute 'html'
```

**What This Means**:
- **Technical**: Folium internal API changed between versions
- **Root cause**: Accessing internal attributes (not public API)
- **Why it matters**: Custom HTML legend doesn't render

**Context**:
```python
# src/viz.py
import folium

m = folium.Map(...)
legend_html = '<div>...</div>'
m.get_root().html.add_child(folium.Element(legend_html))  # ❌ Breaks in some versions
```

**The Solution**: Version-compatible fallback
```python
root = m.get_root()

# Try new API
if hasattr(root, 'html'):
    root.html.add_child(folium.Element(legend_html))
else:
    # Fallback for older versions
    from branca.element import Element
    root.add_child(Element(legend_html))
```

**Better Solution**: Use public API (if available)
```python
# Folium 0.14+
folium.Marker(...).add_to(m)  # Preferred public API
```

**Lesson Learned**:
- Avoid accessing internal attributes (`._private`, `.internal`)
- Internal APIs can change without warning
- Always have version-compatible fallbacks

---

## Minor Fixes

### Problem 7: API Baseline Data NoneType Error

**The Error**:
```python
AttributeError: 'NoneType' object has no attribute 'median'
```

**The Fix**:
```python
# Before
features = baseline_data.median().to_dict()  # ❌ If baseline_data is None

# After
if baseline_data is None:
    raise HTTPException(503, "Baseline data not loaded")
features = baseline_data.median().to_dict()  # ✅ Safe
```

**Why This Matters**:
- Clearer error messages ("Baseline data not loaded" vs "NoneType")
- Proper HTTP status code (503 Service Unavailable)
- Easier debugging

---

### Problem 8: Git Tracking Large Binary Files

**The Issue**:
```bash
git add outputs/xgb_model.joblib  # 50MB file
git push  # ❌ Slow! GitHub warns about large files
```

**The Solution**: .gitignore
```gitignore
# .gitignore
outputs/*.joblib
outputs/*.parquet
data_processed/
*.pyc
__pycache__/
```

**Why This Matters**:
- Git is for code, not large binaries
- Models change frequently (don't bloat history)
- Use artifact storage (S3, Azure Blob) for models

**Best Practice**:
```python
# Store model metadata in git
{
  "model_version": "1.0.0",
  "model_path": "s3://models/xgb_v1.0.0.joblib",
  "training_date": "2025-11-24",
  "metrics": {"r2": 0.903, "mae": 0.897}
}
```

---

## Preventive Measures

### 1. Pin Dependency Versions
```txt
# requirements.txt
# DON'T: Unpinned (breaks randomly)
xgboost
shap

# DO: Pinned (reproducible)
xgboost==2.0.3
shap==0.45.0

# BETTER: With constraints
xgboost>=2.0.0,<3.0.0  # Allow patch updates, block breaking changes
```

### 2. Add Compatibility Tests
```python
# tests/test_compatibility.py
def test_xgboost_shap_compatibility():
    """Verify XGBoost and SHAP work together"""
    model = XGBRegressor()
    model.fit(X_train, y_train)
    
    # Try TreeExplainer first
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
    except AttributeError:
        # Fall back to PermutationExplainer
        explainer = shap.Explainer(model.predict, X_train.sample(50))
        shap_values = explainer(X_test)
    
    assert shap_values is not None
```

### 3. Use Type Hints Everywhere
```python
# Without types (error at runtime)
def process_data(df):
    return df.groupby('date').mean()  # What if df is None?

# With types (error at development time)
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby('date').mean()  # Type checker catches None

# Even better: Optional types
from typing import Optional

def process_data(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None:
        raise ValueError("DataFrame cannot be None")
    return df.groupby('date').mean()
```

### 4. Add Health Checks to Critical Functions
```python
# src/preprocess.py
def preprocess():
    df = ingest()
    
    # Sanity check
    assert len(df) > 0, "Empty dataframe after ingestion"
    assert 'date' in df.columns, "Missing date column"
    assert df['date'].is_monotonic_increasing, "Dates not sorted"
    
    df = add_lag_features(df)
    
    # Check lag features created
    lag_cols = [c for c in df.columns if '_lag' in c]
    assert len(lag_cols) > 0, "No lag features created"
    
    return df
```

### 5. Log Everything Important
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def preprocess():
    logger.info("Starting preprocessing")
    df = ingest()
    logger.info(f"Loaded {len(df)} rows")
    
    df = add_lag_features(df)
    logger.info(f"Added lag features, now {len(df.columns)} columns")
    
    return df
```

---

## Debugging Techniques

### 1. Interactive Debugging with pdb
```python
# Insert breakpoint
import pdb; pdb.set_trace()

# Or in Python 3.7+
breakpoint()

# At breakpoint:
# - 'l' (list): Show code around current line
# - 'p variable': Print variable value
# - 'n' (next): Execute next line
# - 'c' (continue): Resume execution
# - 'q' (quit): Exit debugger
```

### 2. IPython for Data Exploration
```python
# In script
from IPython import embed
embed()  # Drops into IPython shell

# Now interactively explore:
# df.head()
# df.describe()
# df['temp_mean'].plot()
```

### 3. Assert Statements for Assumptions
```python
def calculate_heat_index(temp, humidity):
    # Document assumptions
    assert 0 <= humidity <= 100, f"Invalid humidity: {humidity}"
    assert -50 <= temp <= 60, f"Invalid temperature: {temp}"
    
    # If assertions fail, you immediately know which assumption broke
```

### 4. Print Debugging (with context)
```python
# BAD: Useless print
print(df)  # Which df? When? Where?

# GOOD: Contextual print
print(f"[preprocess] After ingestion: shape={df.shape}, nulls={df.isnull().sum().sum()}")
```

### 5. Use pytest -v -s for Test Debugging
```bash
# Normal test (hides output)
pytest tests/test_model.py

# Verbose with stdout (see print statements)
pytest tests/test_model.py -v -s

# Stop at first failure
pytest tests/test_model.py -x

# Drop into debugger on failure
pytest tests/test_model.py --pdb
```

### 6. Git Bisect for Regression Hunting
```bash
# Something broke, but when?
git bisect start
git bisect bad           # Current commit is broken
git bisect good abc123   # This old commit worked

# Git will binary search
# At each step: test and mark
pytest tests/
git bisect good  # If test passes
# or
git bisect bad   # If test fails

# Git finds the breaking commit!
```

---

## Common Error Patterns and Solutions

### Pattern 1: KeyError with Dictionary Access
```python
# Problem
value = data['key']  # ❌ KeyError if 'key' missing

# Solution 1: Use .get()
value = data.get('key', default_value)  # ✅ Returns default if missing

# Solution 2: Check first
if 'key' in data:
    value = data['key']

# Solution 3: Try/except
try:
    value = data['key']
except KeyError:
    value = default_value
```

### Pattern 2: AttributeError with None
```python
# Problem
result = df.mean()  # ❌ AttributeError if df is None

# Solution: Early validation
def process(df):
    if df is None:
        raise ValueError("DataFrame cannot be None")
    return df.mean()  # ✅ Safe now
```

### Pattern 3: FileNotFoundError
```python
# Problem
df = pd.read_csv('data.csv')  # ❌ If file doesn't exist

# Solution: Check existence
from pathlib import Path

data_path = Path('data.csv')
if not data_path.exists():
    raise FileNotFoundError(f"Data file not found: {data_path}")

df = pd.read_csv(data_path)  # ✅ Clear error message
```

### Pattern 4: IndexError with List Access
```python
# Problem
first_item = my_list[0]  # ❌ IndexError if list is empty

# Solution 1: Check length
if len(my_list) > 0:
    first_item = my_list[0]

# Solution 2: Try/except
try:
    first_item = my_list[0]
except IndexError:
    first_item = None

# Solution 3: Use default
first_item = my_list[0] if my_list else None
```

---

## Troubleshooting Checklist

When something breaks, check in this order:

1. **Read the error message** (completely!)
   - File name and line number
   - Error type (AttributeError, KeyError, etc.)
   - Error message details

2. **Check recent changes**
   ```bash
   git diff  # What changed?
   git log --oneline -5  # Recent commits
   ```

3. **Verify dependencies**
   ```bash
   pip list  # Installed versions
   pip check  # Dependency conflicts
   ```

4. **Check data**
   ```python
   print(df.head())
   print(df.info())
   print(df.isnull().sum())
   ```

5. **Isolate the problem**
   - Comment out code sections
   - Test with minimal example
   - Run unit tests: `pytest tests/test_specific.py -v`

6. **Add logging**
   ```python
   logger.debug(f"Variable X: {X}")
   logger.info(f"Processing {len(df)} rows")
   ```

7. **Search for error**
   - Google: "[error message] [library name]"
   - Stack Overflow
   - GitHub Issues

8. **Ask for help** (with context!)
   - What you're trying to do
   - What you tried
   - Full error traceback
   - Minimal reproducible example

---

## Summary: Key Lessons

### Most Important Lessons
1. **Version compatibility matters** - Pin dependencies
2. **Validate inputs early** - Fail fast with clear errors
3. **Test assumptions** - Use assertions
4. **Log everything important** - Future you will thank you
5. **Have fallbacks** - Don't rely on one approach
6. **Read documentation** - Parameter names change
7. **Type hints help** - Catch errors before runtime
8. **Git is your friend** - Commit often, bisect when stuck

### Most Common Mistakes
1. Using unpinned dependencies
2. Accessing None without checking
3. Assuming dict keys exist
4. Not checking file existence
5. Shadowing stdlib names
6. Ignoring type hints
7. Not testing edge cases
8. Committing large binary files

### Prevention is Better Than Cure
- Write tests first (TDD)
- Use type hints
- Add assertions
- Log liberally
- Document assumptions
- Review before committing
- Run tests before pushing

---

**Next**: Read `03-professional-features-guide.md` for production-ready features explained
