from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from core.suggestions_engine.smart_suggestions import suggestion_engine
from core.services.action_state_service import action_state_service


router = APIRouter()


class Suggestion(BaseModel):
    id: str
    type: str  # e.g., "hvac_schedule", "setpoint_change"
    description: str
    estimated_savings_kwh: float
    comfort_risk: str  # "low", "medium", "high"
    params: dict | None = None
    signature: str | None = None
    dedupe_key: str | None = None


class SuggestionQuery(BaseModel):
    building_id: str
    horizon_hours: int = 24


class SuggestionActionRequest(BaseModel):
    building_id: str
    suggestion: Suggestion


class SuggestionDismissRequest(BaseModel):
    building_id: str
    suggestion_id: str
    suggestion: Suggestion | None = None


class AppliedActionResponse(BaseModel):
    id: str
    type: str
    description: str
    estimated_savings_kwh: float
    comfort_risk: str
    applied_at: str
    params: dict


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

    filtered = [
        s
        for s in suggestions_data
        if not action_state_service.should_suppress_suggestion(query.building_id, s)
    ]
    return [Suggestion(**s) for s in filtered]


@router.post("/apply", response_model=AppliedActionResponse)
async def apply_suggestion(request: SuggestionActionRequest) -> AppliedActionResponse:
    payload = (
        request.suggestion.model_dump()
        if hasattr(request.suggestion, "model_dump")
        else request.suggestion.dict()
    )
    action = action_state_service.apply_suggestion(
        building_id=request.building_id,
        suggestion=payload,
    )
    return AppliedActionResponse(**action)


@router.post("/dismiss")
async def dismiss_suggestion(request: SuggestionDismissRequest) -> dict:
    suggestion_payload = None
    if request.suggestion is not None:
        suggestion_payload = (
            request.suggestion.model_dump()
            if hasattr(request.suggestion, "model_dump")
            else request.suggestion.dict()
        )
    action_state_service.dismiss_suggestion(
        request.building_id,
        request.suggestion_id,
        suggestion=suggestion_payload,
    )
    return {"status": "ok"}


@router.get("/applied/{building_id}", response_model=List[AppliedActionResponse])
async def list_applied_suggestions(building_id: str) -> List[AppliedActionResponse]:
    return [AppliedActionResponse(**a) for a in action_state_service.get_applied_actions(building_id)]
