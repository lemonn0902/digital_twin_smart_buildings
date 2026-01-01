from datetime import datetime, timedelta
from typing import List, Dict, Any
import hashlib
import json
import pandas as pd

from core.services.timeseries_service import timeseries_service


class SuggestionEngine:
    """Enhanced suggestion engine with data-driven recommendations."""
    
    def generate_suggestions(
        self,
        building_id: str,
        horizon_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Generate energy optimization suggestions."""
        suggestions = []
        
        # Get recent data to inform suggestions
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=48)
        
        try:
            df = timeseries_service.get_metrics(
                building_id=building_id,
                zone_id=None,
                metrics=["energy", "temperature", "occupancy"],
                start_time=start_time,
                end_time=end_time,
                resolution_minutes=60
            )
            
            if not df.empty:
                # Analyze patterns and generate data-driven suggestions
                suggestions.extend(self._analyze_energy_patterns(df, building_id))
                suggestions.extend(self._analyze_temperature_patterns(df, building_id))
                suggestions.extend(self._analyze_occupancy_patterns(df, building_id))
        except Exception:
            pass
        
        # Always include rule-based fallbacks
        suggestions.extend(self._rule_based_suggestions(building_id))

        deduped: Dict[str, Dict[str, Any]] = {}
        for s in suggestions:
            key = str(s.get("dedupe_key") or s.get("id") or "")
            if not key:
                continue
            existing = deduped.get(key)
            if existing is None or float(s.get("estimated_savings_kwh", 0.0)) > float(existing.get("estimated_savings_kwh", 0.0)):
                deduped[key] = s

        # Sort by estimated savings
        suggestions = list(deduped.values())
        suggestions.sort(key=lambda x: x.get("estimated_savings_kwh", 0), reverse=True)
        
        return suggestions[:5]  # Return top 5

    def _stable_hash(self, payload: Dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha1(encoded).hexdigest()[:12]

    def _round_step(self, value: float, step: float) -> float:
        if step <= 0:
            return float(value)
        return float(round(value / step) * step)

    def _make_suggestion(
        self,
        building_id: str,
        suggestion_type: str,
        description: str,
        estimated_savings_kwh: float,
        comfort_risk: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
        version: int = 1,
    ) -> Dict[str, Any]:
        signature_payload = {
            "v": version,
            "type": suggestion_type,
            "params": params,
            "context": context,
        }
        signature = self._stable_hash(signature_payload)

        dedupe_payload = {
            "v": version,
            "type": suggestion_type,
            "params": params,
            "context": {k: context[k] for k in sorted(context.keys()) if k.endswith("_bucket") or k.endswith("_band")},
        }
        dedupe_key = self._stable_hash(dedupe_payload)

        suggestion_id = f"{suggestion_type}:{building_id}:{signature}"
        return {
            "id": suggestion_id,
            "type": suggestion_type,
            "description": description,
            "estimated_savings_kwh": float(estimated_savings_kwh),
            "comfort_risk": comfort_risk,
            "params": params,
            "signature": signature,
            "dedupe_key": dedupe_key,
        }
    
    def _analyze_energy_patterns(self, df: pd.DataFrame, building_id: str) -> List[Dict]:
        """Analyze energy consumption patterns."""
        suggestions = []
        
        energy_df = df[df["metric"] == "energy"] if "metric" in df.columns else df
        
        if energy_df.empty:
            return suggestions
        
        # Check for high base load (idle consumption)
        avg_energy = float(energy_df["value"].mean())
        min_energy = float(energy_df["value"].min())
        ratio = (avg_energy / max(min_energy, 1e-6)) if min_energy is not None else 0.0
        ratio_bucket = self._round_step(ratio, 0.2)
        
        if avg_energy > min_energy * 1.5:
            estimated = float((avg_energy - min_energy) * 8)
            params = {"schedule": "night_setback"}
            context = {
                "avg_energy_kwh": self._round_step(avg_energy, 1.0),
                "min_energy_kwh": self._round_step(min_energy, 1.0),
                "base_load_ratio": self._round_step(ratio, 0.05),
                "base_load_ratio_bucket": ratio_bucket,
            }
            suggestions.append(
                self._make_suggestion(
                    building_id=building_id,
                    suggestion_type="hvac_schedule",
                    description=f"High base load detected ({avg_energy:.1f} kWh avg vs {min_energy:.1f} kWh min). Consider night setback or improved controls.",
                    estimated_savings_kwh=estimated,
                    comfort_risk="low",
                    params=params,
                    context=context,
                    version=2,
                )
            )
        
        return suggestions
    
    def _analyze_temperature_patterns(self, df: pd.DataFrame, building_id: str) -> List[Dict]:
        """Analyze temperature patterns."""
        suggestions = []
        
        temp_df = df[df["metric"] == "temperature"] if "metric" in df.columns else df
        
        if temp_df.empty:
            return suggestions
        
        # Check for overcooling/overheating
        avg_temp = float(temp_df["value"].mean())
        if avg_temp < 22.0:
            avg_temp_bucket = self._round_step(avg_temp, 0.5)
            target = self._round_step(min(24.0, max(22.5, avg_temp + 1.5)), 0.5)
            target_band = f"{target:.1f}"
            savings = float(max(0.0, (target - avg_temp) * 0.6 * 24))
            params = {"setpoint_c_target": target}
            context = {
                "avg_temp_bucket": avg_temp_bucket,
                "target_setpoint_band": target_band,
            }
            suggestions.append(
                self._make_suggestion(
                    building_id=building_id,
                    suggestion_type="setpoint_change",
                    description=f"Average temperature is {avg_temp:.1f}°C. Raising setpoint to {target:.1f}°C could save energy while maintaining comfort.",
                    estimated_savings_kwh=savings,
                    comfort_risk="low",
                    params=params,
                    context=context,
                    version=2,
                )
            )
        
        return suggestions
    
    def _analyze_occupancy_patterns(self, df: pd.DataFrame, building_id: str) -> List[Dict]:
        """Analyze occupancy patterns for optimization opportunities."""
        suggestions = []
        
        occ_df = df[df["metric"] == "occupancy"] if "metric" in df.columns else df
        
        if occ_df.empty:
            return suggestions
        
        # Check for HVAC running during low occupancy periods
        low_occ_threshold = 0.2
        low_occ_hours = occ_df[occ_df["value"] < low_occ_threshold]

        low_occ_ratio = float(len(low_occ_hours) / max(len(occ_df), 1))
        low_occ_bucket = self._round_step(low_occ_ratio, 0.1)
        
        if len(low_occ_hours) > len(occ_df) * 0.3:  # More than 30% low occupancy
            params = {"schedule": "occupancy_based"}
            context = {
                "low_occ_ratio": self._round_step(low_occ_ratio, 0.02),
                "low_occ_ratio_bucket": low_occ_bucket,
            }
            suggestions.append(
                self._make_suggestion(
                    building_id=building_id,
                    suggestion_type="hvac_schedule",
                    description="Significant low-occupancy periods detected. Consider reducing HVAC intensity during these times.",
                    estimated_savings_kwh=15.0,
                    comfort_risk="medium",
                    params=params,
                    context=context,
                    version=2,
                )
            )
        
        return suggestions
    
    def _rule_based_suggestions(self, building_id: str) -> List[Dict]:
        """Generate rule-based suggestions as fallback."""
        sched = self._make_suggestion(
            building_id=building_id,
            suggestion_type="hvac_schedule",
            description="Pre-cool office zones by 1°C between 7:00–8:00 to reduce peak load.",
            estimated_savings_kwh=12.5,
            comfort_risk="low",
            params={"schedule": "pre_cool", "delta_c": 1.0, "window": "07:00-08:00"},
            context={"rule_band": "precool"},
            version=2,
        )
        vent = self._make_suggestion(
            building_id=building_id,
            suggestion_type="ventilation",
            description="Increase CO₂-based fresh air intake threshold from 800 ppm to 900 ppm in low-occupancy periods.",
            estimated_savings_kwh=5.2,
            comfort_risk="medium",
            params={"co2_threshold_ppm": 900},
            context={"rule_band": "co2_900"},
            version=2,
        )
        return [sched, vent]


suggestion_engine = SuggestionEngine()
