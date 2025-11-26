from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd

from core.utils.model_loader import get_model_path


@lru_cache(maxsize=1)
def _load_iforest() -> Optional[object]:
    """
    Lazily load the trained IsolationForest model from disk.

    If the pickle file is missing or corrupted, return None so the
    caller can gracefully fall back instead of raising EOFError.
    """
    model_path = get_model_path("anomaly", "isolation_forest.pkl")
    try:
        return joblib.load(model_path)
    except Exception:
        # In production, log this error with details.
        return None


def isolation_forest_scores(
    df: pd.DataFrame, feature_cols: List[str]
) -> pd.Series:
    """
    Get anomaly scores from IsolationForest.

    We use the negative of score_samples so that larger values
    correspond to more anomalous points.

    If the model cannot be loaded, returns a zero-valued Series.
    """
    if df.empty:
        return pd.Series(dtype="float64")

    model = _load_iforest()
    if model is None:
        return pd.Series(0.0, index=df.index, name="if_score")

    x = df[feature_cols].to_numpy(dtype=np.float32)
    raw_scores = model.score_samples(x)
    scores = -raw_scores
    return pd.Series(scores, index=df.index, name="if_score")


