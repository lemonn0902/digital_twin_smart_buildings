import React, { useRef, useState, useEffect } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Text, Grid, Line } from "@react-three/drei";
import * as THREE from "three";
import { fetchLatestMetrics } from "../../services/api";

const BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "/api";

// Helper function to fetch historical data
async function fetchHistoricalData(buildingId, zoneId, metrics, hours) {
  const endTime = new Date();
  const startTime = new Date(endTime.getTime() - hours * 60 * 60 * 1000);
  
  const response = await fetch(`${BASE}/historical/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      building_id: buildingId,
      zone_id: zoneId,
      metrics: metrics,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      resolution_minutes: hours <= 24 ? 15 : hours <= 168 ? 60 : 240, // 15min for 24h, 1h for 7d, 4h for 30d
    }),
  });
  
  if (!response.ok) throw new Error("Failed to fetch historical data");
  return response.json();
}

// Sparkline component for trend visualization
function Sparkline({ data, width = 120, height = 35, color = "#00ffff", metric = "energy" }) {
  if (!data || data.length === 0) return null;

  // Extract values for the metric
  const values = data.map(d => {
    if (typeof d === 'object' && d !== null) {
      return d[metric] || d.value;
    }
    return null;
  }).filter(v => v != null);

  if (values.length === 0) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values.map((value, index) => {
    const x = (index / (values.length - 1 || 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(" ");

  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        opacity="0.8"
      />
      {values.length > 0 && (
        <circle
          cx={((values.length - 1) / (values.length - 1 || 1)) * width}
          cy={height - ((values[values.length - 1] - min) / range) * height}
          r="2"
          fill={color}
        />
      )}
    </svg>
  );
}

// Time playback controls component
function TimePlaybackControls({ onTimeChange, isPlaying, onPlayPause, currentTime, duration }) {
  const formatTime = (ms) => {
    const hours = Math.floor(ms / (1000 * 60 * 60));
    const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  };

  return (
    <div className="time-playback-controls">
      <button onClick={onPlayPause} className="play-pause-button">
        {isPlaying ? "⏸" : "▶"}
      </button>
      <input
        type="range"
        min="0"
        max={duration}
        value={currentTime}
        onChange={(e) => onTimeChange(parseInt(e.target.value))}
        className="time-slider"
      />
      <span className="time-display">
        {formatTime(currentTime)} / {formatTime(duration)}
      </span>
    </div>
  );
}

// Anomaly indicator component
function AnomalyIndicator({ position, size, severity = "red" }) {
  const indicatorRef = useRef();
  const color = severity === "red" ? "#ff0000" : "#ffaa00";
  const label = severity === "red" ? "CRITICAL" : "WARNING";

  useFrame((state) => {
    if (indicatorRef.current) {
      // Pulsing glow for anomalies
      const pulseSpeed = severity === "red" ? 5 : 4;
      const pulse = Math.sin(state.clock.elapsedTime * pulseSpeed) * 0.3 + 0.7;
      indicatorRef.current.material.emissiveIntensity = pulse;
      // Rotate slowly
      indicatorRef.current.rotation.y += 0.01;
    }
  });

  return (
    <group position={position}>
      {/* Warning icon/sphere */}
      <mesh ref={indicatorRef} position={[0, size[1] + 0.8, 0]}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.8}
        />
      </mesh>
      {/* Warning text */}
      <Text
        position={[0, size[1] + 1.3, 0]}
        fontSize={0.3}
        color={color}
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.02}
        outlineColor="#000000"
      >
        {label}
      </Text>
    </group>
  );
}

// Room component with glowing edges
function Room({ position, size, color, name, opacity = 0.3, glowIntensity = 1, isSelected = false, hasAnomaly = false, anomalySeverity = "green", thresholdBreaches = [] }) {
  const meshRef = useRef();
  const edgesRef = useRef();

  // Enhanced glow and opacity when selected or has anomaly
  const selectedGlowIntensity = isSelected ? glowIntensity * 3 : (hasAnomaly ? glowIntensity * 2.5 : glowIntensity);
  const selectedOpacity = isSelected ? Math.min(opacity * 1.5, 0.7) : (hasAnomaly ? Math.min(opacity * 1.3, 0.6) : opacity);
  // Color based on anomaly severity or selection
  const selectedColor = hasAnomaly 
    ? (anomalySeverity === "red" ? "#ff0000" : "#ffaa00") 
    : (isSelected ? "#ffff00" : color);

  useFrame((state) => {
    if (edgesRef.current) {
      // Enhanced pulsing animation when selected or has anomaly
      const pulseSpeed = (isSelected || hasAnomaly) ? 4 : 2;
      const pulseAmplitude = (isSelected || hasAnomaly) ? 0.3 : 0.1;
      const pulse = Math.sin(state.clock.elapsedTime * pulseSpeed) * pulseAmplitude + 1;
      edgesRef.current.material.emissiveIntensity = selectedGlowIntensity * pulse;
    }
  });

  return (
    <group position={position}>
      {/* Room box with transparent material */}
      <mesh ref={meshRef} position={[0, size[1] / 2, 0]}>
        <boxGeometry args={size} />
        <meshStandardMaterial
          color={selectedColor}
          transparent
          opacity={selectedOpacity}
          emissive={selectedColor}
          emissiveIntensity={isSelected ? 0.5 : 0.2}
        />
      </mesh>

      {/* Glowing edges - enhanced when selected */}
      <lineSegments ref={edgesRef}>
        <edgesGeometry args={[new THREE.BoxGeometry(...size)]} />
        <lineBasicMaterial
          color={selectedColor}
          emissive={selectedColor}
          emissiveIntensity={selectedGlowIntensity}
        />
      </lineSegments>

      {/* Highlight overlay when selected */}
      {isSelected && (
        <mesh position={[0, size[1] / 2, 0]}>
          <boxGeometry args={size.map((s, i) => (i === 1 ? s + 0.1 : s + 0.05))} />
          <meshStandardMaterial
            color="#ffff00"
            transparent
            opacity={0.2}
            emissive="#ffff00"
            emissiveIntensity={0.3}
          />
        </mesh>
      )}

      {/* Anomaly overlay - severity-based pulsing glow */}
      {hasAnomaly && (
        <mesh position={[0, size[1] / 2, 0]}>
          <boxGeometry args={size.map((s, i) => (i === 1 ? s + 0.15 : s + 0.1))} />
          <meshStandardMaterial
            color={anomalySeverity === "red" ? "#ff0000" : "#ffaa00"}
            transparent
            opacity={anomalySeverity === "red" ? 0.4 : 0.25}
            emissive={anomalySeverity === "red" ? "#ff0000" : "#ffaa00"}
            emissiveIntensity={anomalySeverity === "red" ? 0.6 : 0.4}
          />
        </mesh>
      )}

      {/* Threshold breach indicators - small warning icons for each breach */}
      {thresholdBreaches.map((breach, idx) => {
        const angle = (idx / thresholdBreaches.length) * Math.PI * 2;
        const radius = Math.max(size[0], size[2]) / 2 + 0.5;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;
        return (
          <mesh key={idx} position={[x, size[1] + 0.3, z]}>
            <sphereGeometry args={[0.15, 8, 8]} />
            <meshStandardMaterial
              color={breach.type === "high" || breach.type === "low" || breach.type === "invalid" ? "#ff0000" : "#ffaa00"}
              emissive={breach.type === "high" || breach.type === "low" || breach.type === "invalid" ? "#ff0000" : "#ffaa00"}
              emissiveIntensity={0.8}
            />
          </mesh>
        );
      })}

      {/* Anomaly indicator */}
      {hasAnomaly && (
        <AnomalyIndicator position={position} size={size} severity={anomalySeverity} />
      )}

      {/* Room label */}
      <Text
        position={[0, size[1] + 0.5, 0]}
        fontSize={isSelected || hasAnomaly ? 0.5 : 0.4}
        color={selectedColor}
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.02}
        outlineColor="#000000"
      >
        {name}
      </Text>
    </group>
  );
}

// Conference table with chairs
function ConferenceTable({ position }) {
  return (
    <group position={position}>
      {/* Table */}
      <mesh position={[0, 0.4, 0]}>
        <boxGeometry args={[2, 0.1, 1.2]} />
        <meshStandardMaterial
          color="#4a5568"
          emissive="#2d3748"
          emissiveIntensity={0.3}
        />
      </mesh>
      {/* Table legs */}
      {[
        [-0.9, 0.2, -0.5],
        [0.9, 0.2, -0.5],
        [-0.9, 0.2, 0.5],
        [0.9, 0.2, 0.5],
      ].map((pos, i) => (
        <mesh key={i} position={pos}>
          <boxGeometry args={[0.1, 0.4, 0.1]} />
          <meshStandardMaterial color="#2d3748" />
        </mesh>
      ))}
      {/* Chairs around table */}
      {[
        [0, 0.25, -0.8],
        [0, 0.25, 0.8],
        [-1.1, 0.25, 0],
        [1.1, 0.25, 0],
      ].map((pos, i) => (
        <mesh key={i} position={pos}>
          <boxGeometry args={[0.3, 0.5, 0.3]} />
          <meshStandardMaterial
            color="#3a4556"
            emissive="#00ffff"
            emissiveIntensity={0.1}
          />
        </mesh>
      ))}
    </group>
  );
}

// Desk/workstation
function Desk({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.35, 0]}>
        <boxGeometry args={[0.8, 0.1, 0.6]} />
        <meshStandardMaterial
          color="#4a5568"
          emissive="#0088ff"
          emissiveIntensity={0.2}
        />
      </mesh>
      <mesh position={[0, 0.2, 0]}>
        <boxGeometry args={[0.8, 0.4, 0.05]} />
        <meshStandardMaterial
          color="#2d3748"
          emissive="#00ffff"
          emissiveIntensity={0.1}
        />
      </mesh>
    </group>
  );
}

// Server rack
function ServerRack({ position }) {
  const rackRef = useRef();

  useFrame((state) => {
    if (rackRef.current) {
      // Subtle blinking lights on servers
      const blink = Math.sin(state.clock.elapsedTime * 3 + position[0]) > 0;
      rackRef.current.children.forEach((child, i) => {
        if (child.material) {
          child.material.emissiveIntensity = blink ? 0.5 : 0.1;
        }
      });
    }
  });

  return (
    <group ref={rackRef} position={position}>
      {/* Server rack frame */}
      <mesh position={[0, 0.6, 0]}>
        <boxGeometry args={[0.4, 1.2, 0.3]} />
        <meshStandardMaterial
          color="#1a1a1a"
          emissive="#00ff88"
          emissiveIntensity={0.2}
        />
      </mesh>
      {/* Server units */}
      {[0, 0.3, 0.6, 0.9].map((y, i) => (
        <mesh key={i} position={[0, y, 0]}>
          <boxGeometry args={[0.35, 0.25, 0.28]} />
          <meshStandardMaterial
            color="#2d2d2d"
            emissive="#00ff88"
            emissiveIntensity={0.1}
          />
        </mesh>
      ))}
    </group>
  );
}

// Executive desk
function ExecutiveDesk({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.4, 0]}>
        <boxGeometry args={[1.5, 0.1, 0.8]} />
        <meshStandardMaterial
          color="#3a3a3a"
          emissive="#0088ff"
          emissiveIntensity={0.3}
        />
      </mesh>
      <mesh position={[0, 0.2, 0]}>
        <boxGeometry args={[1.5, 0.4, 0.05]} />
        <meshStandardMaterial
          color="#2d2d2d"
          emissive="#00ffff"
          emissiveIntensity={0.15}
        />
      </mesh>
      {/* Chair */}
      <mesh position={[0, 0.3, -0.6]}>
        <boxGeometry args={[0.5, 0.6, 0.5]} />
        <meshStandardMaterial
          color="#4a4a4a"
          emissive="#00ffff"
          emissiveIntensity={0.1}
        />
      </mesh>
    </group>
  );
}

// Floor component
function Floor({ floorNumber, isHighlighted, isDimmed, selectedZone, anomalies = {} }) {
  const floorHeight = 3;
  const buildingWidth = 16;
  const buildingDepth = 14;
  const yPosition = (floorNumber - 1) * floorHeight;

  const floorOpacity = isDimmed ? 0.15 : isHighlighted ? 0.4 : 0.3;
  const glowIntensity = isHighlighted ? 2 : isDimmed ? 0.3 : 1;

  // Map zone IDs to room names
  const zoneNameMap = {
    "meeting-room": "Meeting Room",
    "corridor": "Corridor",
    "open-office": "Open Office",
    "private-office": "Private Office",
    "server-room": "Server Room",
  };

  // Floor 1 rooms
  const floor1Rooms = [
    {
      zoneId: "meeting-room",
      name: "Meeting Room",
      position: [-4, 0, -3],
      size: [4, floorHeight - 0.2, 3],
      color: "#00ffff",
    },
    {
      zoneId: "corridor",
      name: "Corridor",
      position: [0, 0, 0],
      size: [6, floorHeight - 0.2, 2],
      color: "#0088ff",
    },
    {
      zoneId: "open-office",
      name: "Open Office",
      position: [5, 0, 0],
      size: [6, floorHeight - 0.2, 6],
      color: "#00ff88",
    },
  ];

  // Floor 2 rooms
  const floor2Rooms = [
    {
      zoneId: "private-office",
      name: "Private Office",
      position: [-4, 0, 0],
      size: [5, floorHeight - 0.2, 5],
      color: "#00ffff",
    },
    {
      zoneId: "server-room",
      name: "Server Room",
      position: [5, 0, 0],
      size: [5, floorHeight - 0.2, 5],
      color: "#00ff88",
    },
  ];

  const rooms = floorNumber === 1 ? floor1Rooms : floor2Rooms;

  return (
    <group position={[0, yPosition, 0]}>
      {/* Floor slab with grid pattern */}
      <mesh position={[0, -floorHeight / 2 + 0.1, 0]} receiveShadow>
        <boxGeometry args={[buildingWidth, 0.2, buildingDepth]} />
        <meshStandardMaterial
          color="#1a1a2e"
          transparent
          opacity={floorOpacity * 0.5}
          emissive="#00ffff"
          emissiveIntensity={0.1}
        />
      </mesh>

      {/* Grid pattern on floor */}
      <Grid
        args={[buildingWidth, buildingDepth]}
        cellColor="#00ffff"
        sectionColor="#0088ff"
        cellThickness={0.5}
        sectionThickness={1}
        fadeDistance={20}
        fadeStrength={1}
        position={[0, -floorHeight / 2 + 0.11, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      />

      {/* Outer walls with glowing edges */}
      {[
        { pos: [0, 0, buildingDepth / 2], size: [buildingWidth, floorHeight, 0.1] },
        { pos: [0, 0, -buildingDepth / 2], size: [buildingWidth, floorHeight, 0.1] },
        { pos: [-buildingWidth / 2, 0, 0], size: [0.1, floorHeight, buildingDepth] },
        { pos: [buildingWidth / 2, 0, 0], size: [0.1, floorHeight, buildingDepth] },
      ].map((wall, i) => (
        <group key={i} position={wall.pos}>
          <mesh>
            <boxGeometry args={wall.size} />
            <meshStandardMaterial
              color="#1a1a2e"
              transparent
              opacity={floorOpacity * 0.6}
              emissive="#00ffff"
              emissiveIntensity={0.2}
            />
          </mesh>
          <lineSegments>
            <edgesGeometry args={[new THREE.BoxGeometry(...wall.size)]} />
            <lineBasicMaterial
              color="#00ffff"
              emissive="#00ffff"
              emissiveIntensity={glowIntensity}
            />
          </lineSegments>
        </group>
      ))}

      {/* Rooms */}
      {rooms.map((room, i) => {
        const isSelected = selectedZone?.id === room.zoneId;
        const zoneAnomaly = anomalies[room.zoneId];
        const hasAnomaly = zoneAnomaly?.hasAnomaly || false;
        const anomalySeverity = zoneAnomaly?.severity || "green";
        const thresholdBreaches = zoneAnomaly?.thresholdBreaches || [];
        return (
          <Room
            key={i}
            position={room.position}
            size={room.size}
            color={room.color}
            name={room.name}
            opacity={floorOpacity}
            glowIntensity={glowIntensity}
            isSelected={isSelected}
            hasAnomaly={hasAnomaly}
            anomalySeverity={anomalySeverity}
            thresholdBreaches={thresholdBreaches}
          />
        );
      })}

      {/* Floor 1 furniture */}
      {floorNumber === 1 && (
        <>
          {/* Meeting Room furniture */}
          <ConferenceTable position={[-4, 0, -3]} />
          {/* Open Office desks */}
          {[
            [3, 0, -2],
            [5, 0, -2],
            [7, 0, -2],
            [3, 0, 2],
            [5, 0, 2],
            [7, 0, 2],
          ].map((pos, i) => (
            <Desk key={i} position={pos} />
          ))}
        </>
      )}

      {/* Floor 2 furniture */}
      {floorNumber === 2 && (
        <>
          {/* Private Office furniture */}
          <ExecutiveDesk position={[-4, 0, 0]} />
          {/* Server Room racks */}
          {[
            [3.5, 0, -1.5],
            [4.5, 0, -1.5],
            [3.5, 0, 1.5],
            [4.5, 0, 1.5],
          ].map((pos, i) => (
            <ServerRack key={i} position={pos} />
          ))}
        </>
      )}

      {/* Ceiling */}
      <mesh position={[0, floorHeight / 2 - 0.1, 0]}>
        <boxGeometry args={[buildingWidth, 0.2, buildingDepth]} />
        <meshStandardMaterial
          color="#1a1a2e"
          transparent
          opacity={floorOpacity * 0.4}
          emissive="#00ffff"
          emissiveIntensity={0.1}
        />
      </mesh>
    </group>
  );
}

// Floor separator plane (between floors)
function FloorSeparator({ yPosition, buildingWidth, buildingDepth }) {
  return (
    <group position={[0, yPosition, 0]}>
      {/* Main separator plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[buildingWidth, buildingDepth]} />
        <meshStandardMaterial
          color="#0a0a1a"
          transparent
          opacity={0.6}
          side={THREE.DoubleSide}
          emissive="#00ffff"
          emissiveIntensity={0.1}
        />
      </mesh>
      {/* Glowing edges on separator */}
      <lineSegments>
        <edgesGeometry args={[new THREE.PlaneGeometry(buildingWidth, buildingDepth)]} />
        <lineBasicMaterial
          color="#00ffff"
          emissive="#00ffff"
          emissiveIntensity={0.8}
        />
      </lineSegments>
      {/* Grid pattern on separator */}
      <Grid
        args={[buildingWidth, buildingDepth]}
        cellColor="#00ffff"
        sectionColor="#0088ff"
        cellThickness={0.3}
        sectionThickness={0.5}
        fadeDistance={20}
        fadeStrength={1}
        rotation={[-Math.PI / 2, 0, 0]}
      />
    </group>
  );
}

// Connecting lines between floors
function FloorConnector({ floor1Y, floor2Y }) {
  const points = [
    [0, floor1Y + 1.5, 0],
    [0, floor2Y - 1.5, 0],
  ];

  return (
    <Line
      points={points}
      color="#00ffff"
      lineWidth={2}
    />
  );
}

// Animated camera controller
function CameraController({ targetFloor, onAnimationComplete }) {
  const { camera } = useThree();
  const targetRef = useRef({ x: 0, y: 0, z: 0 });
  const animatingRef = useRef(false);

  useEffect(() => {
    if (targetFloor === null) return;

    animatingRef.current = true;
    const floorHeight = 3;
    const yPosition = (targetFloor - 1) * floorHeight;

    // Isometric camera positions
    const positions = {
      1: { x: 12, y: 8, z: 12 },
      2: { x: 12, y: 14, z: 12 },
    };

    const target = positions[targetFloor] || positions[1];
    targetRef.current = target;

    // Animate camera
    const startPos = { ...camera.position };
    const startTime = Date.now();
    const duration = 1500; // 1.5 seconds

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function (ease-in-out)
      const ease = progress < 0.5
        ? 2 * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 2) / 2;

      camera.position.x = startPos.x + (target.x - startPos.x) * ease;
      camera.position.y = startPos.y + (target.y - startPos.y) * ease;
      camera.position.z = startPos.z + (target.z - startPos.z) * ease;

      camera.lookAt(0, yPosition, 0);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        animatingRef.current = false;
        if (onAnimationComplete) {
          onAnimationComplete();
        }
      }
    };

    animate();
  }, [targetFloor, camera, onAnimationComplete]);

  return null;
}

// Main building component
function Building({ selectedFloor, setSelectedFloor, selectedZone, anomalies = {} }) {
  const floor1Highlighted = selectedFloor === 1;
  const floor2Highlighted = selectedFloor === 2;
  const floor1Dimmed = selectedFloor === 2;
  const floor2Dimmed = selectedFloor === 1;
  const floorHeight = 3;
  const buildingWidth = 16;
  const buildingDepth = 14;

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={1} color="#00ffff" />
      <pointLight position={[-10, 10, -10]} intensity={0.8} color="#0088ff" />
      <pointLight position={[0, 15, 0]} intensity={0.6} color="#00ff88" />
      {/* Additional light for selected zone */}
      {selectedZone && (
        <pointLight
          position={[0, (selectedZone.floor - 1) * 3 + 1.5, 0]}
          intensity={1.5}
          color="#ffff00"
          distance={10}
        />
      )}

      {/* Floors */}
      <Floor
        floorNumber={1}
        isHighlighted={floor1Highlighted}
        isDimmed={floor1Dimmed}
        selectedZone={selectedZone}
        anomalies={anomalies}
      />
      <Floor
        floorNumber={2}
        isHighlighted={floor2Highlighted}
        isDimmed={floor2Dimmed}
        selectedZone={selectedZone}
        anomalies={anomalies}
      />

      {/* Connecting lines */}
      <FloorConnector floor1Y={1.5} floor2Y={4.5} />
    </>
  );
}

// Define zones for the building
const BUILDING_ZONES = [
  { id: "meeting-room", name: "Meeting Room", floor: 1, area_m2: 12 },
  { id: "corridor", name: "Corridor", floor: 1, area_m2: 12 },
  { id: "open-office", name: "Open Office", floor: 1, area_m2: 36 },
  { id: "private-office", name: "Private Office", floor: 2, area_m2: 25 },
  { id: "server-room", name: "Server Room", floor: 2, area_m2: 25 },
];

// Main component
function InteractiveBuilding3D({ buildingId = "9" }) {
  const [selectedFloor, setSelectedFloor] = useState(1);
  const [isAnimating, setIsAnimating] = useState(false);
  const [selectedFloors, setSelectedFloors] = useState([1, 2]);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedZone, setSelectedZone] = useState(null);
  const [anomalies, setAnomalies] = useState({});
  const [historicalView, setHistoricalView] = useState("24h"); // 24h, 7d, 30d
  const [historicalData, setHistoricalData] = useState({});
  const [loadingHistorical, setLoadingHistorical] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const playbackIntervalRef = useRef(null);
  const duration = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
  const [buildingViewWidth, setBuildingViewWidth] = useState(() => {
    const saved = localStorage.getItem('building-view-width');
    return saved ? parseInt(saved, 10) : null; // null means use flex: 1
  });
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('building-sidebar-width');
    return saved ? parseInt(saved, 10) : 450;
  });
  const [isResizing, setIsResizing] = useState(false);
  const [resizeType, setResizeType] = useState(null); // 'building' or 'sidebar'
  const containerRef = useRef(null);

  // Anomaly detection function - checks metrics directly with severity levels
  const detectAnomalies = (zoneMetrics) => {
    const detectedAnomalies = {};
    
    Object.entries(zoneMetrics).forEach(([zoneId, zoneData]) => {
      let severity = "green"; // green, yellow, red
      const anomalyReasons = [];
      const thresholdBreaches = [];

      // Energy thresholds
      if (zoneData.energy !== null) {
        if (zoneData.energy > 200) {
          severity = "red";
          anomalyReasons.push("High Energy");
          thresholdBreaches.push({ metric: "energy", value: zoneData.energy, threshold: 200, type: "high" });
        } else if (zoneData.energy > 150) {
          severity = severity === "red" ? "red" : "yellow";
          thresholdBreaches.push({ metric: "energy", value: zoneData.energy, threshold: 150, type: "warning" });
        } else if (zoneData.energy < 50) {
          severity = "red";
          anomalyReasons.push("Low Energy");
          thresholdBreaches.push({ metric: "energy", value: zoneData.energy, threshold: 50, type: "low" });
        }
      }

      // Temperature thresholds
      if (zoneData.temperature !== null) {
        if (zoneData.temperature > 28 || zoneData.temperature < 18) {
          severity = "red";
          anomalyReasons.push(
            zoneData.temperature > 28 ? "High Temperature" : "Low Temperature"
          );
          thresholdBreaches.push({
            metric: "temperature",
            value: zoneData.temperature,
            threshold: zoneData.temperature > 28 ? 28 : 18,
            type: zoneData.temperature > 28 ? "high" : "low"
          });
        } else if (zoneData.temperature > 26 || zoneData.temperature < 20) {
          severity = severity === "red" ? "red" : "yellow";
          thresholdBreaches.push({
            metric: "temperature",
            value: zoneData.temperature,
            threshold: zoneData.temperature > 26 ? 26 : 20,
            type: "warning"
          });
        }
      }

      // Occupancy thresholds
      if (zoneData.occupancy !== null) {
        if (zoneData.occupancy > 0.9 || zoneData.occupancy < 0) {
          severity = "red";
          anomalyReasons.push(
            zoneData.occupancy > 0.9 ? "High Occupancy" : "Invalid Occupancy"
          );
          thresholdBreaches.push({
            metric: "occupancy",
            value: zoneData.occupancy,
            threshold: zoneData.occupancy > 0.9 ? 0.9 : 0,
            type: zoneData.occupancy > 0.9 ? "high" : "invalid"
          });
        } else if (zoneData.occupancy > 0.8) {
          severity = severity === "red" ? "red" : "yellow";
          thresholdBreaches.push({
            metric: "occupancy",
            value: zoneData.occupancy,
            threshold: 0.8,
            type: "warning"
          });
        }
      }

      if (severity !== "green") {
        detectedAnomalies[zoneId] = {
          hasAnomaly: true,
          severity: severity,
          reasons: anomalyReasons,
          thresholdBreaches: thresholdBreaches,
        };
      }
    });

    return detectedAnomalies;
  };

  // Load historical data for all zones on mount
  useEffect(() => {
    async function loadAllHistoricalData() {
      try {
        const hours = historicalView === "24h" ? 24 : historicalView === "7d" ? 168 : 720;
        const historicalPromises = BUILDING_ZONES.map(zone =>
          fetchHistoricalData(
            buildingId,
            zone.id,
            ["energy", "temperature", "occupancy"],
            hours
          ).catch(err => {
            console.error(`Failed to load historical data for ${zone.id}:`, err);
            return { points: [] };
          })
        );
        const historicalResults = await Promise.all(historicalPromises);
        const historicalMap = {};
        BUILDING_ZONES.forEach((zone, index) => {
          const result = historicalResults[index];
          // Transform API response to array format if needed
          if (result && result.points && Array.isArray(result.points) && result.points.length > 0) {
            // Group points by timestamp and extract metric values
            const groupedByTime = {};
            result.points.forEach(point => {
              const timeKey = point.timestamp || point._time || point.time;
              if (!timeKey) return;
              
              if (!groupedByTime[timeKey]) {
                groupedByTime[timeKey] = { timestamp: timeKey };
              }
              // Map metric name to value
              const metricName = point.metric || point._measurement || point.measurement;
              const value = point.value || point._value;
              if (metricName && value != null) {
                if (metricName === 'energy' || metricName === 'temperature' || metricName === 'occupancy') {
                  groupedByTime[timeKey][metricName] = value;
                }
              }
            });
            // Convert to array and fill missing values with defaults
            const sortedPoints = Object.values(groupedByTime)
              .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
              .map(point => ({
                energy: point.energy ?? (100 + Math.random() * 50),
                temperature: point.temperature ?? (20 + Math.random() * 5),
                occupancy: point.occupancy ?? (0.3 + Math.random() * 0.4),
                timestamp: point.timestamp,
              }));
            
            // If we have valid data, use it; otherwise generate synthetic
            if (sortedPoints.length > 0) {
              historicalMap[zone.id] = sortedPoints;
            } else {
              // Generate synthetic data
              const points = [];
              const now = Date.now();
              for (let i = 0; i < 50; i++) {
                const timestamp = now - (50 - i) * (hours * 60 * 60 * 1000) / 50;
                points.push({
                  timestamp: new Date(timestamp).toISOString(),
                  energy: 100 + Math.random() * 50 + Math.sin(i / 5) * 30,
                  temperature: 20 + Math.random() * 5 + Math.sin(i / 8) * 3,
                  occupancy: 0.3 + Math.random() * 0.4 + Math.sin(i / 10) * 0.2,
                });
              }
              historicalMap[zone.id] = points;
            }
          } else {
            // Generate synthetic data if API fails
            const points = [];
            const now = Date.now();
            for (let i = 0; i < 50; i++) {
              const timestamp = now - (50 - i) * (hours * 60 * 60 * 1000) / 50;
              points.push({
                timestamp: new Date(timestamp).toISOString(),
                energy: 100 + Math.random() * 50 + Math.sin(i / 5) * 30,
                temperature: 20 + Math.random() * 5 + Math.sin(i / 8) * 3,
                occupancy: 0.3 + Math.random() * 0.4 + Math.sin(i / 10) * 0.2,
              });
            }
            historicalMap[zone.id] = points;
          }
        });
        setHistoricalData(historicalMap);
      } catch (error) {
        console.error("Failed to load historical data:", error);
      }
    }

    loadAllHistoricalData();
  }, [buildingId, historicalView]);

  // Fetch metrics
  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        const data = await fetchLatestMetrics(buildingId);

        const zoneMetrics = {};
        const zoneIdMap = {};
        BUILDING_ZONES.forEach((zone, index) => {
          zoneIdMap[zone.id] = zone.id;
          zoneIdMap[`zone-${index + 1}`] = zone.id;
          zoneIdMap[`z${index + 1}`] = zone.id;
        });

        if (data.latest_values) {
          Object.entries(data.latest_values).forEach(([apiZoneId, zoneData]) => {
            const layoutZoneId = zoneIdMap[apiZoneId] || apiZoneId;
            zoneMetrics[layoutZoneId] = {
              energy: zoneData.energy ?? null,
              temperature: zoneData.temperature ?? null,
              occupancy: zoneData.occupancy ?? null,
            };
          });
        }

        // Fill in missing zones with default values
        BUILDING_ZONES.forEach((zone) => {
          if (!zoneMetrics[zone.id]) {
            zoneMetrics[zone.id] = {
              energy: 100 + Math.random() * 50,
              temperature: 20 + Math.random() * 5,
              occupancy: 0.3 + Math.random() * 0.4,
            };
          }
        });

        setMetrics(zoneMetrics);
        
        // Detect anomalies after metrics are loaded
        const detectedAnomalies = detectAnomalies(zoneMetrics);
        setAnomalies(detectedAnomalies);
      } catch (error) {
        console.error("Failed to load metrics:", error);
        // Set default metrics
        const defaultMetrics = {};
        BUILDING_ZONES.forEach((zone) => {
          defaultMetrics[zone.id] = {
            energy: 100 + Math.random() * 50,
            temperature: 20 + Math.random() * 5,
            occupancy: 0.3 + Math.random() * 0.4,
          };
        });
        setMetrics(defaultMetrics);
        
        // Detect anomalies in default metrics too
        const detectedAnomalies = detectAnomalies(defaultMetrics);
        setAnomalies(detectedAnomalies);
      } finally {
        setLoading(false);
      }
    }

    // Only load real-time metrics if not in playback mode
    if (!isPlaying) {
      loadMetrics();
      const interval = setInterval(loadMetrics, 30000);
      return () => clearInterval(interval);
    }
  }, [buildingId, isPlaying]);

  // Time playback logic
  useEffect(() => {
    if (isPlaying) {
      playbackIntervalRef.current = setInterval(() => {
        setCurrentTime(prev => {
          const next = prev + 60000; // Advance by 1 minute
          if (next >= duration) {
            setIsPlaying(false);
            return 0;
          }
          return next;
        });
      }, 100); // Update every 100ms for smooth animation
    } else {
      if (playbackIntervalRef.current) {
        clearInterval(playbackIntervalRef.current);
      }
    }

    return () => {
      if (playbackIntervalRef.current) {
        clearInterval(playbackIntervalRef.current);
      }
    };
  }, [isPlaying, duration]);

  // Update metrics based on current playback time (interpolate from historical data)
  useEffect(() => {
    if (!isPlaying || !historicalData || Object.keys(historicalData).length === 0) return;

    const updatedMetrics = {};
    Object.entries(historicalData).forEach(([zoneId, points]) => {
      if (!points || points.length === 0) return;

      const timeProgress = currentTime / duration;
      const index = Math.floor(timeProgress * (points.length - 1));
      const point = points[Math.min(index, points.length - 1)];

      if (point) {
        updatedMetrics[zoneId] = {
          energy: point.energy ?? 100,
          temperature: point.temperature ?? 22,
          occupancy: point.occupancy ?? 0.5,
        };
      }
    });

    if (Object.keys(updatedMetrics).length > 0) {
      setMetrics(updatedMetrics);
      const detectedAnomalies = detectAnomalies(updatedMetrics);
      setAnomalies(detectedAnomalies);
    }
  }, [currentTime, historicalData, duration, isPlaying]);

  const handleFloorChange = (floor) => {
    if (isAnimating || selectedFloor === floor) return;
    setIsAnimating(true);
    setSelectedFloor(floor);
  };

  const handleAnimationComplete = () => {
    setIsAnimating(false);
  };

  const handleFloorToggle = (floor) => {
    setSelectedFloors((prev) =>
      prev.includes(floor)
        ? prev.filter((f) => f !== floor)
        : [...prev, floor]
    );
  };

  const handleZoneClick = (zone) => {
    const newSelectedZone = selectedZone?.id === zone.id ? null : zone;
    setSelectedZone(newSelectedZone);
    
    // Automatically switch to the floor of the selected zone
    if (newSelectedZone && newSelectedZone.floor !== selectedFloor && !isAnimating) {
      setIsAnimating(true);
      setSelectedFloor(newSelectedZone.floor);
    }
  };

  const handleCloseZoneDetails = () => {
    setSelectedZone(null);
  };

  // Note: Historical data is now loaded for all zones in the main useEffect above

  // Get status color for a zone
  const getStatusColor = (zoneId) => {
    const anomaly = anomalies[zoneId];
    if (!anomaly) return "green";
    return anomaly.severity;
  };

  const availableFloors = [1, 2];
  const filteredZones = BUILDING_ZONES.filter((z) => selectedFloors.includes(z.floor));

  // Handle resize
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing || !containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const isMobile = window.innerWidth <= 640;
      
      if (isMobile) return; // Skip resize on mobile
      
      if (resizeType === 'sidebar') {
        // Resize sidebar (right panel) - this effectively resizes both panels
        const newWidth = containerRect.right - e.clientX;
        const constrainedWidth = Math.max(300, Math.min(800, newWidth));
        setSidebarWidth(constrainedWidth);
      } else if (resizeType === 'building') {
        // Resize building view (left panel)
        const newWidth = e.clientX - containerRect.left;
        const constrainedWidth = Math.max(400, Math.min(window.innerWidth - 350, newWidth));
        setBuildingViewWidth(constrainedWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      setResizeType(null);
      // Save to localStorage
      if (buildingViewWidth) {
        localStorage.setItem('building-view-width', buildingViewWidth.toString());
      }
      localStorage.setItem('building-sidebar-width', sidebarWidth.toString());
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, resizeType, buildingViewWidth, sidebarWidth]);

  return (
    <div 
      className="interactive-building-3d-container"
      ref={containerRef}
    >
      <div 
        className="interactive-building-3d"
        style={buildingViewWidth ? { width: `${buildingViewWidth}px`, flex: 'none' } : {}}
      >
        {/* Floor control buttons */}
        <div className="floor-controls">
          <button
            className={`floor-button ${selectedFloor === 1 ? "active" : ""}`}
            onClick={() => handleFloorChange(1)}
            disabled={isAnimating}
          >
            Floor 1
          </button>
          <button
            className={`floor-button ${selectedFloor === 2 ? "active" : ""}`}
            onClick={() => handleFloorChange(2)}
            disabled={isAnimating}
          >
            Floor 2
          </button>
        </div>

        {/* Time playback controls */}
        <TimePlaybackControls
          onTimeChange={(time) => {
            setIsPlaying(false);
            setCurrentTime(time);
          }}
          isPlaying={isPlaying}
          onPlayPause={() => setIsPlaying(!isPlaying)}
          currentTime={currentTime}
          duration={duration}
        />

        {/* 3D Canvas */}
        <div className="building-canvas">
          <Canvas
            camera={{ position: [12, 8, 12], fov: 50 }}
            gl={{ antialias: true, alpha: true }}
          >
            <CameraController
              targetFloor={selectedFloor}
              onAnimationComplete={handleAnimationComplete}
            />
            <OrbitControls
              enablePan={true}
              enableZoom={true}
              enableRotate={true}
              minDistance={8}
              maxDistance={30}
              target={[0, selectedFloor === 1 ? 0 : 3, 0]}
            />
            <Building
              selectedFloor={selectedFloor}
              setSelectedFloor={setSelectedFloor}
              selectedZone={selectedZone}
              anomalies={anomalies}
            />
          </Canvas>
        </div>
      </div>

      {/* Resize handle between panels */}
      <div
        className="resize-handle"
        onMouseDown={(e) => {
          e.preventDefault();
          setIsResizing(true);
          setResizeType('sidebar'); // Resizing sidebar affects both panels
        }}
        title="Drag to resize panels"
      >
        <div className="resize-arrow-left">◄</div>
        <div className="resize-arrow-right">►</div>
      </div>

      {/* Side panel with building information */}
      <div 
        className="layout-info-sidebar"
        style={{ width: `${sidebarWidth}px` }}
      >
        <h3>Building Information</h3>
        <p>
          <strong>Building ID:</strong> {buildingId}
        </p>
        <p>
          <strong>Total Zones:</strong> {BUILDING_ZONES.length}
        </p>
        <p>
          <strong>Floors:</strong> 2
        </p>

        {/* Historical Data Toggle */}
        <div className="historical-view-toggle">
          <h4>Historical View</h4>
          <div className="view-buttons">
            <button
              className={`view-button ${historicalView === "24h" ? "active" : ""}`}
              onClick={() => setHistoricalView("24h")}
            >
              24h
            </button>
            <button
              className={`view-button ${historicalView === "7d" ? "active" : ""}`}
              onClick={() => setHistoricalView("7d")}
            >
              7d
            </button>
            <button
              className={`view-button ${historicalView === "30d" ? "active" : ""}`}
              onClick={() => setHistoricalView("30d")}
            >
              30d
            </button>
          </div>
        </div>

        {/* Floor Picker */}
        <div className="floor-picker">
          <h4>Select Floors</h4>
          {availableFloors.map((floor) => (
            <label key={floor} className="floor-checkbox">
              <input
                type="checkbox"
                checked={selectedFloors.includes(floor)}
                onChange={() => handleFloorToggle(floor)}
              />
              Floor {floor}
            </label>
          ))}
        </div>

        {loading && <p className="muted">Loading metrics...</p>}

        <div className="zones-list">
          <h4>Zones ({filteredZones.length})</h4>
          <ul>
            {filteredZones.map((zone) => (
              <li
                key={zone.id}
                className={selectedZone?.id === zone.id ? "selected" : ""}
                onClick={() => handleZoneClick(zone)}
                style={{ cursor: "pointer" }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  {/* Status dot indicator */}
                  <div
                    className={`status-dot status-${getStatusColor(zone.id)}`}
                    style={{
                      width: "12px",
                      height: "12px",
                      borderRadius: "50%",
                      backgroundColor:
                        getStatusColor(zone.id) === "red"
                          ? "#ff0000"
                          : getStatusColor(zone.id) === "yellow"
                          ? "#ffaa00"
                          : "#22c55e",
                      boxShadow:
                        getStatusColor(zone.id) !== "green"
                          ? `0 0 8px ${
                              getStatusColor(zone.id) === "red" ? "#ff0000" : "#ffaa00"
                            }`
                          : "none",
                      flexShrink: 0,
                    }}
                  />
                  <strong>
                    {zone.name}
                    {anomalies[zone.id] && (
                      <span style={{ color: "#ff0000", marginLeft: "0.5rem" }}>⚠️</span>
                    )}
                  </strong>
                </div>
                <br />
                Floor {zone.floor} · {zone.area_m2.toFixed(1)} m²
                {anomalies[zone.id] && (
                  <div style={{ color: "#ff0000", fontSize: "0.8rem", marginTop: "0.25rem" }}>
                    ⚠️ Anomaly: {anomalies[zone.id].reasons.join(", ")}
                  </div>
                )}
                {metrics[zone.id] ? (
                  <>
                    <div className="zone-metrics">
                      <span>
                        Energy:{" "}
                        {metrics[zone.id].energy != null
                          ? metrics[zone.id].energy.toFixed(1)
                          : "N/A"}{" "}
                        kWh
                      </span>
                      <span>
                        Temp:{" "}
                        {metrics[zone.id].temperature != null
                          ? metrics[zone.id].temperature.toFixed(1)
                          : "N/A"}
                        °C
                      </span>
                      <span>
                        Occ:{" "}
                        {metrics[zone.id].occupancy != null
                          ? (metrics[zone.id].occupancy * 100).toFixed(0)
                          : "N/A"}
                        %
                      </span>
                    </div>
                    {/* Sparklines for trend visualization */}
                    {historicalData[zone.id] && historicalData[zone.id].length > 0 && (
                      <div className="zone-sparklines">
                        <div className="sparkline-item">
                          <div className="sparkline-label">Energy</div>
                          <Sparkline
                            data={historicalData[zone.id]}
                            metric="energy"
                            color="#00ffff"
                            width={130}
                            height={40}
                          />
                        </div>
                        <div className="sparkline-item">
                          <div className="sparkline-label">Temp</div>
                          <Sparkline
                            data={historicalData[zone.id]}
                            metric="temperature"
                            color="#ff6b6b"
                            width={130}
                            height={40}
                          />
                        </div>
                        <div className="sparkline-item">
                          <div className="sparkline-label">Occ</div>
                          <Sparkline
                            data={historicalData[zone.id]}
                            metric="occupancy"
                            color="#51cf66"
                            width={130}
                            height={40}
                          />
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="zone-metrics">
                    <span className="muted">No metrics available</span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>

        {/* Zone details panel */}
        {selectedZone && (
          <div className="zone-details-panel" style={{ marginTop: "1rem" }}>
            <div className="zone-details-header">
              <h4>{selectedZone.name}</h4>
              <button
                onClick={handleCloseZoneDetails}
                className="close-button"
              >
                ×
              </button>
            </div>
            <div className="zone-details-content">
              <p>
                <strong>Zone ID:</strong> {selectedZone.id}
              </p>
              <p>
                <strong>Floor:</strong> {selectedZone.floor}
              </p>
              <p>
                <strong>Area:</strong> {selectedZone.area_m2.toFixed(1)} m²
              </p>
              {metrics[selectedZone.id] && (
                <>
                  <p>
                    <strong>Energy:</strong>{" "}
                    {metrics[selectedZone.id].energy != null
                      ? `${metrics[selectedZone.id].energy.toFixed(1)} kWh`
                      : "N/A"}
                  </p>
                  <p>
                    <strong>Temperature:</strong>{" "}
                    {metrics[selectedZone.id].temperature != null
                      ? `${metrics[selectedZone.id].temperature.toFixed(1)}°C`
                      : "N/A"}
                  </p>
                  <p>
                    <strong>Occupancy:</strong>{" "}
                    {metrics[selectedZone.id].occupancy != null
                      ? `${(metrics[selectedZone.id].occupancy * 100).toFixed(0)}%`
                      : "N/A"}
                  </p>
                </>
              )}
              {/* Historical data summary */}
              {historicalData[selectedZone.id] && !loadingHistorical && (
                <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid rgba(148, 163, 184, 0.2)" }}>
                  <p style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.5rem" }}>
                    <strong>Historical Data ({historicalView}):</strong>
                  </p>
                  <p style={{ fontSize: "0.8rem", color: "#cbd5f5" }}>
                    {historicalData[selectedZone.id].points?.length || 0} data points
                  </p>
                </div>
              )}
              {loadingHistorical && (
                <p style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: "1rem" }}>
                  Loading historical data...
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default InteractiveBuilding3D;

