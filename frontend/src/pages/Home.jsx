import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Chatbot from "../components/Chatbot/Chatbot";
import "../styles/homepage.css";

function Home() {
  const navigate = useNavigate();
  const [selectedZone, setSelectedZone] = useState("");
  const [floor, setFloor] = useState("");

  const zones = [
    { id: "zone-east", label: "Zone East" },
    { id: "zone-west", label: "Zone West" },
    { id: "zone-core", label: "Zone Core" },
  ];

  const floors = [
    { id: "1", label: "Floor 1" },
    { id: "2", label: "Floor 2" },
    { id: "3", label: "Floor 3" },
    { id: "4", label: "Floor 4" },
    { id: "5", label: "Floor 5" },
    { id: "6", label: "Floor 6" },
  ];

  const quickActions = [
    { id: "energy", label: "Energy Forecast", icon: "→", path: "/dashboard" },
    { id: "occupancy", label: "Occupancy", icon: "→", path: "/analytics" },
    { id: "thermal", label: "Thermal Analysis", icon: "→", path: "/twin" },
  ];

  const handleSearch = (e) => {
    e.preventDefault();
    const queryParams = new URLSearchParams();

    if (selectedZone) queryParams.append("zone", selectedZone);
    if (floor) queryParams.append("floor", floor);

    // Navigate to dashboard with search parameters
    navigate(`/dashboard?${queryParams.toString()}`);
  };

  return (
    <div className="homepage">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-overlay"></div>
        <div className="hero-content">
          <h1 className="hero-headline">
            Optimize Your Building's Performance with Digital Twin Technology
          </h1>

          {/* Search Panel */}
          <div className="search-panel">
            <form onSubmit={handleSearch} className="search-form">
              <div className="search-field">
                <label htmlFor="zone">Zone</label>
                <select
                  id="zone"
                  value={selectedZone}
                  onChange={(e) => setSelectedZone(e.target.value)}
                >
                  <option value="">Select Zone</option>
                  <option value="zone-east">Zone East</option>
                  <option value="zone-west">Zone West</option>
                  <option value="zone-core">Zone Core</option>
                </select>
              </div>

              <div className="search-field">
                <label htmlFor="floor">Floor</label>
                <select
                  id="floor"
                  value={floor}
                  onChange={(e) => setFloor(e.target.value)}
                >
                  <option value="">Select Floor</option>
                  {floors.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.label}
                    </option>
                  ))}
                </select>
              </div>

              <button type="submit" className="search-btn" aria-label="Search">
                <span className="search-icon">🔍</span>
                Search
              </button>
            </form>
          </div>

          {/* Quick Action Buttons */}
          <div className="quick-actions">
            {quickActions.map((action) => (
              <Link
                key={action.id}
                to={action.path}
                className="quick-action-btn"
              >
                {action.label} <span>{action.icon}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Secondary Navigation Section */}
      <section className="secondary-nav-section">
        <div className="secondary-nav-container">
          <h2 className="secondary-nav-title">Explore Building Intelligence</h2>
          <div className="secondary-nav-grid">
            <Link to="/dashboard" className="nav-card">
              <div className="nav-card-icon">📊</div>
              <h3>Dashboard</h3>
              <p>Monitor real-time energy consumption, occupancy patterns, and HVAC performance metrics</p>
            </Link>
            <Link to="/analytics" className="nav-card">
              <div className="nav-card-icon">📈</div>
              <h3>Analytics</h3>
              <p>Advanced forecasting, anomaly detection, and optimization recommendations</p>
            </Link>
            <Link to="/twin" className="nav-card">
              <div className="nav-card-icon">🔄</div>
              <h3>Twin View</h3>
              <p>Interactive 3D digital twin with thermal modeling and simulation capabilities</p>
            </Link>
          </div>
        </div>
      </section>
      {/* Chatbot */}
      <Chatbot />
    </div>
  );
}

export default Home;
