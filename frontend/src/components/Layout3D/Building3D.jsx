import React, { useMemo } from "react";
import { useThree } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import * as THREE from "three";
import Zone3D from "./Zone3D";

function Building3D({ layout, metrics, selectedMetric, onZoneClick, selectedZone }) {
  const { viewport } = useThree();

  // Calculate positions for zones based on floor and area
  const zonePositions = useMemo(() => {
    const positions = {};
    const floorSpacing = 3; // Vertical spacing between floors
    const gridSize = Math.ceil(Math.sqrt(layout.zones.length));
    const spacing = 5; // Horizontal spacing between zones

    layout.zones.forEach((zone, index) => {
      // Simple grid layout for now (can be improved with actual spatial data)
      const row = Math.floor(index / gridSize);
      const col = index % gridSize;
      
      const x = (col - gridSize / 2) * spacing;
      const y = zone.floor * floorSpacing;
      const z = (row - gridSize / 2) * spacing;

      positions[zone.id] = [x, y, z];
    });

    return positions;
  }, [layout.zones]);

  // Create connections between zones
  const connections = useMemo(() => {
    const lines = [];
    const zoneMap = new Map(layout.zones.map((z) => [z.id, z]));

    layout.zones.forEach((zone) => {
      zone.neighbors.forEach((neighborId) => {
        const neighbor = zoneMap.get(neighborId);
        if (neighbor && zonePositions[zone.id] && zonePositions[neighborId]) {
          const start = new THREE.Vector3(...zonePositions[zone.id]);
          const end = new THREE.Vector3(...zonePositions[neighborId]);
          
          // Adjust to zone center height
          start.y += 0.25;
          end.y += 0.25;

          lines.push(
            <Line
              key={`${zone.id}-${neighborId}`}
              points={[start, end]}
              color="#888888"
              lineWidth={1}
              dashed={false}
            />
          );
        }
      });
    });

    return lines;
  }, [layout.zones, zonePositions]);

  return (
    <>
      {/* Render zones */}
      {layout.zones.map((zone) => (
        <Zone3D
          key={`${zone.id}-${selectedMetric}`}
          zone={zone}
          position={zonePositions[zone.id]}
          metrics={metrics?.[zone.id]}
          selectedMetric={selectedMetric}
          onClick={() => onZoneClick?.(zone)}
          isSelected={selectedZone?.id === zone.id}
        />
      ))}

      {/* Render connections */}
      {connections}
    </>
  );
}

export default Building3D;
