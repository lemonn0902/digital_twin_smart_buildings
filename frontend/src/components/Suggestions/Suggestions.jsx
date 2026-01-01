import React from "react";

function Suggestions({ suggestions = [], appliedActions = [], onApply, onDismiss, busySuggestionId }) {
  const getRiskColor = (risk) => {
    switch (risk?.toLowerCase()) {
      case "low": return "#22c55e";
      case "medium": return "#f59e0b";
      case "high": return "#ef4444";
      default: return "#6b7280";
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case "hvac_schedule": return "❄️";
      case "setpoint_change": return "🌡️";
      case "ventilation": return "💨";
      default: return "💡";
    }
  };

  return (
    <div className="suggestions">
      <h2>Energy Optimization Suggestions</h2>

      {suggestions.length === 0 ? (
        <p className="no-suggestions">No suggestions available at this time.</p>
      ) : (
        <div className="suggestions-grid">
          {suggestions.map((suggestion) => (
            <div key={suggestion.id} className="suggestion-card">
              <div className="suggestion-header">
                <span className="suggestion-icon">{getTypeIcon(suggestion.type)}</span>
                <span className="suggestion-type">{suggestion.type.replace(/_/g, ' ')}</span>
              </div>

              <p className="suggestion-description">{suggestion.description}</p>

              <div className="suggestion-metrics">
                <div className="metric">
                  <span className="metric-label">Estimated Savings</span>
                  <span className="metric-value savings">
                    {suggestion.estimated_savings_kwh.toFixed(1)} kWh
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Comfort Risk</span>
                  <span
                    className="metric-value risk"
                    style={{ color: getRiskColor(suggestion.comfort_risk) }}
                  >
                    {suggestion.comfort_risk}
                  </span>
                </div>
              </div>

              <div className="suggestion-actions">
                <button
                  className="action-button primary"
                  onClick={() => onApply && onApply(suggestion)}
                  disabled={busySuggestionId === suggestion.id}
                >
                  Apply
                </button>
                <button
                  className="action-button secondary"
                  onClick={() => onDismiss && onDismiss(suggestion)}
                  disabled={busySuggestionId === suggestion.id}
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="total-savings">
          <strong>Total Potential Savings: </strong>
          {suggestions.reduce((sum, s) => sum + s.estimated_savings_kwh, 0).toFixed(1)} kWh
        </div>
      )}

      <h2>Applied Actions</h2>
      {appliedActions.length === 0 ? (
        <p className="no-suggestions">No applied actions yet.</p>
      ) : (
        <div className="suggestions-grid">
          {appliedActions.map((action) => (
            <div key={action.id} className="suggestion-card">
              <div className="suggestion-header">
                <span className="suggestion-icon">{getTypeIcon(action.type)}</span>
                <span className="suggestion-type">{action.type.replace(/_/g, " ")}</span>
              </div>
              <p className="suggestion-description">{action.description}</p>
              <div className="suggestion-metrics">
                <div className="metric">
                  <span className="metric-label">Applied</span>
                  <span className="metric-value savings">
                    {new Date(action.applied_at).toLocaleString()}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Comfort Risk</span>
                  <span className="metric-value risk" style={{ color: getRiskColor(action.comfort_risk) }}>
                    {action.comfort_risk}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Suggestions;
