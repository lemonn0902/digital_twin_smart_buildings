from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from core.utils.config import get_settings


settings = get_settings()

# Global client (singleton)
_influx_client: Optional[InfluxDBClient] = None
_write_api: Optional[Any] = None
_query_api: Optional[Any] = None


def get_influx_client() -> InfluxDBClient:
    """Get or create InfluxDB client singleton."""
    global _influx_client
    if _influx_client is None:
        _influx_client = InfluxDBClient(
            url=settings.influxdb_url,
            token=settings.influxdb_token,
            org=settings.influxdb_org,
            timeout=30_000
        )
    return _influx_client


def get_write_api():
    """Get write API for writing data points."""
    global _write_api
    if _write_api is None:
        client = get_influx_client()
        _write_api = client.write_api(write_options=SYNCHRONOUS)
    return _write_api


def get_query_api():
    """Get query API for querying data."""
    global _query_api
    if _query_api is None:
        client = get_influx_client()
        _query_api = client.query_api()
    return _query_api


def write_telemetry_point(
    building_id: str,
    zone_id: str,
    metric: str,
    value: float,
    timestamp: Optional[datetime] = None
) -> None:
    """
    Write a single telemetry point to InfluxDB.
    
    Args:
        building_id: Building identifier
        zone_id: Zone/room identifier
        metric: Metric name (e.g., "temperature", "energy", "co2")
        value: Metric value
        timestamp: Optional timestamp (defaults to now)
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    point = (
        Point(metric)
        .tag("building_id", building_id)
        .tag("zone_id", zone_id)
        .field("value", value)
        .time(timestamp, WritePrecision.NS)
    )
    
    try:
        write_api = get_write_api()
        write_api.write(
            bucket=settings.influxdb_bucket,
            org=settings.influxdb_org,
            record=point
        )
    except Exception as e:
        # In production, log this error properly
        print(f"Failed to write to InfluxDB: {e}")


def query_time_series(
    building_id: str,
    zone_id: Optional[str],
    metrics: List[str],
    start_time: datetime,
    end_time: datetime,
    resolution_minutes: int = 15
) -> pd.DataFrame:
    """
    Query time-series data from InfluxDB.
    
    Returns:
        DataFrame with columns: timestamp, metric, value, zone_id
    """
    try:
        query_api = get_query_api()

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        start_iso = start_time.astimezone(timezone.utc).isoformat()
        end_iso = end_time.astimezone(timezone.utc).isoformat()

        # Build Flux query
        flux_query = f'''
        from(bucket: "{settings.influxdb_bucket}")
          |> range(start: time(v: "{start_iso}"), stop: time(v: "{end_iso}"))
          |> filter(fn: (r) => r["building_id"] == "{building_id}")
        '''
        
        if zone_id:
            flux_query += f'|> filter(fn: (r) => r["zone_id"] == "{zone_id}")'
        
        if metrics:
            metrics_filter = " or ".join([f'r["_measurement"] == "{m}"' for m in metrics])
            flux_query += f'|> filter(fn: (r) => {metrics_filter})'
        
        flux_query += f'''
          |> aggregateWindow(every: {resolution_minutes}m, fn: mean, createEmpty: false)
          |> yield(name: "mean")
        '''
        
        result = query_api.query_data_frame(flux_query)
        
        if result is None or result.empty:
            return pd.DataFrame()
        
        # Normalize columns
        if "_time" in result.columns:
            result = result.rename(columns={"_time": "timestamp", "_value": "value", "_measurement": "metric"})
        
        return result
        
    except Exception as e:
        print(f"InfluxDB query failed: {e}")
        return pd.DataFrame()


def get_latest_value(
    building_id: str,
    zone_id: Optional[str],
    metric: str
) -> Optional[float]:
    """Get the most recent value for a metric."""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    df = query_time_series(building_id, zone_id, [metric], start_time, end_time)
    
    if df.empty:
        return None
    
    return float(df.iloc[-1]["value"])


# Fallback stub function for when InfluxDB is not available
def query_time_series_stub(
    building_id: str,
    zone_id: Optional[str],
    metrics: List[str],
    start_time: datetime,
    end_time: datetime,
    resolution_minutes: int = 15
) -> pd.DataFrame:
    """Generate synthetic time-series data when InfluxDB is unavailable."""
    import numpy as np
    
    timestamps = pd.date_range(start=start_time, end=end_time, freq=f"{resolution_minutes}min")
    
    data = []
    for ts in timestamps:
        hour = ts.hour
        # Simple daily pattern
        base_value = 0.5 + 0.3 * np.sin(2 * np.pi * hour / 24)
        noise = np.random.normal(0, 0.1)
        
        for metric in metrics:
            data.append({
                "timestamp": ts,
                "metric": metric,
                "value": max(0, base_value + noise),
                "zone_id": zone_id or "zone-1",
                "building_id": building_id
            })
    
    return pd.DataFrame(data)
