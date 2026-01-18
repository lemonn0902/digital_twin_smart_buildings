import React, { useState, useEffect } from "react";
import "../styles/building-info.css";

const BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "/api";

function BuildingOverview() {
  const [buildingData, setBuildingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBuildingData();
  }, []);

  const fetchBuildingData = async () => {
    try {
      // Fetch from backend dashboard endpoint which includes building info
      const response = await fetch(`${BASE}/dashboard/overview/demo-building`);
      if (!response.ok) throw new Error("Failed to fetch building data");
      const data = await response.json();
      setBuildingData(data.building || {});
    } catch (err) {
      console.error("Error fetching building data:", err);
      // Use mock data as fallback
      setBuildingData({
        building_id: "demo-building",
        primary_use: "Office",
        square_feet: 27000,
        year_built: 2010,
        floors: 2,
        zones: 6,
        total_area_m2: 2508,
        hvac_zones: 6,
        energy_meters: 12,
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="building-info-container">
        <div className="loading">Loading building information...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="building-info-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="building-info-container">
      <div className="building-overview">
        <div className="overview-header">
          <h1>Building Overview</h1>
          <p className="subtitle">General information and key metrics</p>
        </div>

        <div className="info-grid">
          {/* Basic Information Card */}
          <div className="info-card">
            <div className="card-icon">🏢</div>
            <div className="card-content">
              <h3>Building Identity</h3>
              <div className="info-item">
                <span className="label">Building ID:</span>
                <span className="value">{buildingData?.building_id || "demo-building"}</span>
              </div>
              <div className="info-item">
                <span className="label">Primary Use:</span>
                <span className="value">{buildingData?.primary_use || "Office"}</span>
              </div>
              <div className="info-item">
                <span className="label">Year Built:</span>
                <span className="value">{buildingData?.year_built || 2010}</span>
              </div>
            </div>
          </div>

          {/* Size & Space Card */}
          <div className="info-card">
            <div className="card-icon">📐</div>
            <div className="card-content">
              <h3>Building Size</h3>
              <div className="info-item">
                <span className="label">Total Area:</span>
                <span className="value">
                  {buildingData?.total_area_m2 
                    ? `${buildingData.total_area_m2.toLocaleString()} m²`
                    : `${buildingData?.square_feet ? (buildingData.square_feet * 0.092903).toFixed(0) : "N/A"} m²`
                  }
                </span>
              </div>
              <div className="info-item">
                <span className="label">Square Feet:</span>
                <span className="value">{buildingData?.square_feet?.toLocaleString() || "27,000"} sq ft</span>
              </div>
              <div className="info-item">
                <span className="label">Number of Floors:</span>
                <span className="value">{buildingData?.floors || 2}</span>
              </div>
            </div>
          </div>

          {/* Systems Card */}
          <div className="info-card">
            <div className="card-icon">⚙️</div>
            <div className="card-content">
              <h3>Building Systems</h3>
              <div className="info-item">
                <span className="label">HVAC Zones:</span>
                <span className="value">{buildingData?.hvac_zones || 6}</span>
              </div>
              <div className="info-item">
                <span className="label">Total Zones:</span>
                <span className="value">{buildingData?.zones || 6}</span>
              </div>
              <div className="info-item">
                <span className="label">Energy Meters:</span>
                <span className="value">{buildingData?.energy_meters || 12}</span>
              </div>
            </div>
          </div>

          {/* Status Card */}
          <div className="info-card">
            <div className="card-icon">📊</div>
            <div className="card-content">
              <h3>System Status</h3>
              <div className="status-item">
                <span className="status-label">Digital Twin:</span>
                <span className="status-badge active">Active</span>
              </div>
              <div className="status-item">
                <span className="status-label">Data Collection:</span>
                <span className="status-badge active">Online</span>
              </div>
              <div className="status-item">
                <span className="status-label">AI Monitoring:</span>
                <span className="status-badge active">Running</span>
              </div>
            </div>
          </div>
        </div>

        {/* Description Section */}
        <div className="overview-section">
          <h2>About This Building</h2>
          <p>
            This modern office building features advanced energy management systems and comprehensive
            monitoring capabilities. The digital twin leverages real-time sensor data from HVAC systems,
            occupancy sensors, and energy meters to provide insights into building performance and optimize
            operational efficiency.
          </p>
          <p>
            The building is divided into distinct zones across multiple floors, each with dedicated HVAC
            control and monitoring. Real-time analytics identify anomalies, forecast energy consumption,
            and recommend optimization strategies to reduce operational costs and environmental impact.
          </p>
        </div>

        {/* Key Capabilities */}
        <div className="overview-section">
          <h2>Key Capabilities</h2>
          <div className="capabilities-grid">
            <div className="capability">
              <div className="capability-icon">🔍</div>
              <h4>Anomaly Detection</h4>
              <p>Real-time detection of equipment failures and unusual patterns</p>
            </div>
            <div className="capability">
              <div className="capability-icon">🔮</div>
              <h4>Forecasting</h4>
              <p>Predict energy consumption and occupancy patterns</p>
            </div>
            <div className="capability">
              <div className="capability-icon">💡</div>
              <h4>Smart Recommendations</h4>
              <p>AI-driven suggestions for energy optimization</p>
            </div>
            <div className="capability">
              <div className="capability-icon">📈</div>
              <h4>Performance Analytics</h4>
              <p>Comprehensive insights into building operations</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BuildingOverview;
