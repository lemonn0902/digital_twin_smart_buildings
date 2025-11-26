import React, { useState } from "react";
import { runSimulation } from "../../services/api";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

function SimulationPanel({ buildingId = "demo-building" }) {
  const [loading, setLoading] = useState(false);
  const [simulation, setSimulation] = useState(null);
  const [error, setError] = useState(null);
  const [startTime, setStartTime] = useState("2025-01-01T08:00");
  const [endTime, setEndTime] = useState("2025-01-01T18:00");
  const [resolution, setResolution] = useState(60);

  const handleRunSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await runSimulation(buildingId, startTime, endTime, resolution);
      setSimulation(result);
    } catch (err) {
      setError(err.message || "Failed to run simulation");
    } finally {
      setLoading(false);
    }
  };

  const chartData = simulation?.points?.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    occupancy: (point.occupancy * 100).toFixed(1),
    energy: point.energy_kwh.toFixed(2),
    temperature: point.temperature_c.toFixed(1),
  })) || [];

  return (
    <div className="simulation-panel">
      <h2>Run Simulation</h2>
      
      <div className="simulation-controls">
        <div className="control-group">
          <label>Building ID</label>
          <input type="text" value={buildingId} readOnly />
        </div>
        <div className="control-group">
          <label>Start Time</label>
          <input 
            type="datetime-local" 
            value={startTime} 
            onChange={(e) => setStartTime(e.target.value)}
          />
        </div>
        <div className="control-group">
          <label>End Time</label>
          <input 
            type="datetime-local" 
            value={endTime} 
            onChange={(e) => setEndTime(e.target.value)}
          />
        </div>
        <div className="control-group">
          <label>Resolution (minutes)</label>
          <select value={resolution} onChange={(e) => setResolution(Number(e.target.value))}>
            <option value={15}>15 min</option>
            <option value={30}>30 min</option>
            <option value={60}>60 min</option>
          </select>
        </div>
        <button 
          className="run-button" 
          onClick={handleRunSimulation} 
          disabled={loading}
        >
          {loading ? "Running..." : "Run Simulation"}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {simulation && (
        <div className="simulation-results">
          <h3>Results: {simulation.scenario}</h3>
          <p>{simulation.points.length} data points generated</p>
          
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="left" label={{ value: 'Energy (kWh)', angle: -90 }} />
              <YAxis yAxisId="right" orientation="right" label={{ value: 'Occupancy (%) / Temp (°C)', angle: 90 }} />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="energy" stroke="#4f46e5" name="Energy (kWh)" strokeWidth={2} />
              <Line yAxisId="right" type="monotone" dataKey="occupancy" stroke="#22c55e" name="Occupancy (%)" />
              <Line yAxisId="right" type="monotone" dataKey="temperature" stroke="#f59e0b" name="Temperature (°C)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default SimulationPanel;
