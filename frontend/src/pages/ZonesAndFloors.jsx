import React, { useState, useEffect } from "react";
import "../styles/building-info.css";

const BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "/api";

function ZonesAndFloors() {
  const [zones, setZones] = useState([]);
  const [selectedFloor, setSelectedFloor] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [envData, setEnvData] = useState({});

  useEffect(() => {
    fetchZoneData();
    fetchEnvironmentalData();
  }, []);

  const fetchZoneData = async () => {
    try {
      const response = await fetch(`${BASE}/layout/demo-building`);
      if (!response.ok) throw new Error("Failed to fetch zone data");
      const data = await response.json();
      setZones(data.zones || getDefaultZones());
    } catch (err) {
      console.error("Error fetching zone data:", err);
      setZones(getDefaultZones());
    } finally {
      setLoading(false);
    }
  };

  const fetchEnvironmentalData = async () => {
    try {
      const response = await fetch(`${BASE}/historical/latest/demo-building`);
      if (response.ok) {
        const data = await response.json();
        setEnvData(data);
      }
    } catch (err) {
      console.error("Error fetching environmental data:", err);
    }
  };

  const getDefaultZones = () => [
    // Floor 1 - Zone East
    {
      id: "zone-east-f1",
      name: "Open Office - East",
      zone_type: "zone-east",
      floor: 1,
      area_m2: 250.0,
      neighbors: ["zone-west-f1"],
      occupancy_capacity: 60,
      hvac_zone: "HVAC-East-1",
      temperature: 22.5,
      humidity: 45,
      energy_kw: 15.2,
    },
    // Floor 1 - Zone West
    {
      id: "zone-west-f1",
      name: "Meeting & Conference - West",
      zone_type: "zone-west",
      floor: 1,
      area_m2: 180.0,
      neighbors: ["zone-east-f1", "zone-core-f1"],
      occupancy_capacity: 40,
      hvac_zone: "HVAC-West-1",
      temperature: 22.8,
      humidity: 44,
      energy_kw: 12.5,
    },
    // Floor 1 - Zone Core
    {
      id: "zone-core-f1",
      name: "Building Core - Corridors",
      zone_type: "zone-core",
      floor: 1,
      area_m2: 120.0,
      neighbors: ["zone-west-f1"],
      occupancy_capacity: 0,
      hvac_zone: "HVAC-Core-1",
      temperature: 21.9,
      humidity: 46,
      energy_kw: 5.8,
    },
    // Floor 2 - Zone East
    {
      id: "zone-east-f2",
      name: "Collaborative Workspace - East",
      zone_type: "zone-east",
      floor: 2,
      area_m2: 240.0,
      neighbors: ["zone-west-f2"],
      occupancy_capacity: 55,
      hvac_zone: "HVAC-East-2",
      temperature: 22.6,
      humidity: 43,
      energy_kw: 14.8,
    },
    // Floor 2 - Zone West
    {
      id: "zone-west-f2",
      name: "Management Offices - West",
      zone_type: "zone-west",
      floor: 2,
      area_m2: 200.0,
      neighbors: ["zone-east-f2", "zone-core-f2"],
      occupancy_capacity: 45,
      hvac_zone: "HVAC-West-2",
      temperature: 22.4,
      humidity: 45,
      energy_kw: 13.2,
    },
    // Floor 2 - Zone Core
    {
      id: "zone-core-f2",
      name: "Building Core - Services",
      zone_type: "zone-core",
      floor: 2,
      area_m2: 100.0,
      neighbors: ["zone-west-f2"],
      occupancy_capacity: 0,
      hvac_zone: "HVAC-Core-2",
      temperature: 21.8,
      humidity: 47,
      energy_kw: 6.5,
    },
    // Floor 3 - Zone East
    {
      id: "zone-east-f3",
      name: "Research Labs - East",
      zone_type: "zone-east",
      floor: 3,
      area_m2: 280.0,
      neighbors: ["zone-west-f3"],
      occupancy_capacity: 50,
      hvac_zone: "HVAC-East-3",
      temperature: 22.0,
      humidity: 50,
      energy_kw: 18.5,
    },
    // Floor 3 - Zone West
    {
      id: "zone-west-f3",
      name: "Testing Facilities - West",
      zone_type: "zone-west",
      floor: 3,
      area_m2: 220.0,
      neighbors: ["zone-east-f3", "zone-core-f3"],
      occupancy_capacity: 35,
      hvac_zone: "HVAC-West-3",
      temperature: 22.3,
      humidity: 48,
      energy_kw: 16.2,
    },
    // Floor 3 - Zone Core
    {
      id: "zone-core-f3",
      name: "Building Core - Utilities",
      zone_type: "zone-core",
      floor: 3,
      area_m2: 110.0,
      neighbors: ["zone-west-f3"],
      occupancy_capacity: 5,
      hvac_zone: "HVAC-Core-3",
      temperature: 20.5,
      humidity: 52,
      energy_kw: 8.2,
    },
    // Floors 4-6 follow similar pattern
    ...Array.from({ length: 3 }, (_, floorIdx) => {
      const floorNum = floorIdx + 4;
      return [
        {
          id: `zone-east-f${floorNum}`,
          name: `Office Space - East Floor ${floorNum}`,
          zone_type: "zone-east",
          floor: floorNum,
          area_m2: 230.0 + Math.random() * 50,
          neighbors: [`zone-west-f${floorNum}`],
          occupancy_capacity: 50,
          hvac_zone: `HVAC-East-${floorNum}`,
          temperature: 22.0 + Math.random() * 1.5,
          humidity: 44 + Math.random() * 4,
          energy_kw: 14.0 + Math.random() * 4,
        },
        {
          id: `zone-west-f${floorNum}`,
          name: `Office Space - West Floor ${floorNum}`,
          zone_type: "zone-west",
          floor: floorNum,
          area_m2: 190.0 + Math.random() * 40,
          neighbors: [`zone-east-f${floorNum}`, `zone-core-f${floorNum}`],
          occupancy_capacity: 40,
          hvac_zone: `HVAC-West-${floorNum}`,
          temperature: 22.0 + Math.random() * 1.5,
          humidity: 44 + Math.random() * 4,
          energy_kw: 12.0 + Math.random() * 3,
        },
        {
          id: `zone-core-f${floorNum}`,
          name: `Building Core Floor ${floorNum}`,
          zone_type: "zone-core",
          floor: floorNum,
          area_m2: 105.0 + Math.random() * 20,
          neighbors: [`zone-west-f${floorNum}`],
          occupancy_capacity: 0,
          hvac_zone: `HVAC-Core-${floorNum}`,
          temperature: 20.5 + Math.random() * 1.5,
          humidity: 45 + Math.random() * 5,
          energy_kw: 6.0 + Math.random() * 2,
        },
      ];
    }).flat(),
  ];

  const floors = [...new Set(zones.map((z) => z.floor))].sort();
  const filteredZones = zones.filter((z) => z.floor === selectedFloor);
  const totalArea = filteredZones.reduce((sum, z) => sum + z.area_m2, 0);
  const totalCapacity = filteredZones.reduce((sum, z) => sum + z.occupancy_capacity, 0);
  const totalEnergy = filteredZones.reduce((sum, z) => sum + (z.energy_kw || 0), 0);

  const zonesByType = {
    "zone-east": filteredZones.filter((z) => z.zone_type === "zone-east"),
    "zone-west": filteredZones.filter((z) => z.zone_type === "zone-west"),
    "zone-core": filteredZones.filter((z) => z.zone_type === "zone-core"),
  };

  if (loading) {
    return (
      <div className="building-info-container">
        <div className="loading">Loading zone information...</div>
      </div>
    );
  }

  return (
    <div className="building-info-container">
      <div className="zones-and-floors">
        <div className="overview-header">
          <h1>Zones & Floors</h1>
          <p className="subtitle">Building layout and thermal zones</p>
        </div>

        {/* Floor Selection */}
        <div className="floor-selector">
          {floors.map((floor) => (
            <button
              key={floor}
              className={`floor-btn ${selectedFloor === floor ? "active" : ""}`}
              onClick={() => setSelectedFloor(floor)}
            >
              Floor {floor}
            </button>
          ))}
        </div>

        {/* Floor Summary */}
        <div className="floor-summary">
          <div className="summary-item">
            <div className="summary-icon">📏</div>
            <div className="summary-info">
              <span className="summary-label">Total Floor Area</span>
              <span className="summary-value">{totalArea.toFixed(0)} m²</span>
            </div>
          </div>
          <div className="summary-item">
            <div className="summary-icon">👥</div>
            <div className="summary-info">
              <span className="summary-label">Total Capacity</span>
              <span className="summary-value">{totalCapacity} people</span>
            </div>
          </div>
          <div className="summary-item">
            <div className="summary-icon">🔢</div>
            <div className="summary-info">
              <span className="summary-label">Number of Zones</span>
              <span className="summary-value">{filteredZones.length}</span>
            </div>
          </div>
          <div className="summary-item">
            <div className="summary-icon">⚡</div>
            <div className="summary-info">
              <span className="summary-label">Total Energy</span>
              <span className="summary-value">{totalEnergy.toFixed(1)} kW</span>
            </div>
          </div>
        </div>

        {/* Zones Grid */}
        <div className="zones-grid">
          {filteredZones.map((zone) => (
            <div key={zone.id} className="zone-card">
              <div className="zone-header">
                <h3>{zone.name}</h3>
                <span className="zone-id">{zone.zone_type}</span>
              </div>

              <div className="zone-details">
                <div className="detail-row">
                  <span className="detail-label">Area:</span>
                  <span className="detail-value">{zone.area_m2.toFixed(1)} m²</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Capacity:</span>
                  <span className="detail-value">
                    {zone.occupancy_capacity === 0 ? "Common Area" : `${zone.occupancy_capacity} people`}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">HVAC Zone:</span>
                  <span className="detail-value">{zone.hvac_zone}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Energy Usage:</span>
                  <span className="detail-value">{(zone.energy_kw || 0).toFixed(1)} kW</span>
                </div>
              </div>

              <div className="zone-environment">
                <div className="env-item">
                  <span className="env-icon">🌡️</span>
                  <div className="env-info">
                    <span className="env-label">Temperature</span>
                    <span className="env-value">{zone.temperature}°C</span>
                  </div>
                </div>
                <div className="env-item">
                  <span className="env-icon">💧</span>
                  <div className="env-info">
                    <span className="env-label">Humidity</span>
                    <span className="env-value">{zone.humidity}%</span>
                  </div>
                </div>
              </div>

              {zone.neighbors.length > 0 && (
                <div className="zone-neighbors">
                  <span className="neighbors-label">Adjacent Zones:</span>
                  <div className="neighbors-list">
                    {zone.neighbors.map((neighbor) => (
                      <span key={neighbor} className="neighbor-badge">
                        {neighbor}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* All Zones Overview */}
        <div className="zones-overview">
          <h2>All Building Zones ({zones.length} Total)</h2>
          <div className="zones-table-container">
            <table className="zones-table">
              <thead>
                <tr>
                  <th>Zone Type</th>
                  <th>Name</th>
                  <th>Floor</th>
                  <th>Area (m²)</th>
                  <th>Capacity</th>
                  <th>HVAC Zone</th>
                  <th>Energy (kW)</th>
                  <th>Temp</th>
                  <th>Humidity</th>
                </tr>
              </thead>
              <tbody>
                {zones.map((zone) => (
                  <tr key={zone.id}>
                    <td className="zone-type-badge">{zone.zone_type}</td>
                    <td>{zone.name}</td>
                    <td>Floor {zone.floor}</td>
                    <td>{zone.area_m2.toFixed(1)}</td>
                    <td>{zone.occupancy_capacity === 0 ? "Common" : zone.occupancy_capacity}</td>
                    <td>{zone.hvac_zone}</td>
                    <td>{(zone.energy_kw || 0).toFixed(1)}</td>
                    <td>{zone.temperature}°C</td>
                    <td>{zone.humidity}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Zone Statistics by Type */}
        <div className="zone-statistics">
          <h2>Zone Type Statistics</h2>
          <div className="statistics-grid">
            {Object.entries(zonesByType).map(([zoneType, typeZones]) => {
              const typeArea = typeZones.reduce((sum, z) => sum + z.area_m2, 0);
              const typeEnergy = typeZones.reduce((sum, z) => sum + (z.energy_kw || 0), 0);
              const avgTemp = typeZones.length > 0 ? typeZones.reduce((sum, z) => sum + z.temperature, 0) / typeZones.length : 0;
              
              return (
                <div key={zoneType} className="stat-card">
                  <h3>{zoneType}</h3>
                  <div className="stat-items">
                    <div className="stat-item">
                      <span className="stat-label">Count:</span>
                      <span className="stat-value">{typeZones.length}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Total Area:</span>
                      <span className="stat-value">{typeArea.toFixed(0)} m²</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Total Energy:</span>
                      <span className="stat-value">{typeEnergy.toFixed(1)} kW</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Avg Temp:</span>
                      <span className="stat-value">{avgTemp.toFixed(1)}°C</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ZonesAndFloors;
