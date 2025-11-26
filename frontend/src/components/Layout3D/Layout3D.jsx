import React from "react";

function Layout3D({ layout }) {
  if (!layout || !layout.zones) {
    return <div className="layout-3d loading">Loading layout...</div>;
  }

  return (
    <div className="layout-3d">
      <h2>Building Layout</h2>
      <div className="layout-info">
        <p><strong>Building ID:</strong> {layout.building_id}</p>
        <p><strong>Total Zones:</strong> {layout.zones.length}</p>
      </div>
      
      <div className="zones-graph">
        {layout.zones.map((zone) => (
          <div key={zone.id} className="zone-node" style={{ 
            width: `${Math.sqrt(zone.area_m2) * 2}px`,
            height: `${Math.sqrt(zone.area_m2) * 2}px`,
          }}>
            <div className="zone-label">{zone.name}</div>
            <div className="zone-details">
              <div>{zone.area_m2.toFixed(0)} m²</div>
              <div>Floor {zone.floor}</div>
            </div>
            <div className="zone-connections">
              {zone.neighbors.map((neighborId) => (
                <div key={neighborId} className="connection-line" />
              ))}
            </div>
          </div>
        ))}
      </div>
      
      <div className="zones-list">
        <h3>Zones</h3>
        <ul>
          {layout.zones.map((zone) => (
            <li key={zone.id}>
              <strong>{zone.name}</strong> (Floor {zone.floor}) — {zone.area_m2.toFixed(1)} m²
              {zone.neighbors.length > 0 && (
                <span className="neighbors">
                  {" "}↔ {zone.neighbors.join(", ")}
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default Layout3D;
