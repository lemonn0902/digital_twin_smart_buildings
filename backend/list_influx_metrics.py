#!/usr/bin/env python3
"""List telemetry metric names in InfluxDB in a compact, actionable way.

Run from the backend directory:
  python list_influx_metrics.py

This script uses the same config as the backend (core.utils.config.get_settings).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.utils.config import get_settings
from core.services.influxdb_service import get_query_api


def _print_header(title: str) -> None:
    print("=" * 70)
    print(title)
    print("=" * 70)


def list_metrics(building_id: str, lookback_days: int = 30) -> None:
    settings = get_settings()
    query_api = get_query_api()

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=lookback_days)
    start_iso = start_time.isoformat()
    end_iso = end_time.isoformat()

    _print_header("INFLUXDB TELEMETRY METRICS")
    print("Configuration:")
    print(f"  URL: {settings.influxdb_url}")
    print(f"  Org: {settings.influxdb_org}")
    print(f"  Bucket: {settings.influxdb_bucket}")
    print(f"  Building ID filter: {building_id}")
    print(f"  Lookback: {lookback_days} days")

    _print_header("1) Measurements (telemetry-only) in lookback window")
    flux_measurements = f'''
    import "influxdata/influxdb/schema"

    schema.measurements(bucket: "{settings.influxdb_bucket}")
      |> filter(fn: (r) => r["_value"] != "")
    '''

    try:
        result = query_api.query(flux_measurements)
        all_measurements: list[str] = []
        for table in result:
            for record in table.records:
                val = record.get_value()
                if isinstance(val, str) and val not in all_measurements:
                    all_measurements.append(val)

        # Many buckets also contain Influx internal metrics; filter to likely telemetry
        telemetry_candidates = [m for m in all_measurements if m in {"energy", "temperature", "occupancy", "humidity", "co2"}]

        print(f"Found {len(all_measurements)} total measurements in bucket.")
        if telemetry_candidates:
            print("Telemetry measurements detected:")
            for m in sorted(telemetry_candidates):
                print(f"  - {m}")
        else:
            print("No common telemetry measurements found (energy/temperature/occupancy/humidity/co2).")
            print("Here are the first 30 measurements as a hint:")
            for m in all_measurements[:30]:
                print(f"  - {m}")
    except Exception as e:
        print(f"Failed to query measurements: {e}")

    _print_header("2) Distinct telemetry measurements for this building_id")
    flux_distinct_measurements = f'''
    from(bucket: "{settings.influxdb_bucket}")
      |> range(start: time(v: "{start_iso}"), stop: time(v: "{end_iso}"))
      |> filter(fn: (r) => r["building_id"] == "{building_id}")
      |> keep(columns: ["_measurement"])
      |> distinct(column: "_measurement")
      |> sort(columns: ["_measurement"])
    '''

    try:
        result = query_api.query(flux_distinct_measurements)
        building_measurements: list[str] = []
        for table in result:
            for record in table.records:
                val = record.get_value()
                if isinstance(val, str):
                    building_measurements.append(val)

        if building_measurements:
            for m in building_measurements:
                print(f"  - {m}")
        else:
            print("No measurements found for this building_id in the lookback window.")
    except Exception as e:
        print(f"Failed to query building measurements: {e}")

    _print_header("3) Distinct fields (_field) for this building_id")
    flux_fields = f'''
    from(bucket: "{settings.influxdb_bucket}")
      |> range(start: time(v: "{start_iso}"), stop: time(v: "{end_iso}"))
      |> filter(fn: (r) => r["building_id"] == "{building_id}")
      |> keep(columns: ["_measurement", "_field"])
      |> distinct(column: "_field")
      |> sort(columns: ["_field"])
    '''

    try:
        result = query_api.query(flux_fields)
        fields: list[str] = []
        for table in result:
            for record in table.records:
                val = record.get_value()
                if isinstance(val, str) and val not in fields:
                    fields.append(val)

        if fields:
            for f in fields:
                print(f"  - {f}")
        else:
            print("No fields found for this building_id in the lookback window.")
    except Exception as e:
        print(f"Failed to query fields: {e}")

    _print_header("4) Distinct zone_id values for this building_id")
    flux_zones = f'''
    import "influxdata/influxdb/schema"

    schema.tagValues(
      bucket: "{settings.influxdb_bucket}",
      tag: "zone_id",
      start: time(v: "{start_iso}"),
      stop: time(v: "{end_iso}")
    )
    '''

    try:
        result = query_api.query(flux_zones)
        zones: list[str] = []
        for table in result:
            for record in table.records:
                val = record.get_value()
                if isinstance(val, str):
                    zones.append(val)

        zones = sorted(set(zones))
        if zones:
            for z in zones:
                print(f"  - {z}")
        else:
            print("No zone_id tags found in the lookback window.")
    except Exception as e:
        print(f"Failed to query zone_id tags: {e}")

    _print_header("5) Sample points (to confirm values are non-zero)")
    flux_sample = f'''
    from(bucket: "{settings.influxdb_bucket}")
      |> range(start: time(v: "{start_iso}"), stop: time(v: "{end_iso}"))
      |> filter(fn: (r) => r["building_id"] == "{building_id}")
      |> filter(fn: (r) => r["_measurement"] == "energy" or r["_measurement"] == "temperature" or r["_measurement"] == "occupancy" or r["_measurement"] == "humidity")
      |> keep(columns: ["_time", "_measurement", "_field", "_value", "zone_id", "building_id"])
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 10)
    '''

    try:
        result = query_api.query(flux_sample)
        rows = []
        for table in result:
            for record in table.records:
                rows.append(
                    (
                        record.get_time(),
                        record.get_measurement(),
                        record.get_field(),
                        record.get_value(),
                        record.values.get("zone_id"),
                        record.values.get("building_id"),
                    )
                )

        if not rows:
            print("No recent telemetry points found for this building_id.")
        else:
            for t, m, f, v, z, b in rows:
                print(f"  time={t} measurement={m} field={f} value={v} building_id={b} zone_id={z}")
    except Exception as e:
        print(f"Failed to query sample points: {e}")


if __name__ == "__main__":
    # Defaults match the frontend building id.
    list_metrics(building_id="demo-building", lookback_days=60)
