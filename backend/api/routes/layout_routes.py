from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any


router = APIRouter()


class Zone(BaseModel):
    id: str
    name: str
    floor: int
    area_m2: float
    neighbors: List[str]


class LayoutResponse(BaseModel):
    building_id: str
    zones: List[Zone]
    metadata: Dict[str, Any] = {}


@router.get("/{building_id}", response_model=LayoutResponse)
async def get_layout(building_id: str) -> LayoutResponse:
    """
    Return a static, simple graph-like layout for now.
    Later you'll parse BIM or generate graphs in core.layout_generator.
    """
    zones = [
        Zone(
            id="z1",
            name="Open Office",
            floor=1,
            area_m2=120.0,
            neighbors=["z2", "z3"],
        ),
        Zone(
            id="z2",
            name="Meeting Room",
            floor=1,
            area_m2=30.0,
            neighbors=["z1"],
        ),
        Zone(
            id="z3",
            name="Corridor",
            floor=1,
            area_m2=40.0,
            neighbors=["z1"],
        ),
    ]
    return LayoutResponse(
        building_id=building_id,
        zones=zones,
        metadata={"note": "Static demo layout, replace with BIM graph later."},
    )
