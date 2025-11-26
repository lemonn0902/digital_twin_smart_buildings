from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

import numpy as np
import pandas as pd
import tensorflow as tf

from core.utils.model_loader import get_model_path


@lru_cache(maxsize=1)
def _load_autoencoder() -> Optional[object]:
    """
    Lazily load the trained autoencoder model from disk.

    If the file is missing or not a valid H5 model, return None so
    the rest of the pipeline can gracefully fall back to other models.
    """
    model_path = get_model_path("anomaly", "autoencoder.h5")
    try:
        return tf.keras.models.load_model(model_path)
    except Exception:
        # In a real system, you'd log this properly.
        return None


def autoencoder_reconstruction_error(
    df: pd.DataFrame, feature_cols: List[str]
) -> pd.Series:
    """
    Compute reconstruction error per row using the autoencoder.

    If the autoencoder model cannot be loaded, returns a zero-valued
    Series so downstream code can continue (IsolationForest will still
    provide anomaly signal).
    """
    if df.empty:
        return pd.Series(dtype="float64")

    model = _load_autoencoder()
    if model is None:
        return pd.Series(0.0, index=df.index, name="ae_error")

    x = df[feature_cols].to_numpy(dtype=np.float32)
    recon = model.predict(x, verbose=0)
    errors = np.mean((x - recon) ** 2, axis=1)
    return pd.Series(errors, index=df.index, name="ae_error")


