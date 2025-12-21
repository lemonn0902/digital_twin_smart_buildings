"""
Forecasting service for energy consumption and occupancy prediction.
Uses trained LSTM models to generate forecasts.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler

try:
    from tensorflow import keras
except ImportError:
    keras = None

from core.utils.model_loader import get_model_path
from core.services.timeseries_service import timeseries_service


# Forecasting parameters (must match training script)
SEQUENCE_LENGTH = 24  # Use 24 hours of history for energy
FORECAST_HORIZON = 24  # Predict next 24 hours for energy
ENERGY_FEATURES = ["energy", "temperature", "humidity"]

# Occupancy prediction parameters
OCCUPANCY_SEQUENCE_LENGTH = 12  # Use 12 hours of history
OCCUPANCY_FORECAST_HORIZON = 12  # Predict next 12 hours
OCCUPANCY_FEATURES = ["occupancy", "hour_sin", "hour_cos", "dow_sin", "dow_cos", "energy"]


@lru_cache(maxsize=1)
def _load_energy_model() -> Optional[Any]:
    """
    Lazily load the trained energy forecasting LSTM model.
    
    Returns None if model cannot be loaded.
    """
    if keras is None:
        return None
    
    model_path = get_model_path("forecasting", "lstm_energy.h5")
    try:
        return keras.models.load_model(model_path)
    except Exception:
        # In production, log this error with details
        return None


@lru_cache(maxsize=1)
def _load_energy_scaler() -> Optional[MinMaxScaler]:
    """Load the scaler used during energy model training."""
    scaler_path = get_model_path("forecasting", "lstm_energy_scaler.pkl")
    try:
        return joblib.load(scaler_path)
    except Exception:
        return None


def _prepare_historical_data(
    building_id: str,
    hours: int = SEQUENCE_LENGTH
) -> Optional[pd.DataFrame]:
    """
    Fetch and prepare historical data for forecasting.
    
    Args:
        building_id: Building identifier
        hours: Number of hours of history to fetch
    
    Returns:
        DataFrame with required features, or None if unavailable
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    try:
        df = timeseries_service.get_metrics(
            building_id=building_id,
            zone_id=None,
            metrics=ENERGY_FEATURES,
            start_time=start_time,
            end_time=end_time,
            resolution_minutes=60  # Hourly data
        )
        
        if df.empty:
            return None
        
        # Pivot to get metrics as columns
        if "metric" in df.columns:
            df = df.pivot_table(
                index="timestamp",
                columns="metric",
                values="value",
                aggfunc="mean"
            ).reset_index()
        
        # Ensure we have all required features
        for feature in ENERGY_FEATURES:
            if feature not in df.columns:
                return None
        
        # Sort by timestamp and take last SEQUENCE_LENGTH rows
        df = df.sort_values("timestamp").tail(SEQUENCE_LENGTH)
        
        if len(df) < SEQUENCE_LENGTH:
            return None
        
        return df[ENERGY_FEATURES]
    
    except Exception:
        return None


def _generate_synthetic_history(hours: int = SEQUENCE_LENGTH) -> pd.DataFrame:
    """
    Generate synthetic historical data as fallback.
    Creates realistic patterns for energy, temperature, and humidity.
    """
    timestamps = pd.date_range(
        end=datetime.utcnow(),
        periods=hours,
        freq="1H"
    )
    
    hours_of_day = timestamps.hour
    day_of_week = timestamps.dayofweek
    
    # Energy pattern: higher during business hours
    energy_base = 100
    energy_pattern = 40 * np.sin(2 * np.pi * (hours_of_day - 8) / 24)
    energy_weekend = np.where(day_of_week >= 5, -20, 0)
    energy = energy_base + energy_pattern + energy_weekend + np.random.normal(0, 5, len(timestamps))
    energy = np.maximum(energy, 10)
    
    # Temperature pattern: daily cycle
    temperature = 22 + 5 * np.sin(2 * np.pi * hours_of_day / 24) + np.random.normal(0, 1, len(timestamps))
    
    # Humidity pattern
    humidity = 50 + 15 * np.sin(2 * np.pi * hours_of_day / 24) + np.random.normal(0, 3, len(timestamps))
    humidity = np.clip(humidity, 0, 100)
    
    return pd.DataFrame({
        "energy": energy,
        "temperature": temperature,
        "humidity": humidity
    }, index=timestamps)


def forecast_energy_consumption(
    building_id: str,
    horizon_hours: int = FORECAST_HORIZON
) -> Dict[str, Any]:
    """
    Forecast energy consumption for the next N hours.
    
    Args:
        building_id: Building identifier
        horizon_hours: Number of hours to forecast (default: 24)
    
    Returns:
        Dictionary with:
        - forecast: List of forecasted values with timestamps
        - confidence: Optional confidence intervals
        - model_available: Boolean indicating if model was used
    """
    # Load model and scaler
    model = _load_energy_model()
    scaler = _load_energy_scaler()
    
    if model is None or scaler is None:
        # Fallback: generate synthetic forecast
        return _generate_synthetic_forecast(building_id, horizon_hours)
    
    # Get historical data
    historical_df = _prepare_historical_data(building_id, SEQUENCE_LENGTH)
    
    if historical_df is None or len(historical_df) < SEQUENCE_LENGTH:
        # Fallback to synthetic data
        historical_df = _generate_synthetic_history(SEQUENCE_LENGTH)
    
    # Prepare input sequence
    historical_values = historical_df[ENERGY_FEATURES].values
    
    # Scale the data
    historical_scaled = scaler.transform(historical_values)
    
    # Reshape for LSTM: (1, sequence_length, n_features)
    input_sequence = historical_scaled.reshape(1, SEQUENCE_LENGTH, len(ENERGY_FEATURES))
    
    # Generate forecast
    try:
        forecast_scaled = model.predict(input_sequence, verbose=0)
        
        # The model predicts energy for FORECAST_HORIZON hours (24 by default)
        # We may need to truncate or extend based on requested horizon_hours
        predicted_hours = min(horizon_hours, len(forecast_scaled[0]))
        forecast_energy_scaled = forecast_scaled[0, :predicted_hours]
        
        # Get the last known scaled values for temperature and humidity
        # We'll use these for inverse transform (scaler needs all features)
        last_scaled = historical_scaled[-1:]
        
        # Create array for inverse transform
        # Use forecasted energy, and repeat last known temp/humidity for each hour
        forecast_array = np.zeros((predicted_hours, len(ENERGY_FEATURES)))
        forecast_array[:, 0] = forecast_energy_scaled  # Energy forecast
        forecast_array[:, 1] = last_scaled[0, 1]  # Use last known temperature (constant)
        forecast_array[:, 2] = last_scaled[0, 2]  # Use last known humidity (constant)
        
        # Inverse transform to get actual energy values
        forecast_actual = scaler.inverse_transform(forecast_array)
        energy_forecast = forecast_actual[:, 0]
        
        actual_horizon = predicted_hours
        
        # Generate timestamps for forecast
        start_time = datetime.utcnow()
        forecast_timestamps = pd.date_range(
            start=start_time,
            periods=actual_horizon,
            freq="1H"
        )
        
        # Create forecast points
        forecast_points = [
            {
                "timestamp": ts.isoformat(),
                "energy_kwh": float(value),
                "confidence_lower": float(value * 0.9),  # Simple confidence estimate
                "confidence_upper": float(value * 1.1),
            }
            for ts, value in zip(forecast_timestamps, energy_forecast)
        ]
        
        return {
            "forecast": forecast_points,
            "model_available": True,
            "horizon_hours": horizon_hours,
        }
    
    except Exception as e:
        # Fallback on any error
        return _generate_synthetic_forecast(building_id, horizon_hours)


@lru_cache(maxsize=1)
def _load_occupancy_model() -> Optional[Any]:
    """
    Lazily load the trained occupancy prediction LSTM model.
    
    Returns None if model cannot be loaded.
    """
    if keras is None:
        return None
    
    model_path = get_model_path("forecasting", "lstm_occupancy.h5")
    try:
        return keras.models.load_model(model_path)
    except Exception:
        # In production, log this error with details
        return None


@lru_cache(maxsize=1)
def _load_occupancy_scaler() -> Optional[MinMaxScaler]:
    """Load the scaler used during occupancy model training."""
    scaler_path = get_model_path("forecasting", "lstm_occupancy_scaler.pkl")
    try:
        return joblib.load(scaler_path)
    except Exception:
        return None


def _prepare_occupancy_historical_data(
    building_id: str,
    hours: int = OCCUPANCY_SEQUENCE_LENGTH
) -> Optional[pd.DataFrame]:
    """
    Fetch and prepare historical data for occupancy prediction.
    Includes time features (hour, dayofweek) encoded cyclically.
    
    Args:
        building_id: Building identifier
        hours: Number of hours of history to fetch
    
    Returns:
        DataFrame with required features including time features, or None if unavailable
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    try:
        df = timeseries_service.get_metrics(
            building_id=building_id,
            zone_id=None,
            metrics=["occupancy", "energy"],
            start_time=start_time,
            end_time=end_time,
            resolution_minutes=60  # Hourly data
        )
        
        if df.empty:
            return None
        
        # Pivot to get metrics as columns
        if "metric" in df.columns:
            df = df.pivot_table(
                index="timestamp",
                columns="metric",
                values="value",
                aggfunc="mean"
            ).reset_index()
        
        # Ensure we have required features
        if "occupancy" not in df.columns or "energy" not in df.columns:
            return None
        
        # Sort by timestamp and take last OCCUPANCY_SEQUENCE_LENGTH rows
        df = df.sort_values("timestamp").tail(OCCUPANCY_SEQUENCE_LENGTH)
        
        if len(df) < OCCUPANCY_SEQUENCE_LENGTH:
            return None
        
        # Add time features
        df = df.copy()
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        df["dayofweek"] = pd.to_datetime(df["timestamp"]).dt.dayofweek
        
        # Cyclical encoding
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
        df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
        df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)
        
        return df[OCCUPANCY_FEATURES]
    
    except Exception:
        return None


def _generate_synthetic_occupancy_history(hours: int = OCCUPANCY_SEQUENCE_LENGTH) -> pd.DataFrame:
    """
    Generate synthetic historical occupancy data with time features as fallback.
    """
    timestamps = pd.date_range(
        end=datetime.utcnow(),
        periods=hours,
        freq="1H"
    )
    
    hours_of_day = timestamps.hour
    day_of_week = timestamps.dayofweek
    
    # Occupancy pattern: higher during business hours
    occupancy = np.where(
        (hours_of_day >= 9) & (hours_of_day < 17) & (day_of_week < 5),
        0.7 + np.random.normal(0, 0.1, len(timestamps)),
        0.1 + np.random.normal(0, 0.05, len(timestamps))
    )
    occupancy = np.clip(occupancy, 0, 1)
    
    # Energy pattern (needed as feature)
    energy = 100 + 30 * np.sin(2 * np.pi * (hours_of_day - 8) / 24)
    energy = np.maximum(energy, 10)
    
    # Time features
    hour_sin = np.sin(2 * np.pi * hours_of_day / 24)
    hour_cos = np.cos(2 * np.pi * hours_of_day / 24)
    dow_sin = np.sin(2 * np.pi * day_of_week / 7)
    dow_cos = np.cos(2 * np.pi * day_of_week / 7)
    
    return pd.DataFrame({
        "occupancy": occupancy,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "dow_sin": dow_sin,
        "dow_cos": dow_cos,
        "energy": energy
    }, index=timestamps)


def forecast_occupancy(
    building_id: str,
    horizon_hours: int = OCCUPANCY_FORECAST_HORIZON
) -> Dict[str, Any]:
    """
    Forecast occupancy for the next N hours.
    
    Args:
        building_id: Building identifier
        horizon_hours: Number of hours to forecast (default: 12, max: 12)
    
    Returns:
        Dictionary with:
        - forecast: List of forecasted values with timestamps
        - confidence: Optional confidence intervals
        - model_available: Boolean indicating if model was used
    """
    # Limit horizon to model's training horizon
    horizon_hours = min(horizon_hours, OCCUPANCY_FORECAST_HORIZON)
    
    # Load model and scaler
    model = _load_occupancy_model()
    scaler = _load_occupancy_scaler()
    
    if model is None or scaler is None:
        # Fallback: generate synthetic forecast
        return _generate_synthetic_occupancy_forecast(building_id, horizon_hours)
    
    # Get historical data
    historical_df = _prepare_occupancy_historical_data(building_id, OCCUPANCY_SEQUENCE_LENGTH)
    
    if historical_df is None or len(historical_df) < OCCUPANCY_SEQUENCE_LENGTH:
        # Fallback to synthetic data
        historical_df = _generate_synthetic_occupancy_history(OCCUPANCY_SEQUENCE_LENGTH)
    
    # Prepare input sequence
    historical_values = historical_df[OCCUPANCY_FEATURES].values
    
    # Scale the data
    historical_scaled = scaler.transform(historical_values)
    
    # Reshape for LSTM: (1, sequence_length, n_features)
    input_sequence = historical_scaled.reshape(1, OCCUPANCY_SEQUENCE_LENGTH, len(OCCUPANCY_FEATURES))
    
    # Generate forecast
    try:
        forecast_scaled = model.predict(input_sequence, verbose=0)
        
        # The model predicts occupancy for OCCUPANCY_FORECAST_HORIZON hours (12 by default)
        predicted_hours = min(horizon_hours, len(forecast_scaled[0]))
        forecast_occupancy_scaled = forecast_scaled[0, :predicted_hours]
        
        # Get the last known scaled values for other features
        # We'll use these for inverse transform (scaler needs all features)
        last_scaled = historical_scaled[-1:]
        
        # Create array for inverse transform
        # Use forecasted occupancy, and repeat last known values for other features
        forecast_array = np.zeros((predicted_hours, len(OCCUPANCY_FEATURES)))
        forecast_array[:, 0] = forecast_occupancy_scaled  # Occupancy forecast
        forecast_array[:, 1] = last_scaled[0, 1]  # hour_sin (will be updated with future times)
        forecast_array[:, 2] = last_scaled[0, 2]  # hour_cos (will be updated with future times)
        forecast_array[:, 3] = last_scaled[0, 3]  # dow_sin (will be updated with future times)
        forecast_array[:, 4] = last_scaled[0, 4]  # dow_cos (will be updated with future times)
        forecast_array[:, 5] = last_scaled[0, 5]  # energy (use last known)
        
        # Update time features for future timestamps
        start_time = datetime.utcnow()
        future_timestamps = pd.date_range(
            start=start_time,
            periods=predicted_hours,
            freq="1H"
        )
        
        future_hours = future_timestamps.hour
        future_dow = future_timestamps.dayofweek
        
        forecast_array[:, 1] = np.sin(2 * np.pi * future_hours / 24)  # hour_sin
        forecast_array[:, 2] = np.cos(2 * np.pi * future_hours / 24)  # hour_cos
        forecast_array[:, 3] = np.sin(2 * np.pi * future_dow / 7)  # dow_sin
        forecast_array[:, 4] = np.cos(2 * np.pi * future_dow / 7)  # dow_cos
        
        # Inverse transform to get actual occupancy values
        forecast_actual = scaler.inverse_transform(forecast_array)
        occupancy_forecast = forecast_actual[:, 0]
        
        # Clip occupancy to valid range [0, 1]
        occupancy_forecast = np.clip(occupancy_forecast, 0, 1)
        
        actual_horizon = predicted_hours
        
        # Create forecast points
        forecast_points = [
            {
                "timestamp": ts.isoformat(),
                "occupancy": float(value),
                "confidence_lower": float(max(0, value - 0.1)),  # Simple confidence estimate
                "confidence_upper": float(min(1, value + 0.1)),
            }
            for ts, value in zip(future_timestamps, occupancy_forecast)
        ]
        
        return {
            "forecast": forecast_points,
            "model_available": True,
            "horizon_hours": actual_horizon,
        }
    
    except Exception as e:
        # Fallback on any error
        return _generate_synthetic_occupancy_forecast(building_id, horizon_hours)


def _generate_synthetic_occupancy_forecast(
    building_id: str,
    horizon_hours: int
) -> Dict[str, Any]:
    """
    Generate synthetic occupancy forecast as fallback when model is unavailable.
    """
    start_time = datetime.utcnow()
    timestamps = pd.date_range(
        start=start_time,
        periods=horizon_hours,
        freq="1H"
    )
    
    hours_of_day = timestamps.hour
    day_of_week = timestamps.dayofweek
    
    # Simple pattern-based forecast
    occupancy_forecast = np.where(
        (hours_of_day >= 9) & (hours_of_day < 17) & (day_of_week < 5),
        0.7 + np.random.normal(0, 0.1, len(timestamps)),
        0.1 + np.random.normal(0, 0.05, len(timestamps))
    )
    occupancy_forecast = np.clip(occupancy_forecast, 0, 1)
    
    forecast_points = [
        {
            "timestamp": ts.isoformat(),
            "occupancy": float(value),
            "confidence_lower": float(max(0, value - 0.15)),
            "confidence_upper": float(min(1, value + 0.15)),
        }
        for ts, value in zip(timestamps, occupancy_forecast)
    ]
    
    return {
        "forecast": forecast_points,
        "model_available": False,
        "horizon_hours": horizon_hours,
    }


def _generate_synthetic_forecast(
    building_id: str,
    horizon_hours: int
) -> Dict[str, Any]:
    """
    Generate synthetic forecast as fallback when model is unavailable.
    """
    start_time = datetime.utcnow()
    timestamps = pd.date_range(
        start=start_time,
        periods=horizon_hours,
        freq="1H"
    )
    
    hours_of_day = timestamps.hour
    
    # Simple pattern-based forecast
    base_energy = 120
    pattern = 30 * np.sin(2 * np.pi * (hours_of_day - 8) / 24)
    energy_forecast = base_energy + pattern + np.random.normal(0, 5, len(timestamps))
    energy_forecast = np.maximum(energy_forecast, 10)
    
    forecast_points = [
        {
            "timestamp": ts.isoformat(),
            "energy_kwh": float(value),
            "confidence_lower": float(value * 0.85),
            "confidence_upper": float(value * 1.15),
        }
        for ts, value in zip(timestamps, energy_forecast)
    ]
    
    return {
        "forecast": forecast_points,
        "model_available": False,
        "horizon_hours": horizon_hours,
    }
