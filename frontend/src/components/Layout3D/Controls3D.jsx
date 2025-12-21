import React from "react";

const METRIC_OPTIONS = [
  { value: "energy", label: "Energy", color: "#4f46e5" },
  { value: "temperature", label: "Temperature", color: "#f59e0b" },
  { value: "occupancy", label: "Occupancy", color: "#22c55e" },
];

function Controls3D({ selectedMetric, onMetricChange, selectedZone, onCloseZoneDetails }) {
  return (
    <div className="controls-3d">
      <div className="controls-header">
        <h3>3D Building View</h3>
      </div>

      <div className="controls-section">
        <label>Visualization Metric:</label>
        <div className="metric-buttons">
          {METRIC_OPTIONS.map((option) => (
            <button
              key={option.value}
              className={`metric-button ${selectedMetric === option.value ? "active" : ""}`}
              onClick={() => onMetricChange(option.value)}
              style={{
                borderColor: option.color,
                backgroundColor: selectedMetric === option.value ? option.color : "transparent",
                color: selectedMetric === option.value ? "white" : option.color,
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {selectedZone && (
        <div className="zone-details-panel">
          <div className="zone-details-header">
            <h4>{selectedZone.name}</h4>
            <button onClick={onCloseZoneDetails} className="close-button">
              ×
            </button>
          </div>
          <div className="zone-details-content">
            <p><strong>Zone ID:</strong> {selectedZone.id}</p>
            <p><strong>Floor:</strong> {selectedZone.floor}</p>
            <p><strong>Area:</strong> {selectedZone.area_m2.toFixed(1)} m²</p>
            {selectedZone.neighbors && selectedZone.neighbors.length > 0 && (
              <p><strong>Neighbors:</strong> {selectedZone.neighbors.join(", ")}</p>
            )}
          </div>
        </div>
      )}

      <div className="controls-help">
        <p>💡 Click on zones to view details</p>
        <p>🖱️ Use mouse to rotate, pan, and zoom</p>
      </div>
    </div>
  );
}

export default Controls3D;
