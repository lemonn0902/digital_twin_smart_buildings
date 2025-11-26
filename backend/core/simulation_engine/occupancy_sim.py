from typing import Dict


def simulate_occupancy_stub(request) -> Dict[str, float]:
    """
    Extremely simple occupancy profile:
    - 0 during night
    - ramps up in the morning
    - plateaus during work hours
    This is just to let the front-end visualize something.
    """
    # In a real implementation, you'd use request.start_time / end_time.
    # Here we just synthesize a fixed small series.
    timestamps = [f"2025-01-01T0{h}:00:00" for h in range(8, 18)]
    profile: Dict[str, float] = {}
    for ts in timestamps:
        hour = int(ts[11:13])
        if hour < 9:
            occ = 0.2
        elif hour < 17:
            occ = 0.8
        else:
            occ = 0.3
        profile[ts] = occ
    return profile
