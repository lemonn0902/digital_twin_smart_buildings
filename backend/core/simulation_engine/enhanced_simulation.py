from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from core.services.influxdb_service import query_time_series, query_time_series_stub


def simulate_occupancy_enhanced(
    building_id: str,
    start_time: datetime,
    end_time: datetime,
    resolution_minutes: int = 15,
    zone_id: Optional[str] = None
) -> pd.Series:
    """
    Enhanced occupancy simulation using historical patterns or realistic models.
    
    Uses InfluxDB if available, otherwise generates realistic synthetic data.
    """
    # Try to get historical data first
    try:
        df = query_time_series(
            building_id=building_id,
            zone_id=zone_id,
            metrics=["occupancy"],
            start_time=start_time - timedelta(days=7),  # Use past week as pattern
            end_time=start_time,
            resolution_minutes=resolution_minutes
        )
        
        if not df.empty:
            # Use historical average pattern
            hourly_pattern = df.groupby(df["timestamp"].dt.hour)["value"].mean()
            return _apply_pattern(start_time, end_time, resolution_minutes, hourly_pattern)
    except Exception:
        pass
    
    # Fallback: generate realistic synthetic occupancy
    timestamps = pd.date_range(start=start_time, end=end_time, freq=f"{resolution_minutes}min")
    
    occupancy_values = []
    for ts in timestamps:
        hour = ts.hour
        day_of_week = ts.weekday()  # 0 = Monday, 6 = Sunday
        
        # Base occupancy pattern: lower on weekends
        weekend_factor = 0.3 if day_of_week >= 5 else 1.0
        
        # Typical office hours pattern
        if 7 <= hour < 9:
            # Morning ramp-up
            occ = 0.2 + (hour - 7) * 0.3 * weekend_factor
        elif 9 <= hour < 12:
            # Peak morning
            occ = 0.7 + np.random.normal(0, 0.1) * weekend_factor
        elif 12 <= hour < 14:
            # Lunch dip
            occ = 0.4 + np.random.normal(0, 0.1) * weekend_factor
        elif 14 <= hour < 17:
            # Afternoon peak
            occ = 0.75 + np.random.normal(0, 0.1) * weekend_factor
        elif 17 <= hour < 19:
            # Evening ramp-down
            occ = 0.6 - (hour - 17) * 0.3 * weekend_factor
        else:
            # Night
            occ = 0.1 * weekend_factor
        
        occupancy_values.append(max(0, min(1, occ + np.random.normal(0, 0.05))))
    
    return pd.Series(occupancy_values, index=timestamps, name="occupancy")


def simulate_hvac_enhanced(
    occupancy_series: pd.Series,
    outdoor_temp: Optional[float] = None,
    setpoint_temp: float = 24.0
) -> pd.Series:
    """
    Enhanced HVAC simulation using occupancy, temperature, and time-of-day.
    
    More realistic energy consumption model.
    """
    if outdoor_temp is None:
        # Estimate outdoor temp based on time of year (simplified)
        month = occupancy_series.index[0].month
        outdoor_temp = 15.0 + 10.0 * np.sin(2 * np.pi * (month - 3) / 12)
    
    hvac_energy = []
    base_load = 1.0  # kW base HVAC system power
    
    for idx, ts in enumerate(occupancy_series.index):
        occ = occupancy_series.iloc[idx]
        hour = ts.hour
        
        # Temperature difference drives HVAC load
        temp_diff = abs(outdoor_temp - setpoint_temp)
        
        # Occupancy increases cooling/heating demand
        occupancy_load = 2.5 * occ
        
        # Time-of-day factors (pre-cooling in morning, etc.)
        time_factor = 1.0
        if 6 <= hour < 8:
            time_factor = 1.2  # Pre-cooling/pre-heating
        elif 22 <= hour or hour < 6:
            time_factor = 0.5  # Night setback
        
        # Calculate HVAC energy
        energy = base_load + occupancy_load + (temp_diff * 0.3) * time_factor
        hvac_energy.append(energy)
    
    return pd.Series(hvac_energy, index=occupancy_series.index, name="hvac_energy")


def simulate_thermal_enhanced(
    occupancy_series: pd.Series,
    hvac_energy: pd.Series,
    outdoor_temp: Optional[float] = None,
    initial_temp: float = 22.0
) -> pd.Series:
    """
    Enhanced thermal model with thermal mass and realistic dynamics.
    """
    if outdoor_temp is None:
        month = occupancy_series.index[0].month
        outdoor_temp = 15.0 + 10.0 * np.sin(2 * np.pi * (month - 3) / 12)
    
    temps = [initial_temp]
    thermal_mass = 0.85  # Thermal inertia factor
    
    for idx in range(1, len(occupancy_series)):
        prev_temp = temps[-1]
        occ = occupancy_series.iloc[idx]
        hvac = hvac_energy.iloc[idx]
        
        # Occupancy adds heat
        occupancy_heat = 0.5 * occ
        
        # HVAC cooling/heating effect
        setpoint = 24.0
        hvac_effect = -0.15 * (prev_temp - setpoint) * (hvac / 4.0)  # Cooling when hot
        
        # Outdoor temperature influence
        outdoor_influence = 0.05 * (outdoor_temp - prev_temp)
        
        # Thermal dynamics
        new_temp = (
            prev_temp * thermal_mass +
            (prev_temp + hvac_effect + occupancy_heat + outdoor_influence) * (1 - thermal_mass)
        )
        
        temps.append(new_temp)
    
    return pd.Series(temps, index=occupancy_series.index, name="temperature")


def _apply_pattern(
    start_time: datetime,
    end_time: datetime,
    resolution_minutes: int,
    hourly_pattern: pd.Series
) -> pd.Series:
    """Apply an hourly pattern to a time range."""
    timestamps = pd.date_range(start=start_time, end=end_time, freq=f"{resolution_minutes}min")
    values = []
    
    for ts in timestamps:
        hour = ts.hour
        base_value = hourly_pattern.get(hour, 0.5)
        # Add some variation
        value = base_value + np.random.normal(0, 0.05)
        values.append(max(0, min(1, value)))
    
    return pd.Series(values, index=timestamps, name="occupancy")
