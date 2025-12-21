"""
API routes for energy consumption and occupancy forecasting.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from core.services.forecasting_service import (
    forecast_energy_consumption,
    forecast_occupancy,
)


router = APIRouter()


class ForecastRequest(BaseModel):
    building_id: str
    horizon_hours: Optional[int] = 24


class ForecastPoint(BaseModel):
    timestamp: str
    energy_kwh: Optional[float] = None
    occupancy: Optional[float] = None
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None


class ForecastResponse(BaseModel):
    building_id: str
    forecast: List[ForecastPoint]
    model_available: bool
    horizon_hours: int


class OccupancyForecastRequest(BaseModel):
    building_id: str
    horizon_hours: Optional[int] = 12


class OccupancyForecastPoint(BaseModel):
    timestamp: str
    occupancy: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None


class OccupancyForecastResponse(BaseModel):
    building_id: str
    forecast: List[OccupancyForecastPoint]
    model_available: bool
    horizon_hours: int


@router.post("/energy", response_model=ForecastResponse)
async def forecast_energy(request: ForecastRequest) -> ForecastResponse:
    """
    Forecast energy consumption for the next N hours.
    
    Uses trained LSTM model if available, otherwise generates
    pattern-based synthetic forecast.
    
    Args:
        request: ForecastRequest with building_id and optional horizon_hours
    
    Returns:
        ForecastResponse with forecasted energy values and timestamps
    """
    if request.horizon_hours and (request.horizon_hours < 1 or request.horizon_hours > 168):
        raise HTTPException(
            status_code=400,
            detail="horizon_hours must be between 1 and 168 (1 week)"
        )
    
    try:
        result = forecast_energy_consumption(
            building_id=request.building_id,
            horizon_hours=request.horizon_hours or 24
        )
        
        return ForecastResponse(
            building_id=request.building_id,
            forecast=[
                ForecastPoint(**point) for point in result["forecast"]
            ],
            model_available=result["model_available"],
            horizon_hours=result["horizon_hours"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate forecast: {str(e)}"
        )


@router.post("/occupancy", response_model=OccupancyForecastResponse)
async def forecast_occupancy_endpoint(
    request: OccupancyForecastRequest
) -> OccupancyForecastResponse:
    """
    Forecast occupancy for the next N hours.
    
    Uses trained LSTM model if available, otherwise generates
    pattern-based synthetic forecast.
    
    Args:
        request: OccupancyForecastRequest with building_id and optional horizon_hours
    
    Returns:
        OccupancyForecastResponse with forecasted occupancy values and timestamps
    """
    if request.horizon_hours and (request.horizon_hours < 1 or request.horizon_hours > 12):
        raise HTTPException(
            status_code=400,
            detail="horizon_hours must be between 1 and 12 for occupancy prediction"
        )
    
    try:
        result = forecast_occupancy(
            building_id=request.building_id,
            horizon_hours=request.horizon_hours or 12
        )
        
        return OccupancyForecastResponse(
            building_id=request.building_id,
            forecast=[
                OccupancyForecastPoint(**point) for point in result["forecast"]
            ],
            model_available=result["model_available"],
            horizon_hours=result["horizon_hours"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate occupancy forecast: {str(e)}"
        )
