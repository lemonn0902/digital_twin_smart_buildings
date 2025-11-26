import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

function Dashboard({ simulationData, anomalies, suggestions }) {
  // Process simulation data for charts
  const chartData = simulationData?.points?.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    occupancy: point.occupancy,
    energy: point.energy_kwh,
    temperature: point.temperature_c,
  })) || [];

  // Calculate metrics
  const totalEnergy = simulationData?.points?.reduce((sum, p) => sum + p.energy_kwh, 0) || 0;
  const avgTemperature = simulationData?.points?.reduce((sum, p) => sum + p.temperature_c, 0) / (simulationData?.points?.length || 1) || 0;
  const anomalyCount = anomalies?.filter(a => a.is_anomaly)?.length || 0;
  const totalSavings = suggestions?.reduce((sum, s) => sum + s.estimated_savings_kwh, 0) || 0;

  return (
    <div className="dashboard">
      <div className="dashboard-metrics">
        <div className="metric-card">
          <h3>Total Energy</h3>
          <p className="metric-value">{totalEnergy.toFixed(2)} kWh</p>
        </div>
        <div className="metric-card">
          <h3>Avg Temperature</h3>
          <p className="metric-value">{avgTemperature.toFixed(1)}°C</p>
        </div>
        <div className="metric-card">
          <h3>Anomalies</h3>
          <p className="metric-value">{anomalyCount}</p>
        </div>
        <div className="metric-card">
          <h3>Potential Savings</h3>
          <p className="metric-value">{totalSavings.toFixed(1)} kWh</p>
        </div>
      </div>

      <div className="dashboard-charts">
        <div className="chart-container">
          <h3>Energy & Occupancy Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="energy" stroke="#4f46e5" name="Energy (kWh)" />
              <Line yAxisId="right" type="monotone" dataKey="occupancy" stroke="#22c55e" name="Occupancy" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Temperature Profile</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="temperature" stroke="#f59e0b" name="Temperature (°C)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
