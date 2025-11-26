from typing import List, Dict, Any
import pandas as pd


def to_time_series(records: List[Dict[str, Any]], time_key: str = "timestamp") -> pd.DataFrame:
    """
    Turn a list of JSON-like dicts into a simple time-indexed DataFrame.
    This will make it easier to plug in forecasting/anomaly models later.
    """
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if time_key in df.columns:
        df[time_key] = pd.to_datetime(df[time_key])
        df = df.sort_values(time_key).set_index(time_key)
    return df
