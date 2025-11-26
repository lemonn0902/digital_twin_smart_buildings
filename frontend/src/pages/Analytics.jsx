import React, { useEffect, useState } from "react";
import { fetchAnomalies, fetchSuggestions } from "../services/api";
import AnomalyDisplay from "../components/AnomalyDisplay/AnomalyDisplay";
import Suggestions from "../components/Suggestions/Suggestions";

function Analytics() {
  const [anomalies, setAnomalies] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState("energy");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function init() {
      setLoading(true);
      try {
        const [anomalyData, suggestionData] = await Promise.all([
          fetchAnomalies("demo-building", selectedMetric),
          fetchSuggestions("demo-building"),
        ]);
        setAnomalies(anomalyData);
        setSuggestions(suggestionData);
      } catch (err) {
        console.error("Failed to load analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [selectedMetric]);

  return (
    <section className="analytics">
      <h1>Analytics</h1>
      
      <div className="metric-selector">
        <label>Select Metric:</label>
        <select 
          value={selectedMetric} 
          onChange={(e) => setSelectedMetric(e.target.value)}
        >
          <option value="energy">Energy</option>
          <option value="temperature">Temperature</option>
          <option value="co2">CO₂</option>
          <option value="occupancy">Occupancy</option>
        </select>
      </div>

      {loading ? (
        <p>Loading analytics...</p>
      ) : (
        <div className="analytics-content">
          <div className="analytics-section">
            <AnomalyDisplay anomalies={anomalies} metric={selectedMetric} />
          </div>
          <div className="analytics-section">
            <Suggestions suggestions={suggestions} />
          </div>
        </div>
      )}
    </section>
  );
}

export default Analytics;


