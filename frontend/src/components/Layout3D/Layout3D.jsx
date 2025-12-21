import React, { useState, useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera, Grid, Stats } from "@react-three/drei";
import Building3D from "./Building3D";
import Controls3D from "./Controls3D";
import { fetchLatestMetrics } from "../../services/api";

function Layout3D({ layout, buildingId = "demo-building" }) {
  const [selectedMetric, setSelectedMetric] = useState("energy");
  const [selectedZone, setSelectedZone] = useState(null);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(true);

  // Fetch latest metrics for all zones
  useEffect(() => {
    async function loadMetrics() {
      if (!buildingId || !layout?.zones) return;

      try {
        setLoading(true);
        const data = await fetchLatestMetrics(buildingId);
        
        // Transform metrics data to zone-based structure
        const zoneMetrics = {};
        
        // Create a mapping from API zone IDs to layout zone IDs
        // API might return "zone-1", "zone-2" or "z1", "z2", etc.
        const zoneIdMap = {};
        layout.zones.forEach((zone, index) => {
          // Try multiple possible zone ID formats
          zoneIdMap[zone.id] = zone.id; // Direct match
          zoneIdMap[`zone-${index + 1}`] = zone.id; // zone-1, zone-2, etc.
          zoneIdMap[`z${index + 1}`] = zone.id; // z1, z2, etc.
        });
        
        if (data.latest_values) {
          Object.entries(data.latest_values).forEach(([apiZoneId, zoneData]) => {
            // Find matching layout zone ID
            const layoutZoneId = zoneIdMap[apiZoneId] || apiZoneId;
            
            zoneMetrics[layoutZoneId] = {
              energy: zoneData.energy ?? null,
              temperature: zoneData.temperature ?? null,
              occupancy: zoneData.occupancy ?? null,
            };
          });
        }
        
        // Fill in missing zones with default values
        layout.zones.forEach((zone) => {
          if (!zoneMetrics[zone.id]) {
            zoneMetrics[zone.id] = {
              energy: 100 + Math.random() * 50,
              temperature: 20 + Math.random() * 5,
              occupancy: 0.3 + Math.random() * 0.4,
            };
          }
        });
        
        setMetrics(zoneMetrics);
      } catch (error) {
        console.error("Failed to load metrics:", error);
        // Always set default metrics for demo
        const defaultMetrics = {};
        layout.zones.forEach((zone) => {
          defaultMetrics[zone.id] = {
            energy: 100 + Math.random() * 50,
            temperature: 20 + Math.random() * 5,
            occupancy: 0.3 + Math.random() * 0.4,
          };
        });
        setMetrics(defaultMetrics);
      } finally {
        setLoading(false);
      }
    }

    if (layout?.zones) {
      loadMetrics();
      
      // Refresh metrics every 30 seconds
      const interval = setInterval(loadMetrics, 30000);
      return () => clearInterval(interval);
    }
  }, [buildingId, layout]);

  if (!layout || !layout.zones) {
    return <div className="layout-3d loading">Loading layout...</div>;
  }

  const handleZoneClick = (zone) => {
    setSelectedZone(selectedZone?.id === zone.id ? null : zone);
  };

  const handleCloseZoneDetails = () => {
    setSelectedZone(null);
  };

  return (
    <div className="layout-3d-container">
      <div className="layout-3d-canvas">
        <Canvas
          camera={{ position: [15, 15, 15], fov: 50 }}
          shadows
          gl={{ antialias: true }}
        >
          {/* Lighting */}
          <ambientLight intensity={0.5} />
          <directionalLight
            position={[10, 10, 5]}
            intensity={1}
            castShadow
            shadow-mapSize-width={2048}
            shadow-mapSize-height={2048}
          />
          <pointLight position={[-10, -10, -10]} intensity={0.5} />

          {/* Camera controls */}
          <OrbitControls
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            minDistance={5}
            maxDistance={50}
          />

          {/* Grid floor */}
          <Grid
            args={[20, 20]}
            cellColor="#6f6f6f"
            sectionColor="#9d4b4b"
            cellThickness={0.5}
            sectionThickness={1}
            fadeDistance={25}
            fadeStrength={1}
          />

          {/* Building 3D structure */}
          <Building3D
            layout={layout}
            metrics={metrics}
            selectedMetric={selectedMetric}
            onZoneClick={handleZoneClick}
            selectedZone={selectedZone}
          />

          {/* Performance stats (optional, can be removed in production) */}
          <Stats />
        </Canvas>
      </div>

      {/* Controls panel */}
      <Controls3D
        selectedMetric={selectedMetric}
        onMetricChange={setSelectedMetric}
        selectedZone={selectedZone}
        onCloseZoneDetails={handleCloseZoneDetails}
      />

      {/* Zone info sidebar */}
      <div className="layout-info-sidebar">
        <h3>Building Information</h3>
        <p><strong>Building ID:</strong> {layout.building_id}</p>
        <p><strong>Total Zones:</strong> {layout.zones.length}</p>
        <p><strong>Floors:</strong> {Math.max(...layout.zones.map((z) => z.floor))}</p>
        
        {loading && <p className="muted">Loading metrics...</p>}
        
        <div className="zones-list">
          <h4>Zones</h4>
          <ul>
            {layout.zones.map((zone) => (
              <li
                key={zone.id}
                className={selectedZone?.id === zone.id ? "selected" : ""}
                onClick={() => handleZoneClick(zone)}
                style={{ cursor: "pointer" }}
              >
                <strong>{zone.name}</strong>
                <br />
                Floor {zone.floor} · {zone.area_m2.toFixed(1)} m²
                {metrics[zone.id] ? (
                  <div className="zone-metrics">
                    <span>Energy: {metrics[zone.id].energy != null ? metrics[zone.id].energy.toFixed(1) : "N/A"} kWh</span>
                    <span>Temp: {metrics[zone.id].temperature != null ? metrics[zone.id].temperature.toFixed(1) : "N/A"}°C</span>
                    <span>Occ: {metrics[zone.id].occupancy != null ? (metrics[zone.id].occupancy * 100).toFixed(0) : "N/A"}%</span>
                  </div>
                ) : (
                  <div className="zone-metrics">
                    <span className="muted">No metrics available</span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Layout3D;
