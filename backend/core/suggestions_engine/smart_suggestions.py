from datetime import datetime, timedelta
from typing import List, Dict, Any
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
        
        # Sort by estimated savings
        suggestions.sort(key=lambda x: x.get("estimated_savings_kwh", 0), reverse=True)
        
        return suggestions[:5]  # Return top 5
    
    def _analyze_energy_patterns(self, df: pd.DataFrame, building_id: str) -> List[Dict]:
        """Analyze energy consumption patterns."""
        suggestions = []
        
        energy_df = df[df["metric"] == "energy"] if "metric" in df.columns else df
        
        if energy_df.empty:
            return suggestions
        
        # Check for high base load (idle consumption)
        avg_energy = energy_df["value"].mean()
        min_energy = energy_df["value"].min()
        
        if avg_energy > min_energy * 1.5:
            suggestions.append({
                "id": f"base-load-{building_id}",
                "type": "hvac_schedule",
                "description": f"High base load detected ({avg_energy:.1f} kWh avg vs {min_energy:.1f} kWh min). Consider night setback or improved controls.",
                "estimated_savings_kwh": (avg_energy - min_energy) * 8,  # 8 hours of savings
                "comfort_risk": "low"
            })
        
        return suggestions
    
    def _analyze_temperature_patterns(self, df: pd.DataFrame, building_id: str) -> List[Dict]:
        """Analyze temperature patterns."""
        suggestions = []
        
        temp_df = df[df["metric"] == "temperature"] if "metric" in df.columns else df
        
        if temp_df.empty:
            return suggestions
        
        # Check for overcooling/overheating
        avg_temp = temp_df["value"].mean()
        if avg_temp < 22.0:
            savings = (22.0 - avg_temp) * 0.5 * 24  # Rough estimate
            suggestions.append({
                "id": f"temp-adjust-{building_id}",
                "type": "setpoint_change",
                "description": f"Average temperature is {avg_temp:.1f}°C. Raising setpoint to 23°C could save energy while maintaining comfort.",
                "estimated_savings_kwh": savings,
                "comfort_risk": "low"
            })
        
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
        
        if len(low_occ_hours) > len(occ_df) * 0.3:  # More than 30% low occupancy
            suggestions.append({
                "id": f"occupancy-opt-{building_id}",
                "type": "hvac_schedule",
                "description": "Significant low-occupancy periods detected. Consider reducing HVAC intensity during these times.",
                "estimated_savings_kwh": 15.0,
                "comfort_risk": "medium"
            })
        
        return suggestions
    
    def _rule_based_suggestions(self, building_id: str) -> List[Dict]:
        """Generate rule-based suggestions as fallback."""
        return [
            {
                "id": f"sched-1-{building_id}",
                "type": "hvac_schedule",
                "description": "Pre-cool office zones by 1°C between 7:00–8:00 to reduce peak load.",
                "estimated_savings_kwh": 12.5,
                "comfort_risk": "low"
            },
            {
                "id": f"vent-1-{building_id}",
                "type": "setpoint_change",
                "description": "Increase CO₂-based fresh air intake threshold from 800 ppm to 900 ppm in low-occupancy periods.",
                "estimated_savings_kwh": 5.2,
                "comfort_risk": "medium"
            }
        ]


suggestion_engine = SuggestionEngine()
