from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from core.services.timeseries_service import timeseries_service


router = APIRouter()


class HistoricalDataRequest(BaseModel):
    building_id: str
    zone_id: Optional[str] = None
    metrics: List[str]  # e.g., ["temperature", "energy", "occupancy"]
    start_time: str  # ISO format
    end_time: str  # ISO format
    resolution_minutes: int = 15


class MetricPoint(BaseModel):
    timestamp: str
    metric: str
    value: float
    zone_id: Optional[str] = None


class HistoricalDataResponse(BaseModel):
    building_id: str
    points: List[MetricPoint]
    resolution_minutes: int


@router.post("/query", response_model=HistoricalDataResponse)
async def query_historical_data(request: HistoricalDataRequest):
    """Query historical time-series data."""
    try:
        start_time = datetime.fromisoformat(request.start_time.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(request.end_time.replace("Z", "+00:00"))
        
        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="start_time must be before end_time")
        
        # Limit query range to prevent abuse
        max_range_days = 90
        if (end_time - start_time).days > max_range_days:
            raise HTTPException(
                status_code=400,
                detail=f"Query range cannot exceed {max_range_days} days"
            )
        
        df = timeseries_service.get_metrics(
            building_id=request.building_id,
            zone_id=request.zone_id,
            metrics=request.metrics,
            start_time=start_time,
            end_time=end_time,
            resolution_minutes=request.resolution_minutes
        )
        
        points = []
        for _, row in df.iterrows():
            points.append(
                MetricPoint(
                    timestamp=row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
                    metric=row.get("metric", request.metrics[0]),
                    value=float(row["value"]),
                    zone_id=row.get("zone_id") or request.zone_id
                )
            )
        
        return HistoricalDataResponse(
            building_id=request.building_id,
            points=points,
            resolution_minutes=request.resolution_minutes
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query data: {str(e)}")


@router.get("/latest/{building_id}")
async def get_latest_metrics(building_id: str, zone_id: Optional[str] = None):
    """Get latest metric values for a building/zone."""
    from core.services.influxdb_service import get_latest_value
    
    metrics = ["temperature", "energy", "occupancy", "co2"]
    zone_ids = [zone_id] if zone_id else ["zone-1", "zone-2", "zone-3"]
    
    result = {}
    for zid in zone_ids:
        result[zid] = {}
        for metric in metrics:
            value = get_latest_value(building_id, zid, metric)
            if value is not None:
                result[zid][metric] = value
    
    return {"building_id": building_id, "latest_values": result}
