"""Pydantic schemas for API request/response validation (Milestone 6)."""
from __future__ import annotations
from datetime import date as date_type
from pydantic import BaseModel, Field


class ForecastDay(BaseModel):
    """Single day of forecast input."""
    date: date_type = Field(..., description="Forecast date")
    temp_mean: float = Field(..., description="Mean temperature (°C)")
    rel_humidity: float = Field(..., ge=0, le=100, description="Relative humidity (%)")
    pm25: float = Field(..., ge=0, description="PM2.5 concentration (µg/m³)")


class PredictRequest(BaseModel):
    """Request for daily risk prediction."""
    region_id: str = Field(default="R1", description="Region identifier")
    forecast: list[ForecastDay] = Field(..., description="5-day forecast data")


class DriverFeature(BaseModel):
    """Top driver feature with SHAP contribution."""
    feature: str = Field(..., description="Feature name")
    contribution: float = Field(..., description="SHAP value contribution")


class DayPrediction(BaseModel):
    """Prediction for a single day."""
    date: date_type = Field(..., description="Forecast date")
    risk_score: float = Field(..., ge=0, le=1, description="Normalized risk score (0-1)")
    expected_admissions: float = Field(..., ge=0, description="Expected daily admissions")
    top_drivers: list[DriverFeature] = Field(..., description="Top 3 SHAP drivers")


class PredictResponse(BaseModel):
    """Response with daily predictions."""
    region_id: str
    predictions: list[DayPrediction]


class AlertRequest(BaseModel):
    """Request to check if alert should be triggered."""
    region_id: str = Field(default="R1")
    current_temp_mean: float = Field(..., description="Current mean temperature")
    threshold: float = Field(default=None, description="Custom threshold; uses 90th percentile if None")


class AlertResponse(BaseModel):
    """Alert trigger response."""
    triggered: bool = Field(..., description="Whether alert is triggered")
    threshold_value: float = Field(..., description="Threshold used")
    current_value: float = Field(..., description="Current exposure value")
    expected_admissions: float = Field(..., description="Expected admissions if triggered")
    recommended_actions: list[str] = Field(..., description="Recommended public health actions")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    data_available: bool
