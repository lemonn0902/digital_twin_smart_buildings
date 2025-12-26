import React, { useRef, useState, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { Box, Text, Cylinder, Octahedron } from "@react-three/drei";
import * as THREE from "three";

// Floating element component for office zones
function FloatingElement({ index, baseSize, height, materialProps }) {
  const meshRef = useRef();
  const animationRef = useRef({ time: 0 });
  
  useFrame((state, delta) => {
    animationRef.current.time += delta;
    if (meshRef.current) {
      const angle = (index * Math.PI * 2) / 3;
      const radius = baseSize * 0.6;
      const time = animationRef.current.time;
      meshRef.current.position.x = Math.cos(angle + time) * radius;
      meshRef.current.position.y = height * 0.7 + Math.sin(time * 2 + index) * 0.2;
      meshRef.current.position.z = Math.sin(angle + time) * radius;
      meshRef.current.rotation.y += delta * 2;
    }
  });
  
  return (
    <Box
      ref={meshRef}
      args={[0.15, 0.15, 0.15]}
      position={[0, height * 0.7, 0]}
    >
      <meshStandardMaterial
        {...materialProps}
        opacity={0.5}
        emissiveIntensity={0.8}
      />
    </Box>
  );
}

function Zone3D({ zone, position, metrics, selectedMetric, onClick, isSelected }) {
  const meshRef = useRef();
  const animationRef = useRef({ time: 0 });
  const [hovered, setHovered] = useState(false);

  // Calculate zone size based on area (scale to reasonable 3D size)
  const baseSize = Math.sqrt(zone.area_m2) * 0.1; // Scale factor
  const width = baseSize;
  const height = 0.5; // Fixed height for zones
  const depth = baseSize;
  
  // Determine zone type from name
  const zoneType = useMemo(() => {
    const name = zone.name.toLowerCase();
    if (name.includes("corridor")) return "corridor";
    if (name.includes("meeting")) return "meeting";
    if (name.includes("office")) return "office";
    return "default";
  }, [zone.name]);

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

  // Animate based on zone type
  useFrame((state, delta) => {
    animationRef.current.time += delta;
    
    if (meshRef.current) {
      if (hovered || isSelected) {
        meshRef.current.scale.lerp(new THREE.Vector3(1.1, 1.1, 1.1), 0.1);
      } else {
        meshRef.current.scale.lerp(new THREE.Vector3(1, 1, 1), 0.1);
      }
      
      // Zone-specific animations
      if (zoneType === "corridor") {
        // Pulsing animation for corridor
        const pulse = Math.sin(animationRef.current.time * 2) * 0.05 + 1;
        meshRef.current.scale.y = (hovered || isSelected ? 1.1 : 1) * pulse;
      } else if (zoneType === "meeting") {
        // Gentle rotation for meeting room
        meshRef.current.rotation.y = Math.sin(animationRef.current.time * 0.5) * 0.1;
      } else if (zoneType === "office") {
        // Subtle floating animation for office
        meshRef.current.position.y = position[1] + Math.sin(animationRef.current.time * 1.5) * 0.1;
      }
    }
  });

  // Render different shapes based on zone type
  const renderZoneShape = () => {
    const materialProps = {
      color: colorHex,
      opacity: hovered || isSelected ? 0.9 : 0.7,
      transparent: true,
      emissive: hovered || isSelected ? colorHex : "#000000",
      emissiveIntensity: hovered || isSelected ? 0.3 : 0,
    };

    if (zoneType === "corridor") {
      // Corridor: Long tunnel-like shape with animated inner elements
      return (
        <>
          <Box
            args={[width * 1.5, height * 0.8, depth * 0.6]}
            position={[0, height / 2, 0]}
            onClick={onClick}
            onPointerOver={(e) => {
              e.stopPropagation();
              setHovered(true);
            }}
            onPointerOut={() => setHovered(false)}
          >
            <meshStandardMaterial {...materialProps} />
          </Box>
          {/* Animated inner corridor elements */}
          {[...Array(3)].map((_, i) => (
            <Box
              key={i}
              args={[width * 0.3, height * 0.4, depth * 0.3]}
              position={[
                (i - 1) * width * 0.4,
                height * 0.3,
                0
              ]}
            >
              <meshStandardMaterial
                {...materialProps}
                opacity={0.4}
                emissiveIntensity={0.5}
              />
            </Box>
          ))}
        </>
      );
    } else if (zoneType === "meeting") {
      // Meeting Room: Octagonal shape with corner pillars
      return (
        <>
          <Octahedron
            args={[baseSize * 0.7, 0]}
            position={[0, height / 2, 0]}
            onClick={onClick}
            onPointerOver={(e) => {
              e.stopPropagation();
              setHovered(true);
            }}
            onPointerOut={() => setHovered(false)}
          >
            <meshStandardMaterial {...materialProps} />
          </Octahedron>
          {/* Corner pillars */}
          {[...Array(4)].map((_, i) => {
            const angle = (i * Math.PI * 2) / 4;
            const radius = baseSize * 0.5;
            return (
              <Cylinder
                key={i}
                args={[0.08, 0.08, height * 0.6]}
                position={[
                  Math.cos(angle) * radius,
                  height * 0.3,
                  Math.sin(angle) * radius
                ]}
              >
                <meshStandardMaterial
                  {...materialProps}
                  opacity={0.5}
                />
              </Cylinder>
            );
          })}
        </>
      );
    } else if (zoneType === "office") {
      // Open Office: Multi-level structure with floating elements
      return (
        <>
          {/* Base structure */}
          <Box
            args={[width, height * 0.6, depth]}
            position={[0, height * 0.3, 0]}
            onClick={onClick}
            onPointerOver={(e) => {
              e.stopPropagation();
              setHovered(true);
            }}
            onPointerOut={() => setHovered(false)}
          >
            <meshStandardMaterial {...materialProps} />
          </Box>
          {/* Upper level sections */}
          {[...Array(2)].map((_, i) => (
            <Box
              key={i}
              args={[width * 0.4, height * 0.3, depth * 0.4]}
              position={[
                (i - 0.5) * width * 0.5,
                height * 0.85,
                (i % 2 === 0 ? -1 : 1) * depth * 0.2
              ]}
            >
              <meshStandardMaterial
                {...materialProps}
                opacity={0.6}
              />
            </Box>
          ))}
          {/* Floating decorative elements */}
          {[...Array(3)].map((_, i) => (
            <FloatingElement
              key={i}
              index={i}
              baseSize={baseSize}
              height={height}
              materialProps={materialProps}
            />
          ))}
        </>
      );
    } else {
      // Default: Simple box
      return (
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
          <meshStandardMaterial {...materialProps} />
        </Box>
      );
    }
  };

  return (
    <group position={position} ref={meshRef}>
      {renderZoneShape()}
      
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
