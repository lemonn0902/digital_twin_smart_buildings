import React, { useState, useEffect } from "react";
import "../styles/building-info.css";

const BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "/api";

function BuildingSystems() {
  const [systemsData, setSystemsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemsData();
  }, []);

  const fetchSystemsData = async () => {
    try {
      // Try to fetch from dashboard for real data
      const response = await fetch(`${BASE}/dashboard/overview/demo-building`);
      if (!response.ok) throw new Error("Failed to fetch systems data");
      const data = await response.json();
      setSystemsData(data);
    } catch (err) {
      console.error("Error fetching systems data:", err);
      // Use mock data as fallback
      setSystemsData({
        hvac_status: "operational",
        hvac_zones: 6,
        hvac_efficiency: 87,
        lighting_zones: 8,
        lighting_status: "operational",
        energy_monitoring: true,
        occupancy_sensors: 12,
        temperature_sensors: 18,
        humidity_sensors: 12,
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="building-info-container">
        <div className="loading">Loading building systems...</div>
      </div>
    );
  }

  const systems = [
    {
      id: "hvac",
      name: "HVAC System",
      icon: "❄️",
      status: "operational",
      description: "Heating, Ventilation & Air Conditioning",
      components: [
        { label: "Active Zones", value: "6", icon: "📍" },
        { label: "Efficiency Rating", value: "87%", icon: "⚡" },
        { label: "Control Points", value: "18", icon: "🎛️" },
      ],
      subSystems: [
        { name: "Chiller Unit", status: "operational", location: "Basement" },
        { name: "Boiler Unit", status: "operational", location: "Basement" },
        { name: "Air Handling Units", status: "operational", location: "Multiple Floors" },
        { name: "Ductwork Network", status: "operational", location: "Throughout Building" },
      ],
    },
    {
      id: "lighting",
      name: "Lighting Control System",
      icon: "💡",
      status: "operational",
      description: "Smart lighting with occupancy control",
      components: [
        { label: "Controlled Zones", value: "8", icon: "📍" },
        { label: "Dimmable Fixtures", value: "156", icon: "⚙️" },
        { label: "Occupancy Detectors", value: "24", icon: "👁️" },
      ],
      subSystems: [
        { name: "LED Panel Lighting", status: "operational", location: "All Floors" },
        { name: "Task Lighting", status: "operational", location: "Office Areas" },
        { name: "Emergency Lighting", status: "operational", location: "All Areas" },
        { name: "Outdoor Lighting", status: "operational", location: "Exterior" },
      ],
    },
    {
      id: "energy",
      name: "Energy Management",
      icon: "⚡",
      status: "monitoring",
      description: "Real-time energy monitoring and optimization",
      components: [
        { label: "Main Meter", value: "1", icon: "📊" },
        { label: "Sub-Meters", value: "11", icon: "📊" },
        { label: "Monitoring Points", value: "32", icon: "📍" },
      ],
      subSystems: [
        { name: "Main Power Input", status: "operational", location: "Electrical Room" },
        { name: "Backup Generator", status: "standby", location: "Basement" },
        { name: "UPS System", status: "operational", location: "Server Room" },
        { name: "Solar Panels", status: "operational", location: "Roof" },
      ],
    },
    {
      id: "sensors",
      name: "Sensor Network",
      icon: "📡",
      status: "operational",
      description: "Comprehensive environmental and occupancy monitoring",
      components: [
        { label: "Temperature Sensors", value: "18", icon: "🌡️" },
        { label: "Humidity Sensors", value: "12", icon: "💧" },
        { label: "Occupancy Sensors", value: "12", icon: "👥" },
      ],
      subSystems: [
        { name: "Temperature Monitoring", status: "operational", location: "All Zones" },
        { name: "Air Quality Monitoring", status: "operational", location: "Major Zones" },
        { name: "CO2 Detection", status: "operational", location: "Office Spaces" },
        { name: "Motion Detection", status: "operational", location: "Common Areas" },
      ],
    },
    {
      id: "safety",
      name: "Safety & Security",
      icon: "🔒",
      status: "operational",
      description: "Fire detection and access control systems",
      components: [
        { label: "Fire Detectors", value: "28", icon: "🚨" },
        { label: "Fire Suppressors", value: "6", icon: "🧯" },
        { label: "Access Points", value: "12", icon: "🚪" },
      ],
      subSystems: [
        { name: "Fire Detection System", status: "operational", location: "All Areas" },
        { name: "Emergency Exit Lighting", status: "operational", location: "All Exits" },
        { name: "Access Control System", status: "operational", location: "Main Entrances" },
        { name: "Security Cameras", status: "operational", location: "Common Areas" },
      ],
    },
    {
      id: "digital",
      name: "Digital Twin & Analytics",
      icon: "🤖",
      status: "operational",
      description: "AI-powered monitoring and optimization",
      components: [
        { label: "Data Collection", value: "Active", icon: "📥" },
        { label: "Anomaly Detection", value: "Active", icon: "🔍" },
        { label: "Forecasting", value: "Active", icon: "🔮" },
      ],
      subSystems: [
        { name: "Real-time Data Pipeline", status: "operational", location: "Cloud" },
        { name: "Anomaly Detection Engine", status: "operational", location: "Cloud" },
        { name: "Forecasting Models", status: "operational", location: "Cloud" },
        { name: "Optimization Engine", status: "operational", location: "Cloud" },
      ],
    },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case "operational":
        return "status-operational";
      case "monitoring":
        return "status-monitoring";
      case "standby":
        return "status-standby";
      case "warning":
        return "status-warning";
      default:
        return "status-unknown";
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case "operational":
        return "Operational";
      case "monitoring":
        return "Monitoring";
      case "standby":
        return "Standby";
      case "warning":
        return "Warning";
      default:
        return status;
    }
  };

  return (
    <div className="building-info-container">
      <div className="building-systems">
        <div className="overview-header">
          <h1>Building Systems</h1>
          <p className="subtitle">Comprehensive infrastructure overview</p>
        </div>

        <div className="systems-grid">
          {systems.map((system) => (
            <div key={system.id} className="system-card">
              <div className="system-header">
                <div className="system-title">
                  <span className="system-icon">{system.icon}</span>
                  <div>
                    <h3>{system.name}</h3>
                    <p className="system-description">{system.description}</p>
                  </div>
                </div>
                <span className={`system-status ${getStatusColor(system.status)}`}>
                  {getStatusText(system.status)}
                </span>
              </div>

              <div className="system-components">
                {system.components.map((component, idx) => (
                  <div key={idx} className="component-item">
                    <span className="component-icon">{component.icon}</span>
                    <div className="component-info">
                      <span className="component-label">{component.label}</span>
                      <span className="component-value">{component.value}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="subsystems">
                <h4>Sub-Systems</h4>
                <ul className="subsystem-list">
                  {system.subSystems.map((subsystem, idx) => (
                    <li key={idx} className="subsystem-item">
                      <span className="subsystem-indicator"></span>
                      <div className="subsystem-info">
                        <span className="subsystem-name">{subsystem.name}</span>
                        <span className="subsystem-location">{subsystem.location}</span>
                      </div>
                      <span className={`subsystem-status ${getStatusColor(subsystem.status)}`}>
                        {getStatusText(subsystem.status)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* System Health Summary */}
        <div className="system-health">
          <h2>System Health Summary</h2>
          <div className="health-stats">
            <div className="health-stat">
              <div className="stat-icon">✅</div>
              <div className="stat-info">
                <span className="stat-label">Operational Systems</span>
                <span className="stat-value">6/6</span>
              </div>
            </div>
            <div className="health-stat">
              <div className="stat-icon">⚠️</div>
              <div className="stat-info">
                <span className="stat-label">Systems Monitoring</span>
                <span className="stat-value">1</span>
              </div>
            </div>
            <div className="health-stat">
              <div className="stat-icon">📊</div>
              <div className="stat-info">
                <span className="stat-label">Total Sensors</span>
                <span className="stat-value">60+</span>
              </div>
            </div>
            <div className="health-stat">
              <div className="stat-icon">📈</div>
              <div className="stat-info">
                <span className="stat-label">Data Points/Day</span>
                <span className="stat-value">1M+</span>
              </div>
            </div>
          </div>
        </div>

        {/* Maintenance Notes */}
        <div className="maintenance-section">
          <h2>Maintenance & Alerts</h2>
          <div className="alert-info">
            <div className="alert-item no-alerts">
              <span className="alert-icon">✓</span>
              <span className="alert-text">No critical alerts at this time</span>
            </div>
            <div className="alert-note">
              <strong>Next Scheduled Maintenance:</strong> HVAC filter replacement (Filter Change) in 30 days
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BuildingSystems;
