from __future__ import annotations

from datetime import datetime
from typing import List

import numpy as np
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from core.anomaly_engine.autoencoder_model import autoencoder_reconstruction_error
from core.anomaly_engine.isolation_forest import isolation_forest_scores
from core.services.data_service import data_service


router = APIRouter()


class AnomalyPoint(BaseModel):
    timestamp: str
    metric: str
    value: float
    score: float
    is_anomaly: bool


class AnomalyQuery(BaseModel):
    building_id: str
    metric: str  # e.g., "energy", "temperature"
    start_time: str
    end_time: str


FEATURE_COLS = [
    "energy",
    "temperature",
    "humidity",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
]


def _build_synthetic_series(query: AnomalyQuery) -> pd.DataFrame:
    """Fallback synthetic data when dataset/InfluxDB is unavailable."""
    start = datetime.fromisoformat(query.start_time)
    end = datetime.fromisoformat(query.end_time)
    idx = pd.date_range(start=start, end=end, freq="1H")
    if len(idx) == 0:
        return pd.DataFrame()

    hours = idx.hour + idx.minute / 60.0
    weekday = idx.dayofweek

    energy = 150 + 40 * np.sin(2 * np.pi * (hours - 8) / 24) + np.random.normal(0, 5, size=len(idx))
    temperature = 22 - 5 * np.cos(2 * np.pi * hours / 24) + np.random.normal(0, 0.5, size=len(idx))
    humidity = 45 + 10 * np.sin(2 * np.pi * weekday / 7) + np.random.normal(0, 2, size=len(idx))

    df = pd.DataFrame(
        {
            "timestamp": idx,
            "energy": energy,
            "temperature": temperature,
            "humidity": humidity,
        }
    ).set_index("timestamp")
    _augment_time_features(df)
    return df


def _augment_time_features(df: pd.DataFrame) -> None:
    """Append cyclical time features in-place."""
    df["hour"] = df.index.hour
    df["dayofweek"] = df.index.dayofweek
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
    df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7.0)
    df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7.0)
    df.drop(columns=["hour", "dayofweek"], inplace=True)


def _load_feature_frame(query: AnomalyQuery) -> pd.DataFrame:
    """Load real telemetry (from processed dataset / Influx) or fall back."""
    start = datetime.fromisoformat(query.start_time)
    end = datetime.fromisoformat(query.end_time)

    df = data_service.get_data(start_time=start, end_time=end)
    if df.empty:
        return _build_synthetic_series(query)

    df = df.sort_values("timestamp").set_index("timestamp")

    required = {"energy", "temperature", "humidity"}
    if not required.issubset(df.columns):
        return _build_synthetic_series(query)

    _augment_time_features(df)
    df = df[FEATURE_COLS].dropna()
    if df.empty:
        return _build_synthetic_series(query)

    return df


@router.post("/detect", response_model=List[AnomalyPoint])
async def detect_anomalies(query: AnomalyQuery) -> List[AnomalyPoint]:
    """
    Run anomaly detection using both the autoencoder and IsolationForest
    models and return a combined anomaly score per timestamp.

    NOTE: This implementation currently uses a synthetic time series
    as a stand‑in for real building telemetry.
    """
    df = _load_feature_frame(query)
    if df.empty:
        return []

    feature_cols = FEATURE_COLS

    # Model scores
    ae_scores = autoencoder_reconstruction_error(df, feature_cols)
    if_scores = isolation_forest_scores(df, feature_cols)

    # Normalize to 0‑1 for combination
    def _normalize(s: pd.Series) -> pd.Series:
        if s.empty:
            return s
        lo, hi = float(s.min()), float(s.max())
        if hi - lo < 1e-8:
            return pd.Series(0.0, index=s.index)
        return (s - lo) / (hi - lo)

    ae_n = _normalize(ae_scores)
    if_n = _normalize(if_scores)

    combined = 0.5 * ae_n + 0.5 * if_n

    # Simple threshold: top 10% of scores are anomalies
    threshold = float(np.quantile(combined.to_numpy(), 0.9))

    points: List[AnomalyPoint] = []
    value_col = query.metric if query.metric in df.columns else "energy"

    for ts, row in df.iterrows():
        score = float(combined.loc[ts])
        points.append(
            AnomalyPoint(
                timestamp=ts.isoformat(),
                metric=query.metric,
                value=float(row.get(value_col, np.nan)),
                score=score,
                is_anomaly=score >= threshold,
            )
        )

    return points
