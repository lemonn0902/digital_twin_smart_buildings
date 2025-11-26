from typing import Dict


def simulate_thermal_stub(
    request,
    occupancy_series: Dict[str, float],
    hvac_series: Dict[str, float],
) -> Dict[str, float]:
    """
    Simple linear relation between HVAC power, occupancy, and zone temperature.
    Assumes more HVAC = cooler space, more occupancy = slightly warmer.
    """
    temps: Dict[str, float] = {}
    for ts in occupancy_series:
        occ = occupancy_series[ts]
        hvac = hvac_series.get(ts, 0.0)
        temps[ts] = 24.0 - 0.4 * hvac + 0.8 * occ
    return temps
