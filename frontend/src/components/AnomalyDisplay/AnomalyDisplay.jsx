import React from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

function AnomalyDisplay({ anomalies = [], metric = "energy" }) {
  // Process anomalies for visualization
  const chartData = anomalies.map((anomaly) => ({
    x: new Date(anomaly.timestamp).getTime(),
    y: anomaly.value,
    score: anomaly.score,
    isAnomaly: anomaly.is_anomaly,
  }));

  const anomalyPoints = chartData.filter(d => d.isAnomaly);
  const normalPoints = chartData.filter(d => !d.isAnomaly);

  const getAnomalyColor = (score) => {
    if (score > 0.8) return "#ef4444"; // red
    if (score > 0.6) return "#f59e0b"; // orange
    return "#22c55e"; // green
  };

  return (
    <div className="anomaly-display">
      <h2>Anomaly Detection: {metric}</h2>
      
      <div className="anomaly-stats">
        <div className="stat">
          <span className="stat-label">Total Points:</span>
          <span className="stat-value">{anomalies.length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Anomalies:</span>
          <span className="stat-value anomaly-count">
            {anomalies.filter(a => a.is_anomaly).length}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Anomaly Rate:</span>
          <span className="stat-value">
            {((anomalies.filter(a => a.is_anomaly).length / (anomalies.length || 1)) * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            type="number" 
            dataKey="x" 
            domain={['dataMin', 'dataMax']}
            tickFormatter={(value) => new Date(value).toLocaleTimeString()}
          />
          <YAxis 
            type="number" 
            dataKey="y" 
            label={{ value: metric, angle: -90, position: 'insideLeft' }}
          />
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }}
            formatter={(value, name) => {
              if (name === 'y') return [value.toFixed(2), metric];
              return value;
            }}
            labelFormatter={(value) => new Date(value).toLocaleString()}
          />
          <Scatter name="Normal" data={normalPoints} fill="#22c55e">
            {normalPoints.map((entry, index) => (
              <Cell key={`cell-normal-${index}`} fill="#22c55e" opacity={0.6} />
            ))}
          </Scatter>
          <Scatter name="Anomaly" data={anomalyPoints} fill="#ef4444">
            {anomalyPoints.map((entry, index) => (
              <Cell 
                key={`cell-anomaly-${index}`} 
                fill={getAnomalyColor(entry.score)} 
                opacity={0.8}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      <div className="anomaly-list">
        <h3>Detected Anomalies</h3>
        <ul>
          {anomalies
            .filter(a => a.is_anomaly)
            .slice(0, 10)
            .map((anomaly, idx) => (
              <li key={idx} className="anomaly-item">
                <span className="anomaly-time">
                  {new Date(anomaly.timestamp).toLocaleString()}
                </span>
                <span className="anomaly-value">Value: {anomaly.value.toFixed(2)}</span>
                <span className="anomaly-score">Score: {(anomaly.score * 100).toFixed(1)}%</span>
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
}

export default AnomalyDisplay;
