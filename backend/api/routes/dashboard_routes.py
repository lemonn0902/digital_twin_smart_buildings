from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.services.data_service import data_service
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
    feature_df = base_df.set_index("timestamp")[
        ["energy", "temperature", "humidity", "occupancy"]
    ]
    feature_df = _augment_time_features(feature_df)

    ae_scores = autoencoder_reconstruction_error(feature_df, FEATURE_COLS)
    if_scores = isolation_forest_scores(feature_df, FEATURE_COLS)

    combined = 0.5 * _normalize(ae_scores) + 0.5 * _normalize(if_scores)
    feature_df = feature_df.assign(score=combined).reset_index()
    feature_df["is_anomaly"] = feature_df["score"] >= 0.85
    return feature_df


@router.get("/overview/{building_id}", response_model=DashboardResponse)
async def dashboard_overview(building_id: str):
    """
    Aggregate KPIs, charts, anomalies, alerts, and suggestions for the monitoring dashboard.
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=48)

        df = data_service.get_data(start_time=start_time, end_time=end_time)
        if df.empty:
            df = data_service.get_data()

        if df.empty:
            raise HTTPException(status_code=404, detail="No telemetry available for dashboard.")

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        last_24h_start = end_time - timedelta(hours=24)
        recent_df = df[df["timestamp"] >= last_24h_start]
        if recent_df.empty:
            recent_df = df.tail(96)  # fallback ~24h assuming 15m data

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
        }

        return response

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to build dashboard: {exc}") from exc

