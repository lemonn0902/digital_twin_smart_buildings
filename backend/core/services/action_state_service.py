from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import hashlib
import json
import re


@dataclass(frozen=True)
class AppliedAction:
    id: str
    type: str
    description: str
    estimated_savings_kwh: float
    comfort_risk: str
    applied_at: str
    params: Dict[str, Any]
    dedupe_key: str
    signature: str


class ActionStateService:
    def __init__(self) -> None:
        self._applied_by_building: Dict[str, Dict[str, AppliedAction]] = {}
        self._dismissed_ids_by_building: Dict[str, Set[str]] = {}
        self._dismissed_keys_by_building: Dict[str, Set[str]] = {}
        self._version_by_building: Dict[str, int] = {}

    def get_version(self, building_id: str) -> int:
        return self._version_by_building.get(building_id, 0)

    def _bump_version(self, building_id: str) -> int:
        next_version = self.get_version(building_id) + 1
        self._version_by_building[building_id] = next_version
        return next_version

    def get_applied_actions(self, building_id: str) -> List[Dict[str, Any]]:
        applied = self._applied_by_building.get(building_id, {})
        return [asdict(v) for v in applied.values()]

    def get_dismissed_ids(self, building_id: str) -> Set[str]:
        return set(self._dismissed_ids_by_building.get(building_id, set()))

    def get_dismissed_keys(self, building_id: str) -> Set[str]:
        return set(self._dismissed_keys_by_building.get(building_id, set()))

    def is_applied(self, building_id: str, suggestion_id: str) -> bool:
        return suggestion_id in self._applied_by_building.get(building_id, {})

    def is_dismissed(self, building_id: str, suggestion_id: str) -> bool:
        return suggestion_id in self._dismissed_ids_by_building.get(building_id, set())

    def _stable_hash(self, payload: Dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha1(encoded).hexdigest()[:12]

    def _extract_similarity(self, suggestion: Dict[str, Any]) -> tuple[str, str]:
        dedupe_key = str(suggestion.get("dedupe_key") or "")
        signature = str(suggestion.get("signature") or "")
        suggestion_type = str(suggestion.get("type") or "")
        params = suggestion.get("params")
        if not isinstance(params, dict):
            params = self._infer_params(suggestion)

        if not dedupe_key:
            dedupe_key = self._stable_hash({"v": 1, "type": suggestion_type, "params": params})
        if not signature:
            signature = self._stable_hash({"v": 1, "type": suggestion_type, "params": params, "desc": str(suggestion.get("description") or "")})

        return dedupe_key, signature

    def should_suppress_suggestion(self, building_id: str, suggestion: Dict[str, Any]) -> bool:
        suggestion_id = str(suggestion.get("id") or "")
        dedupe_key, _signature = self._extract_similarity(suggestion)

        if suggestion_id and self.is_applied(building_id, suggestion_id):
            return True
        if suggestion_id and self.is_dismissed(building_id, suggestion_id):
            return True

        if dedupe_key:
            dismissed_keys = self.get_dismissed_keys(building_id)
            if dedupe_key in dismissed_keys:
                return True

            applied = self._applied_by_building.get(building_id, {})
            for a in applied.values():
                if a.dedupe_key == dedupe_key:
                    return True

        return False

    def _infer_params(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        suggestion_type = suggestion.get("type")
        description = suggestion.get("description") or ""

        if suggestion_type == "setpoint_change":
            match = re.search(r"(\d+(?:\.\d+)?)\s*°?C", description)
            target = float(match.group(1)) if match else 23.0
            return {"setpoint_c_target": target}

        if suggestion_type == "hvac_schedule":
            return {"schedule": "optimized"}

        if suggestion_type == "ventilation":
            match = re.search(r"(\d+)\s*ppm", description, re.IGNORECASE)
            threshold = int(match.group(1)) if match else 900
            return {"co2_threshold_ppm": threshold}

        return {}

    def apply_suggestion(self, building_id: str, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        if not building_id:
            raise ValueError("building_id is required")

        suggestion_id = str(suggestion.get("id") or "")
        if not suggestion_id:
            raise ValueError("suggestion.id is required")

        self._dismissed_ids_by_building.setdefault(building_id, set()).discard(suggestion_id)

        dedupe_key, signature = self._extract_similarity(suggestion)
        if dedupe_key:
            self._dismissed_keys_by_building.setdefault(building_id, set()).discard(dedupe_key)

        params = suggestion.get("params") if isinstance(suggestion.get("params"), dict) else None
        if params is None:
            params = self._infer_params(suggestion)
        applied_at = datetime.now(timezone.utc).isoformat()
        action = AppliedAction(
            id=suggestion_id,
            type=str(suggestion.get("type") or ""),
            description=str(suggestion.get("description") or ""),
            estimated_savings_kwh=float(suggestion.get("estimated_savings_kwh") or 0.0),
            comfort_risk=str(suggestion.get("comfort_risk") or "low"),
            applied_at=applied_at,
            params=params,
            dedupe_key=dedupe_key,
            signature=signature,
        )

        self._applied_by_building.setdefault(building_id, {})[suggestion_id] = action
        self._bump_version(building_id)
        return asdict(action)

    def dismiss_suggestion(
        self,
        building_id: str,
        suggestion_id: str,
        suggestion: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not building_id:
            raise ValueError("building_id is required")
        if not suggestion_id:
            raise ValueError("suggestion_id is required")

        self._applied_by_building.setdefault(building_id, {}).pop(suggestion_id, None)
        self._dismissed_ids_by_building.setdefault(building_id, set()).add(suggestion_id)

        if suggestion is not None:
            dedupe_key, _signature = self._extract_similarity(suggestion)
            if dedupe_key:
                self._dismissed_keys_by_building.setdefault(building_id, set()).add(dedupe_key)
        self._bump_version(building_id)


action_state_service = ActionStateService()
