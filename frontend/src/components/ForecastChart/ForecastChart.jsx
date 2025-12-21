import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import { fetchEnergyForecast } from "../../services/api";

function ForecastChart({ buildingId, horizonHours = 24 }) {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadForecast() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchEnergyForecast(buildingId, horizonHours);
        setForecast(data);
      } catch (err) {
        setError(err.message || "Failed to load forecast");
      } finally {
        setLoading(false);
      }
    }

    if (buildingId) {
      loadForecast();
    }
  }, [buildingId, horizonHours]);

  if (loading) {
    return (
      <div className="forecast-chart loading">
        <p>Loading energy forecast...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="forecast-chart error">
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!forecast || !forecast.forecast || forecast.forecast.length === 0) {
    return (
      <div className="forecast-chart no-data">
        <p>No forecast data available</p>
      </div>
    );
  }

  // Prepare chart data
  const chartData = forecast.forecast.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    }),
    timestamp: point.timestamp,
    energy: parseFloat(point.energy_kwh.toFixed(2)),
    confidenceLower: point.confidence_lower
      ? parseFloat(point.confidence_lower.toFixed(2))
      : null,
    confidenceUpper: point.confidence_upper
      ? parseFloat(point.confidence_upper.toFixed(2))
      : null,
  }));

  return (
    <div className="forecast-chart">
      <div className="forecast-header">
        <h3>Energy Consumption Forecast</h3>
        <div className="forecast-meta">
          <span className="forecast-horizon">
            Next {forecast.horizon_hours} hours
          </span>
          {forecast.model_available ? (
            <span className="model-badge model-available">ML Model</span>
          ) : (
            <span className="model-badge model-synthetic">Pattern-Based</span>
          )}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorEnergy" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis label={{ value: "Energy (kWh)", angle: -90, position: "insideLeft" }} />
          <Tooltip
            formatter={(value, name) => {
              if (name === "energy") return [`${value} kWh`, "Forecasted Energy"];
              return [value, name];
            }}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Legend />
          {chartData[0].confidenceLower !== null && (
            <Area
              type="monotone"
              dataKey="confidenceLower"
              stroke="#8884d8"
              fillOpacity={0}
              strokeDasharray="5 5"
              strokeWidth={1}
              name="Confidence Lower"
            />
          )}
          <Area
            type="monotone"
            dataKey="energy"
            stroke="#4f46e5"
            strokeWidth={2}
            fill="url(#colorEnergy)"
            name="Forecasted Energy"
          />
          {chartData[0].confidenceUpper !== null && (
            <Area
              type="monotone"
              dataKey="confidenceUpper"
              stroke="#8884d8"
              fillOpacity={0}
              strokeDasharray="5 5"
              strokeWidth={1}
              name="Confidence Upper"
            />
          )}
        </AreaChart>
      </ResponsiveContainer>

      <div className="forecast-stats">
        <div className="stat-item">
          <span className="stat-label">Average:</span>
          <span className="stat-value">
            {(
              chartData.reduce((sum, d) => sum + d.energy, 0) /
              chartData.length
            ).toFixed(2)}{" "}
            kWh
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Peak:</span>
          <span className="stat-value">
            {Math.max(...chartData.map((d) => d.energy)).toFixed(2)} kWh
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Total:</span>
          <span className="stat-value">
            {chartData
              .reduce((sum, d) => sum + d.energy, 0)
              .toFixed(2)}{" "}
            kWh
          </span>
        </div>
      </div>
    </div>
  );
}

export default ForecastChart;
