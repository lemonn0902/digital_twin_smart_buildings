const BASE = "/api";

export async function runSimulation(buildingId, startTime, endTime, resolutionMinutes = 60) {
  const res = await fetch(`${BASE}/simulation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      building_id: buildingId,
      start_time: startTime,
      end_time: endTime,
      resolution_minutes: resolutionMinutes,
      scenario: "baseline",
    }),
  });
  if (!res.ok) throw new Error("Failed to run simulation");
  return res.json();
}

export async function fetchLayout(buildingId) {
  const res = await fetch(`${BASE}/layout/${buildingId}`);
  if (!res.ok) throw new Error("Failed to load layout");
  return res.json();
}

export async function fetchAnomalies(buildingId, metric) {
  const res = await fetch(`${BASE}/anomalies/detect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      building_id: buildingId,
      metric,
      start_time: "2025-01-01T08:00:00",
      end_time: "2025-01-01T18:00:00",
    }),
  });
  if (!res.ok) throw new Error("Failed to fetch anomalies");
  return res.json();
}

export async function fetchSuggestions(buildingId) {
  const res = await fetch(`${BASE}/suggestions/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      building_id: buildingId,
      horizon_hours: 24,
    }),
  });
  if (!res.ok) throw new Error("Failed to fetch suggestions");
  return res.json();
}

export async function applySuggestion(buildingId, suggestion) {
  const res = await fetch(`${BASE}/suggestions/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      building_id: buildingId,
      suggestion,
    }),
  });
  if (!res.ok) throw new Error("Failed to apply suggestion");
  return res.json();
}

export async function dismissSuggestion(buildingId, suggestionId, suggestion) {
  const res = await fetch(`${BASE}/suggestions/dismiss`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      building_id: buildingId,
      suggestion_id: suggestionId,
      suggestion,
    }),
  });
  if (!res.ok) throw new Error("Failed to dismiss suggestion");
  return res.json();
}

export async function fetchAppliedActions(buildingId) {
  const res = await fetch(`${BASE}/suggestions/applied/${buildingId}`);
  if (!res.ok) throw new Error("Failed to fetch applied actions");
  return res.json();
}

export async function fetchDashboardOverview(buildingId) {
  const res = await fetch(`${BASE}/dashboard/overview/${buildingId}`);
  if (!res.ok) throw new Error("Failed to load dashboard overview");
  return res.json();
}

export async function fetchLatestMetrics(buildingId) {
  const res = await fetch(`${BASE}/historical/latest/${buildingId}`);
  if (!res.ok) throw new Error("Failed to load latest metrics");
  return res.json();
}

export async function fetchEnergyForecast(buildingId, horizonHours = 24) {
  const res = await fetch(`${BASE}/forecast/energy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      building_id: buildingId,
      horizon_hours: horizonHours,
    }),
  });
  if (!res.ok) throw new Error("Failed to fetch energy forecast");
  return res.json();
}

export async function fetchOccupancyForecast(buildingId, horizonHours = 12) {
  const res = await fetch(`${BASE}/forecast/occupancy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      building_id: buildingId,
      horizon_hours: horizonHours,
    }),
  });
  if (!res.ok) throw new Error("Failed to fetch occupancy forecast");
  return res.json();
}
