from __future__ import annotations

from datetime import datetime
from typing import List

import numpy as np
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from core.anomaly_engine.autoencoder_model import autoencoder_reconstruction_error
from core.anomaly_engine.isolation_forest import isolation_forest_scores


router = APIRouter()


class AnomalyPoint(BaseModel):
    timestamp: str
    metric: str
    value: float
    score: float
    is_anomaly: bool


class AnomalyQuery(BaseModel):
    building_id: str
    metric: str  # e.g., "co2", "temperature", "energy"
    start_time: str
    end_time: str


def _build_synthetic_series(query: AnomalyQuery) -> pd.DataFrame:
    """
    For now, we don't have a live time-series database wired in.
    This function synthesizes a simple time series between the
    requested start and end times so the ML models can run.
    """
    start = datetime.fromisoformat(query.start_time)
    end = datetime.fromisoformat(query.end_time)

    # 15‑minute resolution synthetic data
    idx = pd.date_range(start=start, end=end, freq="15min")
    if len(idx) == 0:
        return pd.DataFrame()

    # Simple daily pattern + noise
    hours = idx.hour + idx.minute / 60.0
    base = np.where((hours >= 8) & (hours <= 18), 1.0, 0.3)
    noise = np.random.normal(0.0, 0.1, size=len(idx))
    values = base + noise

    df = pd.DataFrame(
        {
            "timestamp": idx,
            "value": values.astype(float),
        }
    ).set_index("timestamp")
    return df


@router.post("/detect", response_model=List[AnomalyPoint])
async def detect_anomalies(query: AnomalyQuery) -> List[AnomalyPoint]:
    """
    Run anomaly detection using both the autoencoder and IsolationForest
    models and return a combined anomaly score per timestamp.

    NOTE: This implementation currently uses a synthetic time series
    as a stand‑in for real building telemetry.
    """
    df = _build_synthetic_series(query)
    if df.empty:
        return []

    feature_cols = ["value"]

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
    for ts, row in df.iterrows():
        score = float(combined.loc[ts])
        points.append(
            AnomalyPoint(
                timestamp=ts.isoformat(),
                metric=query.metric,
                value=float(row["value"]),
                score=score,
                is_anomaly=score >= threshold,
            )
        )

    return points
