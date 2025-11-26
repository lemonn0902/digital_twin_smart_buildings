from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from core.suggestions_engine.smart_suggestions import suggestion_engine


router = APIRouter()


class Suggestion(BaseModel):
    id: str
    type: str  # e.g., "hvac_schedule", "setpoint_change"
    description: str
    estimated_savings_kwh: float
    comfort_risk: str  # "low", "medium", "high"


class SuggestionQuery(BaseModel):
    building_id: str
    horizon_hours: int = 24


@router.post("/recommend", response_model=List[Suggestion])
async def recommend_actions(query: SuggestionQuery) -> List[Suggestion]:
    """
    Return intelligent energy optimization recommendations.
    Uses data-driven analysis when available, with rule-based fallbacks.
    """
    suggestions_data = suggestion_engine.generate_suggestions(
        building_id=query.building_id,
        horizon_hours=query.horizon_hours
    )
    
    return [Suggestion(**s) for s in suggestions_data]
