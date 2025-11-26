from typing import Dict


def simulate_hvac_stub(request, occupancy_series: Dict[str, float]) -> Dict[str, float]:
    """
    Simple rule-of-thumb HVAC energy model based on occupancy.
    """
    hvac_profile: Dict[str, float] = {}
    base_load = 1.0  # kW
    for ts, occ in occupancy_series.items():
        hvac_profile[ts] = base_load + 3.0 * occ
    return hvac_profile
