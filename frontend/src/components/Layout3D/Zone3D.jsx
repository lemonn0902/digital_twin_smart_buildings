import React, { useRef, useState, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { Box, Text } from "@react-three/drei";
import * as THREE from "three";

function Zone3D({ zone, position, metrics, selectedMetric, onClick, isSelected }) {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);

  // Calculate zone size based on area (scale to reasonable 3D size)
  const baseSize = Math.sqrt(zone.area_m2) * 0.1; // Scale factor
  const width = baseSize;
  const height = 0.5; // Fixed height for zones
  const depth = baseSize;

  // Get color based on selected metric - use useMemo to recalculate when metric changes
  const colorHex = useMemo(() => {
    if (!metrics || !selectedMetric) {
      return "#888888"; // Default gray
    }

    const value = metrics[selectedMetric];
    if (value === undefined || value === null) {
      return "#888888";
    }

    const color = new THREE.Color();

    // Color mapping based on metric type
    if (selectedMetric === "energy") {
      // Energy: blue scale (low = light blue, high = dark blue)
      const normalized = Math.min(value / 200, 1); // Assuming max energy ~200 kWh
      color.lerpColors(
        new THREE.Color(0x87ceeb), // Light blue
        new THREE.Color(0x00008b), // Dark blue
        normalized
      );
    } else if (selectedMetric === "temperature") {
      // Temperature: red-yellow-blue scale
      const normalized = Math.min(Math.max((value - 15) / 15, 0), 1); // 15-30°C range
      if (normalized < 0.5) {
        color.lerpColors(
          new THREE.Color(0x0000ff), // Blue (cold)
          new THREE.Color(0xffff00), // Yellow (warm)
          normalized * 2
        );
      } else {
        color.lerpColors(
          new THREE.Color(0xffff00), // Yellow
          new THREE.Color(0xff0000), // Red (hot)
          (normalized - 0.5) * 2
        );
      }
    } else if (selectedMetric === "occupancy") {
      // Occupancy: green scale (low = light green, high = dark green)
      const normalized = Math.min(value, 1); // Occupancy is 0-1
      color.lerpColors(
        new THREE.Color(0x90ee90), // Light green
        new THREE.Color(0x006400), // Dark green
        normalized
      );
    } else {
      color.set("#888888");
    }

    return "#" + color.getHexString();
  }, [metrics, selectedMetric]);

  // Animate on hover
  useFrame(() => {
    if (meshRef.current) {
      if (hovered || isSelected) {
        meshRef.current.scale.lerp(new THREE.Vector3(1.1, 1.1, 1.1), 0.1);
      } else {
        meshRef.current.scale.lerp(new THREE.Vector3(1, 1, 1), 0.1);
      }
    }
  });

  return (
    <group position={position} ref={meshRef}>
      <Box
        args={[width, height, depth]}
        position={[0, height / 2, 0]}
        onClick={onClick}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={colorHex}
          opacity={hovered || isSelected ? 0.9 : 0.7}
          transparent
          emissive={hovered || isSelected ? colorHex : "#000000"}
          emissiveIntensity={hovered || isSelected ? 0.3 : 0}
        />
      </Box>
      
      {/* Zone label */}
      {(hovered || isSelected) && (
        <Text
          position={[0, height + 0.5, 0]}
          fontSize={0.3}
          color="white"
          anchorX="center"
          anchorY="middle"
        >
          {zone.name}
        </Text>
      )}
    </group>
  );
}

export default Zone3D;
