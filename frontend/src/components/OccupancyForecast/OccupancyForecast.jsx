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
import { fetchOccupancyForecast } from "../../services/api";

function OccupancyForecast({ buildingId, horizonHours = 12, actionsVersion }) {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadForecast() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchOccupancyForecast(buildingId, horizonHours);
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
  }, [buildingId, horizonHours, actionsVersion]);

  if (loading) {
    return (
      <div className="occupancy-forecast loading">
        <p>Loading occupancy forecast...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="occupancy-forecast error">
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!forecast || !forecast.forecast || forecast.forecast.length === 0) {
    return (
      <div className="occupancy-forecast no-data">
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
    occupancy: parseFloat((point.occupancy * 100).toFixed(1)), // Convert to percentage
    confidenceLower: point.confidence_lower
      ? parseFloat((point.confidence_lower * 100).toFixed(1))
      : null,
    confidenceUpper: point.confidence_upper
      ? parseFloat((point.confidence_upper * 100).toFixed(1))
      : null,
  }));

  // Calculate statistics
  const avgOccupancy = chartData.reduce((sum, d) => sum + d.occupancy, 0) / chartData.length;
  const peakOccupancy = Math.max(...chartData.map((d) => d.occupancy));
  const lowOccupancy = Math.min(...chartData.map((d) => d.occupancy));

  return (
    <div className="occupancy-forecast">
      <div className="forecast-header">
        <h3>Occupancy Forecast</h3>
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
            <linearGradient id="colorOccupancy" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis
            label={{ value: "Occupancy (%)", angle: -90, position: "insideLeft" }}
            domain={[0, 100]}
          />
          <Tooltip
            formatter={(value, name) => {
              if (name === "occupancy") return [`${value}%`, "Forecasted Occupancy"];
              return [value, name];
            }}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Legend />
          {chartData[0].confidenceLower !== null && (
            <Area
              type="monotone"
              dataKey="confidenceLower"
              stroke="#86efac"
              fillOpacity={0}
              strokeDasharray="5 5"
              strokeWidth={1}
              name="Confidence Lower"
            />
          )}
          <Area
            type="monotone"
            dataKey="occupancy"
            stroke="#22c55e"
            strokeWidth={2}
            fill="url(#colorOccupancy)"
            name="Forecasted Occupancy"
          />
          {chartData[0].confidenceUpper !== null && (
            <Area
              type="monotone"
              dataKey="confidenceUpper"
              stroke="#86efac"
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
          <span className="stat-value">{avgOccupancy.toFixed(1)}%</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Peak:</span>
          <span className="stat-value">{peakOccupancy.toFixed(1)}%</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Low:</span>
          <span className="stat-value">{lowOccupancy.toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}

export default OccupancyForecast;
