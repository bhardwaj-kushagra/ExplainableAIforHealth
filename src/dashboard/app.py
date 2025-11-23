"""Streamlit dashboard for climate-CVD risk monitoring (Milestone 5).

Features:
- Date picker and forecast input
- Risk calendar visualization
- SHAP summary display
- Model metrics summary
"""
from __future__ import annotations
import streamlit as st
from pathlib import Path
import pandas as pd
import json
from datetime import datetime, timedelta
from PIL import Image

# Paths
OUTPUTS = Path('outputs')
METRICS = OUTPUTS / 'metrics.json'
RISK_CALENDAR = OUTPUTS / 'risk_calendar.png'
THRESHOLD_CURVE = OUTPUTS / 'threshold_curve.png'
SHAP_SUMMARY = OUTPUTS / 'shap_summary.png'
POLICY_STATEMENT = OUTPUTS / 'policy_statement.txt'
SPATIAL_MAP = OUTPUTS / 'spatial_risk_map.html'

st.set_page_config(
    page_title="Climate-CVD Risk Dashboard",
    page_icon="🫀",
    layout="wide"
)

st.title("🫀 Climate-Linked Cardiovascular Risk Dashboard")
st.markdown("**Explainable AI for Health**")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Select View", ["Overview", "Risk Calendar", "Model Explainability", "Forecast", "Policy Statement"])

# Load metrics
if METRICS.exists():
    with open(METRICS, 'r') as f:
        metrics = json.load(f)
else:
    metrics = {}

if page == "Overview":
    st.header("System Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Model R²", f"{metrics.get('test_r2', 0):.3f}" if metrics else "N/A")
    with col2:
        st.metric("Test MAE", f"{metrics.get('test_mae', 0):.3f}" if metrics else "N/A")
    with col3:
        st.metric("Test RMSE", f"{metrics.get('test_rmse', 0):.3f}" if metrics else "N/A")
    
    st.markdown("---")
    st.subheader("Model Performance")
    st.write("The XGBoost model achieves strong predictive performance on synthetic data:")
    st.write(f"- **Mean Absolute Error**: {metrics.get('test_mae', 'N/A')} admissions")
    st.write(f"- **R² Score**: {metrics.get('test_r2', 'N/A')}")
    
    st.markdown("---")
    st.subheader("Threshold Response Curve")
    if THRESHOLD_CURVE.exists():
        st.image(str(THRESHOLD_CURVE), width=None)
    else:
        st.warning("Threshold curve not yet generated. Run: `python src/viz.py`")

elif page == "Risk Calendar":
    st.header("Risk Calendar")
    st.markdown("Daily cardiovascular admissions heatmap by year and week")
    
    if RISK_CALENDAR.exists():
        st.image(str(RISK_CALENDAR), width=None)
    else:
        st.warning("Risk calendar not yet generated. Run: `python src/viz.py`")
    
    st.markdown("---")
    st.subheader("Spatial Risk Map")
    if SPATIAL_MAP.exists():
        with open(SPATIAL_MAP, 'r', encoding='utf-8') as f:
            html_content = f.read()
        try:
            import streamlit.components.v1 as components
            components.html(html_content, height=500)
        except AttributeError:
            st.markdown(html_content, unsafe_allow_html=True)
    else:
        st.warning("Spatial map not yet generated. Run: `python src/viz.py`")

elif page == "Model Explainability":
    st.header("SHAP Explainability")
    st.markdown("Understanding which features drive cardiovascular risk predictions")
    
    if SHAP_SUMMARY.exists():
        st.image(str(SHAP_SUMMARY), width=None)
    else:
        st.warning("SHAP summary not yet generated. Run: `python src/explainers.py`")
    
    st.markdown("---")
    st.subheader("Top Risk Drivers")
    top_features_file = OUTPUTS / 'shap_top_features.txt'
    if top_features_file.exists():
        with open(top_features_file, 'r') as f:
            st.text(f.read())
    else:
        st.info("Top features summary not available.")

elif page == "Forecast":
    st.header("5-Day Risk Forecast")
    st.markdown("Enter forecast meteorological data to predict cardiovascular risk")
    
    st.subheader("Input Forecast Data")
    
    with st.form("forecast_form"):
        col1, col2, col3 = st.columns(3)
        
        forecasts = []
        for i in range(5):
            st.markdown(f"**Day {i+1}** ({(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')})")
            c1, c2, c3 = st.columns(3)
            with c1:
                temp = st.number_input(f"Temp (°C) Day {i+1}", value=20.0, key=f"temp_{i}")
            with c2:
                humidity = st.number_input(f"Humidity (%) Day {i+1}", value=65.0, min_value=0.0, max_value=100.0, key=f"hum_{i}")
            with c3:
                pm25 = st.number_input(f"PM2.5 Day {i+1}", value=30.0, min_value=0.0, key=f"pm25_{i}")
            
            forecasts.append({
                'date': (datetime.now() + timedelta(days=i)).date(),
                'temp_mean': temp,
                'rel_humidity': humidity,
                'pm25': pm25
            })
        
        submitted = st.form_submit_button("Get Risk Predictions")
    
    if submitted:
        st.success("Forecast submitted! (API integration would return predictions here)")
        st.json(forecasts)
        st.info("To get live predictions, start the API: `uvicorn src.api.main:app --reload`")

elif page == "Policy Statement":
    st.header("Policy Statement")
    st.markdown("Evidence-based recommendations for public health decision-makers")
    
    if POLICY_STATEMENT.exists():
        with open(POLICY_STATEMENT, 'r', encoding='utf-8') as f:
            policy_text = f.read()
        st.text(policy_text)
        
        # Download button
        st.download_button(
            label="Download Policy Statement",
            data=policy_text,
            file_name="policy_statement.txt",
            mime="text/plain"
        )
    else:
        st.warning("Policy statement not yet generated. Run: `python src/models/produce_policy_statement.py`")

st.sidebar.markdown("---")
st.sidebar.info("**Data Source**: Synthetic (demonstration only)\n\n**Model**: XGBoost + SHAP\n\n**Version**: 1.0.0")
