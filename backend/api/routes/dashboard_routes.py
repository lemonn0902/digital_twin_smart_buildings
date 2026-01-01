from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Dict

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.services.data_service import data_service
from core.services.timeseries_service import timeseries_service
from core.services.action_state_service import action_state_service
from core.anomaly_engine.autoencoder_model import autoencoder_reconstruction_error
from core.anomaly_engine.isolation_forest import isolation_forest_scores
from core.suggestions_engine.smart_suggestions import suggestion_engine


router = APIRouter()

FEATURE_COLS = [
    "energy",
    "temperature",
    "humidity",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
]

EMISSION_FACTOR_T_PER_KWH = 0.000707  # ≈0.707 kg CO₂ per kWh


class DashboardResponse(BaseModel):
    building: Dict
    kpis: Dict[str, float]
    charts: List[Dict]
    carbon: Dict[str, float]
    alerts: List[Dict]
    anomalies: List[Dict]
    suggestions: List[Dict]
    applied_actions: List[Dict]
    actions_version: int


def _augment_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df.index.hour
    df["dayofweek"] = df.index.dayofweek
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
    df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7.0)
    df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7.0)
    return df.drop(columns=["hour", "dayofweek"])


def _normalize(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    lo = float(series.min())
    hi = float(series.max())
    if np.isclose(hi, lo):
        return pd.Series(0.0, index=series.index)
    return (series - lo) / (hi - lo)


def _build_anomalies(base_df: pd.DataFrame) -> pd.DataFrame:
    """Build anomaly detection results from time-series data."""
    if base_df.empty:
        return pd.DataFrame(columns=["timestamp", "score", "is_anomaly", "energy", "temperature", "occupancy"])
    
    # Ensure timestamp is a column, not index
    if base_df.index.name == "timestamp" or "timestamp" not in base_df.columns:
        if "timestamp" not in base_df.columns and base_df.index.name == "timestamp":
            base_df = base_df.reset_index()
    
    # Ensure required columns exist, fill missing ones with defaults
    required_cols = ["energy", "temperature", "humidity", "occupancy"]
    for col in required_cols:
        if col not in base_df.columns:
            if col == "humidity":
                # Default humidity if missing (typical indoor range)
                base_df[col] = 50.0
            else:
                base_df[col] = 0.0
    
    # Set timestamp as index for feature engineering
    feature_df = base_df.set_index("timestamp")[required_cols].copy()
    feature_df = _augment_time_features(feature_df)
    
    # Ensure all feature columns exist
    missing_features = [col for col in FEATURE_COLS if col not in feature_df.columns]
    for col in missing_features:
        feature_df[col] = 0.0
    
    ae_scores = autoencoder_reconstruction_error(feature_df, FEATURE_COLS)
    if_scores = isolation_forest_scores(feature_df, FEATURE_COLS)
    
    combined = 0.5 * _normalize(ae_scores) + 0.5 * _normalize(if_scores)
    feature_df = feature_df.assign(score=combined).reset_index()
    feature_df["is_anomaly"] = feature_df["score"] >= 0.85
    return feature_df


def _load_data_from_influxdb(building_id: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Load data from InfluxDB and transform to dashboard format.
    Returns DataFrame with columns: timestamp, energy, temperature, humidity, occupancy
    """
    try:
        # Query InfluxDB for all metrics across all zones
        metrics = ["energy", "temperature", "humidity", "occupancy"]
        df = timeseries_service.get_metrics(
            building_id=building_id,
            zone_id=None,  # Get all zones
            metrics=metrics,
            start_time=start_time,
            end_time=end_time,
            resolution_minutes=15
        )
        
        if df.empty:
            return pd.DataFrame()
        
        # Debug: Print DataFrame structure
        print(f"📊 InfluxDB raw DataFrame shape: {df.shape}, columns: {list(df.columns)}")
        if not df.empty:
            print(f"📊 Sample rows:\n{df.head(3)}")
        
        # InfluxDB returns: timestamp, metric, value, zone_id (potentially)
        # Transform to: timestamp, energy, temperature, humidity, occupancy
        # Aggregate across zones (sum for energy, mean for others)
        
        # Create pivot table with proper aggregation
        # First, ensure timestamp is datetime
        if "timestamp" not in df.columns:
            # Try alternative column names
            if "_time" in df.columns:
                df = df.rename(columns={"_time": "timestamp"})
            elif "time" in df.columns:
                df = df.rename(columns={"time": "timestamp"})
            else:
                print(f"❌ No timestamp column found. Available columns: {list(df.columns)}")
                return pd.DataFrame()
        
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            # Ensure timestamps are timezone-aware (UTC) for consistent comparisons
            if df["timestamp"].dt.tz is None:
                df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
            else:
                df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
        
        # Ensure we have 'metric' and 'value' columns
        if "metric" not in df.columns:
            if "_measurement" in df.columns:
                df = df.rename(columns={"_measurement": "metric"})
            else:
                print(f"❌ No metric column found. Available columns: {list(df.columns)}")
                return pd.DataFrame()
        
        if "value" not in df.columns:
            if "_value" in df.columns:
                df = df.rename(columns={"_value": "value"})
            else:
                print(f"❌ No value column found. Available columns: {list(df.columns)}")
                return pd.DataFrame()
        
        # Group by timestamp and metric, then aggregate
        result_rows = []
        for timestamp in df["timestamp"].unique():
            ts_data = df[df["timestamp"] == timestamp]
            row = {"timestamp": timestamp}
            
            for metric in metrics:
                metric_data = ts_data[ts_data["metric"] == metric]["value"]
                if len(metric_data) > 0:
                    if metric == "energy":
                        row[metric] = float(metric_data.sum())
                    else:
                        row[metric] = float(metric_data.mean())
                else:
                    row[metric] = 0.0
            
            result_rows.append(row)
        
        if not result_rows:
            return pd.DataFrame()
        
        pivot_df = pd.DataFrame(result_rows)
        
        # Ensure all required columns exist
        for metric in metrics:
            if metric not in pivot_df.columns:
                pivot_df[metric] = 0.0
        
        # Sort by timestamp
        pivot_df = pivot_df.sort_values("timestamp").reset_index(drop=True)
        
        return pivot_df
        
    except Exception as e:
        print(f"Failed to load from InfluxDB: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


@router.get("/overview/{building_id}", response_model=DashboardResponse)
async def dashboard_overview(building_id: str):
    """
    Aggregate KPIs, charts, anomalies, alerts, and suggestions for the monitoring dashboard.
    Uses InfluxDB as primary data source, falls back to CSV if unavailable.
    """
    try:
        # Use timezone-aware datetimes (UTC) to match InfluxDB timestamps
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=48)

        # Try InfluxDB first (realistic IoT data - matches production architecture)
        df = _load_data_from_influxdb(building_id, start_time, end_time)
        
        # Fallback to CSV if InfluxDB is empty or unavailable
        if df.empty:
            print("⚠️  InfluxDB data empty, falling back to CSV data...")
            df = data_service.get_data(start_time=start_time, end_time=end_time)
            if df.empty:
                df = data_service.get_data()
            print("✅ Using CSV data as fallback")
        else:
            print(f"✅ Loaded {len(df)} records from InfluxDB")

        if df.empty:
            raise HTTPException(status_code=404, detail="No telemetry available for dashboard.")

        # Ensure timestamp is datetime
        if "timestamp" not in df.columns:
            raise HTTPException(status_code=500, detail="DataFrame missing 'timestamp' column")
        
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        # Ensure timestamps are timezone-aware (UTC) for consistent comparisons
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        else:
            df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
        
        df = df.sort_values("timestamp").reset_index(drop=True)

        applied_actions = action_state_service.get_applied_actions(building_id)
        actions_version = action_state_service.get_version(building_id)

        total_applied_savings = float(
            sum(a.get("estimated_savings_kwh", 0.0) for a in applied_actions)
        )

        # Ensure required columns exist
        required_metrics = ["energy", "temperature", "occupancy"]
        for metric in required_metrics:
            if metric not in df.columns:
                print(f"⚠️  Warning: Missing column '{metric}', filling with 0.0")
                df[metric] = 0.0
        
        # Add humidity if missing (default to 50%)
        if "humidity" not in df.columns:
            df["humidity"] = 50.0

        last_24h_start = end_time - timedelta(hours=24)
        recent_df = df[df["timestamp"] >= last_24h_start].copy()
        if recent_df.empty:
            recent_df = df.tail(96).copy()  # fallback ~24h assuming 15m data

        if not recent_df.empty and total_applied_savings > 0:
            recent_energy_total = float(recent_df["energy"].sum())
            if recent_energy_total > 0:
                reduction_ratio = min(0.30, total_applied_savings / recent_energy_total)
                recent_df["energy"] = recent_df["energy"] * (1.0 - reduction_ratio)

        setpoint_targets = [
            float(a.get("params", {}).get("setpoint_c_target"))
            for a in applied_actions
            if a.get("type") == "setpoint_change" and a.get("params", {}).get("setpoint_c_target") is not None
        ]
        if setpoint_targets and not recent_df.empty:
            target = float(max(setpoint_targets))
            current_avg = float(recent_df["temperature"].mean()) if not recent_df["temperature"].empty else target
            recent_df["temperature"] = recent_df["temperature"] + 0.35 * (target - current_avg)

        chart_points = recent_df.copy()
        chart_points["carbon"] = chart_points["energy"] * EMISSION_FACTOR_T_PER_KWH

        anomalies_df = _build_anomalies(recent_df)
        anomalies_payload = [
            {
                "timestamp": row["timestamp"].isoformat(),
                "score": float(row["score"]),
                "is_anomaly": bool(row["is_anomaly"]),
                "energy": float(row["energy"]),
                "temperature": float(row["temperature"]),
                "occupancy": float(row["occupancy"]),
            }
            for _, row in anomalies_df.sort_values("score", ascending=False).head(50).iterrows()
        ]

        suggestions = suggestion_engine.generate_suggestions(building_id) if hasattr(suggestion_engine, "generate_suggestions") else []
        suggestions = [
            s
            for s in suggestions
            if not action_state_service.should_suppress_suggestion(building_id, s)
        ]

        total_energy = float(recent_df["energy"].sum())
        avg_temp = float(recent_df["temperature"].mean())
        peak_occ = float(recent_df["occupancy"].max())
        anomaly_rate = (
            float(anomalies_df["is_anomaly"].mean()) * 100.0 if not anomalies_df.empty else 0.0
        )
        potential_savings = (
            sum(s.get("estimated_savings_kwh", 0) for s in suggestions)
            if suggestions
            else 0.0
        )

        carbon_today = total_energy * EMISSION_FACTOR_T_PER_KWH
        prev_window = df[
            (df["timestamp"] < last_24h_start)
            & (df["timestamp"] >= last_24h_start - timedelta(hours=24))
        ]
        carbon_prev = float(prev_window["energy"].sum()) * EMISSION_FACTOR_T_PER_KWH if not prev_window.empty else 0.0
        delta_percent = (
            ((carbon_today - carbon_prev) / carbon_prev) * 100.0 if carbon_prev else 0.0
        )

        alerts = []
        for anomaly in anomalies_payload[:5]:
            severity = "critical" if anomaly["score"] >= 0.9 else "warning"
            alerts.append(
                {
                    "id": f"anomaly-{anomaly['timestamp']}",
                    "severity": severity,
                    "title": "Anomaly detected",
                    "message": (
                        f"Energy spike to {anomaly['energy']:.1f} kWh "
                        f"(score {(anomaly['score'] * 100):.0f}%)."
                    ),
                    "timestamp": anomaly["timestamp"],
                }
            )

        if delta_percent > 5:
            alerts.append(
                {
                    "id": "carbon-alert",
                    "severity": "warning",
                    "title": "Carbon footprint rise",
                    "message": f"Carbon emissions increased by {delta_percent:.1f}% vs. previous day.",
                    "timestamp": end_time.isoformat(),
                }
            )

        building_info = data_service.get_building_info()

        response = {
            "building": building_info,
            "kpis": {
                "total_energy_kwh": round(total_energy, 2),
                "avg_temperature_c": round(avg_temp, 1),
                "peak_occupancy": round(peak_occ, 2),
                "anomaly_rate_pct": round(anomaly_rate, 1),
                "potential_savings_kwh": round(potential_savings, 1),
            },
            "charts": [
                {
                    "timestamp": row["timestamp"].isoformat(),
                    "energy": float(row["energy"]),
                    "temperature": float(row["temperature"]),
                    "occupancy": float(row["occupancy"]),
                    "carbon": float(row["carbon"]),
                }
                for _, row in chart_points.tail(288).iterrows()
            ],
            "carbon": {
                "today_tonnes": round(carbon_today, 3),
                "previous_tonnes": round(carbon_prev, 3),
                "delta_percent": round(delta_percent, 1),
            },
            "alerts": alerts,
            "anomalies": anomalies_payload,
            "suggestions": suggestions[:5],
            "applied_actions": applied_actions,
            "actions_version": actions_version,
        }

        return response

    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Dashboard error: {exc}")
        print(f"Traceback:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Failed to build dashboard: {str(exc)}") from exc

