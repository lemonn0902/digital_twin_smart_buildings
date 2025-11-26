from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from core.simulation_engine.occupancy_sim import simulate_occupancy_stub
from core.simulation_engine.hvac_sim import simulate_hvac_stub
from core.simulation_engine.thermal_model import simulate_thermal_stub


router = APIRouter()


class SimulationRequest(BaseModel):
    building_id: str
    start_time: str
    end_time: str
    resolution_minutes: int = 15
    scenario: Optional[str] = "baseline"


class SimulationPoint(BaseModel):
    timestamp: str
    occupancy: float
    energy_kwh: float
    temperature_c: float


class SimulationResponse(BaseModel):
    building_id: str
    scenario: str
    points: List[SimulationPoint]


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(payload: SimulationRequest) -> SimulationResponse:
    """
    Run a lightweight, fast simulation using stubbed models.
    Later you can replace these with real ML/physics-based models.
    """
    occupancy_series = simulate_occupancy_stub(payload)
    hvac_series = simulate_hvac_stub(payload, occupancy_series)
    thermal_series = simulate_thermal_stub(payload, occupancy_series, hvac_series)

    points = []
    for ts in occupancy_series:
        points.append(
            SimulationPoint(
                timestamp=ts,
                occupancy=occupancy_series[ts],
                energy_kwh=hvac_series.get(ts, 0.0),
                temperature_c=thermal_series.get(ts, 24.0),
            )
        )

    return SimulationResponse(
        building_id=payload.building_id,
        scenario=payload.scenario or "baseline",
        points=points,
    )
