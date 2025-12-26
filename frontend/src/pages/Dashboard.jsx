import React, { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area,
} from "recharts";
import Suggestions from "../components/Suggestions/Suggestions";
import ForecastChart from "../components/ForecastChart/ForecastChart";
import OccupancyForecast from "../components/OccupancyForecast/OccupancyForecast";
import {
  fetchDashboardOverview,
  fetchLatestMetrics,
} from "../services/api";

function formatLabel(label) {
  return label
    .replace(/_/g, " ")
    .replace(/\b\w/g, (l) => l.toUpperCase());
}

function LiveMetrics({ latest }) {
  const zones = Object.entries(latest?.latest_values || {});
  if (zones.length === 0) {
    return <p className="muted">Waiting for live telemetry…</p>;
  }

  return (
    <div className="live-metrics-table">
      {zones.map(([zone, metrics]) => (
        <div key={zone} className="live-metric-row">
          <div className="live-zone">{zone}</div>
          <div className="live-metric">
            <span>Energy</span>
            <strong>{metrics.energy?.toFixed(1) ?? "--"} kWh</strong>
          </div>
          <div className="live-metric">
            <span>Temp</span>
            <strong>{metrics.temperature?.toFixed(1) ?? "--"} °C</strong>
          </div>
          <div className="live-metric">
            <span>Occupancy</span>
            <strong>{(metrics.occupancy ?? 0).toFixed(2)}</strong>
          </div>
        </div>
      ))}
    </div>
  );
}

function AlertsPanel({ alerts }) {
  if (!alerts.length) {
    return <p className="muted">No active alerts.</p>;
  }
  return (
    <ul className="alerts-list">
      {alerts.map((alert) => (
        <li key={alert.id} className={`alert-card ${alert.severity}`}>
          <div className="alert-header">
            <span className="alert-severity">{alert.severity}</span>
            <span className="alert-time">
              {new Date(alert.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <h4>{alert.title}</h4>
          <p>{alert.message}</p>
        </li>
      ))}
    </ul>
  );
}

function DashboardPage() {
  const [overview, setOverview] = useState(null);
  const [latest, setLatest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await fetchDashboardOverview("demo-building");
        setOverview(data);
      } catch (err) {
        setError(err.message || "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    let timer;
    async function pollLatest() {
      try {
        const data = await fetchLatestMetrics("demo-building");
        setLatest(data);
      } catch (err) {
        // Ignore transient polling errors
        console.error("Latest metrics error:", err);
      }
    }
    pollLatest();
    timer = setInterval(pollLatest, 10000);
    return () => clearInterval(timer);
  }, []);

  const chartData = useMemo(() => overview?.charts || [], [overview]);

  const buildingName =
    overview?.building?.name ||
    overview?.building?.building_id ||
    "Building";

  const kpis = overview?.kpis || {};
  const carbon = overview?.carbon;

  return (
    <section className="monitoring-dashboard">
      <div className="dashboard-decorative-circles">
        <div className="decorative-circle circle-1"></div>
        <div className="decorative-circle circle-2"></div>
        <div className="decorative-circle circle-3"></div>
        <div className="decorative-circle circle-4"></div>
      </div>
      <div className="dashboard-header">
        <div>
          <h1>{buildingName}</h1>
          <p className="muted">
            Real-time view of energy, comfort, and alerts for the digital twin.
          </p>
        </div>
        {overview?.building?.primary_use && (
          <div className="building-pill">
            {overview.building.primary_use} ·{" "}
            {overview.building.sqft?.toLocaleString()} sqft
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <p>Loading dashboard...</p>
      ) : (
        <>
          <div className="kpi-grid">
            {Object.entries(kpis).map(([key, value]) => (
              <div className="kpi-card" key={key}>
                <span className="kpi-label">{formatLabel(key)}</span>
                <span className="kpi-value">
                  {typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : value}
                </span>
              </div>
            ))}
            {carbon && (
              <div className="kpi-card carbon">
                <span className="kpi-label">Carbon Today</span>
                <span className="kpi-value">
                  {carbon.today_tonnes.toFixed(3)} tCO₂e
                </span>
                <span className={`kpi-trend ${carbon.delta_percent >= 0 ? "up" : "down"}`}>
                  {carbon.delta_percent >= 0 ? "▲" : "▼"}{" "}
                  {Math.abs(carbon.delta_percent).toFixed(1)}% vs. yesterday
                </span>
              </div>
            )}
          </div>

          <div className="dashboard-charts-row">
            <div className="chart-card">
              <div className="chart-card-header">
                <h3>Energy · Occupancy · Comfort</h3>
              </div>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                    }
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                  />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="energy"
                    stroke="#4f46e5"
                    name="Energy (kWh)"
                    dot={false}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="occupancy"
                    stroke="#22c55e"
                    name="Occupancy"
                    dot={false}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="temperature"
                    stroke="#f59e0b"
                    name="Temperature (°C)"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-card">
              <div className="chart-card-header">
                <h3>Carbon Footprint Trend</h3>
              </div>
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorCarbon" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.6} />
                      <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleTimeString([], { hour: "2-digit" })
                    }
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                  />
                  <Area
                    type="monotone"
                    dataKey="carbon"
                    stroke="#14b8a6"
                    fillOpacity={1}
                    fill="url(#colorCarbon)"
                    name="tCO₂e"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="dashboard-lower-grid">
            <div className="card">
              <div className="card-header">
                <h3>Live Telemetry</h3>
                <span className="muted">
                  Updated {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
              <LiveMetrics latest={latest} />
            </div>
            <div className="card">
              <div className="card-header">
                <h3>Active Alerts</h3>
              </div>
              <AlertsPanel alerts={overview?.alerts || []} />
            </div>
          </div>

          <div className="dashboard-charts-row">
            <div className="chart-card">
              <ForecastChart buildingId="demo-building" horizonHours={24} />
            </div>
          </div>

          <div className="dashboard-charts-row">
            <div className="chart-card">
              <OccupancyForecast buildingId="demo-building" horizonHours={12} />
            </div>
          </div>

          <div className="card suggestions-card">
            <Suggestions suggestions={overview?.suggestions || []} />
          </div>
        </>
      )}
    </section>
  );
}

export default DashboardPage;

