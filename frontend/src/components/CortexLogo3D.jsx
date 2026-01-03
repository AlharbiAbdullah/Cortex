import { useRef, useMemo, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Text, Float } from "@react-three/drei";
import * as THREE from "three";

// ═══════════════════════════════════════════════════════════════════════════
// CORTEX 3D LOGO - Neural Intelligence Visualization
// A living, breathing representation of enterprise intelligence
// ═══════════════════════════════════════════════════════════════════════════

// Color palette - Orange/Amber neural network aesthetic
const COLORS = {
  amber: new THREE.Color("#f59e0b"),
  amberLight: new THREE.Color("#fbbf24"),
  amberGlow: new THREE.Color("#fcd34d"),
  orange: new THREE.Color("#fb923c"),
  orangeBright: new THREE.Color("#fdba74"),
  cream: new THREE.Color("#fef3c7"),
  warmWhite: new THREE.Color("#fffbeb"),
};

// ═══════════════════════════════════════════════════════════════════════════
// NEURAL PARTICLES - Synaptic nodes orbiting the cortex
// ═══════════════════════════════════════════════════════════════════════════

function NeuralParticles({ count = 200, radius = 4 }) {
  const pointsRef = useRef();
  const linesRef = useRef();

  // Initialize particle system with positions, velocities, and colors
  const { positions, velocities, colors, sizes } = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const velocities = [];
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);

    const colorOptions = [
      COLORS.amber,
      COLORS.amberGlow,
      COLORS.orange,
      COLORS.orangeBright,
      COLORS.cream,
    ];

    for (let i = 0; i < count; i++) {
      // Spherical distribution with some clustering near center
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = radius * (0.3 + Math.random() * 0.7);

      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.6; // Flatten slightly
      positions[i * 3 + 2] = r * Math.cos(phi);

      // Organic velocity with orbital tendency
      velocities.push({
        x: (Math.random() - 0.5) * 0.008,
        y: (Math.random() - 0.5) * 0.008,
        z: (Math.random() - 0.5) * 0.008,
        // Orbital parameters
        orbitSpeed: 0.0005 + Math.random() * 0.001,
        orbitPhase: Math.random() * Math.PI * 2,
        orbitRadius: r,
        orbitTilt: (Math.random() - 0.5) * 0.5,
      });

      // Color distribution weighted toward amber
      const colorIndex = Math.random() < 0.6 ? 0 : Math.floor(Math.random() * colorOptions.length);
      const color = colorOptions[colorIndex];
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;

      // Varied particle sizes
      sizes[i] = 0.02 + Math.random() * 0.04;
    }

    return { positions, velocities, colors, sizes };
  }, [count, radius]);

  // Connection lines buffer (max connections)
  const maxConnections = 300;
  const linePositions = useMemo(() => new Float32Array(maxConnections * 6), []);
  const lineColors = useMemo(() => new Float32Array(maxConnections * 6), []);

  // Animation loop
  useFrame((state) => {
    if (!pointsRef.current) return;

    const time = state.clock.elapsedTime;
    const posArray = pointsRef.current.geometry.attributes.position.array;

    // Update particle positions with Brownian motion + orbital tendency
    for (let i = 0; i < count; i++) {
      const vel = velocities[i];
      const idx = i * 3;

      // Current position
      let x = posArray[idx];
      let y = posArray[idx + 1];
      let z = posArray[idx + 2];

      // Add Brownian motion
      x += vel.x + (Math.random() - 0.5) * 0.002;
      y += vel.y + (Math.random() - 0.5) * 0.002;
      z += vel.z + (Math.random() - 0.5) * 0.002;

      // Gentle orbital motion
      const orbitAngle = time * vel.orbitSpeed + vel.orbitPhase;
      const orbitInfluence = 0.002;
      x += Math.cos(orbitAngle) * orbitInfluence;
      z += Math.sin(orbitAngle) * orbitInfluence;

      // Soft boundary - keep particles in sphere
      const dist = Math.sqrt(x * x + y * y + z * z);
      if (dist > radius * 1.2) {
        const scale = (radius * 0.8) / dist;
        x *= scale;
        y *= scale;
        z *= scale;
        // Reverse velocity
        vel.x *= -0.5;
        vel.y *= -0.5;
        vel.z *= -0.5;
      }

      // Breathing effect - subtle expansion/contraction
      const breathe = Math.sin(time * 0.5) * 0.02 + 1;
      posArray[idx] = x * breathe;
      posArray[idx + 1] = y * breathe;
      posArray[idx + 2] = z * breathe;
    }

    pointsRef.current.geometry.attributes.position.needsUpdate = true;

    // Update connection lines between nearby particles
    if (linesRef.current) {
      let lineIndex = 0;
      const connectionDistance = 1.2;
      const maxChecks = Math.min(count, 80); // Limit checks for performance

      for (let i = 0; i < maxChecks && lineIndex < maxConnections; i++) {
        for (let j = i + 1; j < maxChecks && lineIndex < maxConnections; j++) {
          const idx1 = i * 3;
          const idx2 = j * 3;

          const dx = posArray[idx1] - posArray[idx2];
          const dy = posArray[idx1 + 1] - posArray[idx2 + 1];
          const dz = posArray[idx1 + 2] - posArray[idx2 + 2];
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

          if (dist < connectionDistance) {
            const lineIdx = lineIndex * 6;
            const opacity = 1 - dist / connectionDistance;

            // Line start
            linePositions[lineIdx] = posArray[idx1];
            linePositions[lineIdx + 1] = posArray[idx1 + 1];
            linePositions[lineIdx + 2] = posArray[idx1 + 2];
            // Line end
            linePositions[lineIdx + 3] = posArray[idx2];
            linePositions[lineIdx + 4] = posArray[idx2 + 1];
            linePositions[lineIdx + 5] = posArray[idx2 + 2];

            // Color with fade based on distance
            const pulseIntensity = (Math.sin(time * 2 + i * 0.1) + 1) * 0.3 + 0.4;
            lineColors[lineIdx] = COLORS.amber.r * opacity * pulseIntensity;
            lineColors[lineIdx + 1] = COLORS.amber.g * opacity * pulseIntensity;
            lineColors[lineIdx + 2] = COLORS.amber.b * opacity * pulseIntensity;
            lineColors[lineIdx + 3] = COLORS.orange.r * opacity * pulseIntensity;
            lineColors[lineIdx + 4] = COLORS.orange.g * opacity * pulseIntensity;
            lineColors[lineIdx + 5] = COLORS.orange.b * opacity * pulseIntensity;

            lineIndex++;
          }
        }
      }

      // Clear remaining lines
      for (let i = lineIndex * 6; i < maxConnections * 6; i++) {
        linePositions[i] = 0;
        lineColors[i] = 0;
      }

      linesRef.current.geometry.attributes.position.needsUpdate = true;
      linesRef.current.geometry.attributes.color.needsUpdate = true;
    }
  });

  return (
    <group>
      {/* Neural particles */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={count}
            array={positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={count}
            array={colors}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-size"
            count={count}
            array={sizes}
            itemSize={1}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.08}
          vertexColors
          transparent
          opacity={0.9}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Connection lines */}
      <lineSegments ref={linesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={maxConnections * 2}
            array={linePositions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={maxConnections * 2}
            array={lineColors}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial
          vertexColors
          transparent
          opacity={0.6}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </lineSegments>
    </group>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// CORTEX TEXT - The living brain of the platform
// ═══════════════════════════════════════════════════════════════════════════

function CortexText() {
  const textRef = useRef();
  const glowRef = useRef();

  // Pulsing glow animation
  useFrame((state) => {
    if (glowRef.current) {
      const pulse = Math.sin(state.clock.elapsedTime * 1.5) * 0.15 + 0.85;
      glowRef.current.material.opacity = pulse * 0.3;
    }
  });

  return (
    <Float speed={1.5} rotationIntensity={0.1} floatIntensity={0.3}>
      <group>
        {/* Glow layer - behind text */}
        <Text
          ref={glowRef}
          fontSize={1.4}
          letterSpacing={0.15}
          position={[0, 0, -0.1]}
          anchorX="center"
          anchorY="middle"
          fontWeight="bold"
        >
          CORTEX
          <meshBasicMaterial
            color="#fcd34d"
            transparent
            opacity={0.3}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </Text>

        {/* Main text with metallic amber material */}
        <Text
          ref={textRef}
          fontSize={1.4}
          letterSpacing={0.15}
          anchorX="center"
          anchorY="middle"
          fontWeight="bold"
        >
          CORTEX
          <meshStandardMaterial
            color="#f59e0b"
            metalness={0.7}
            roughness={0.2}
            emissive="#f59e0b"
            emissiveIntensity={0.4}
          />
        </Text>

        {/* Subtle front highlight */}
        <Text
          fontSize={1.4}
          letterSpacing={0.15}
          position={[0, 0, 0.02]}
          anchorX="center"
          anchorY="middle"
          fontWeight="bold"
        >
          CORTEX
          <meshBasicMaterial
            color="#ffffff"
            transparent
            opacity={0.1}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </Text>
      </group>
    </Float>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// AMBIENT EFFECTS - Atmospheric depth
// ═══════════════════════════════════════════════════════════════════════════

function AmbientEffects() {
  const ringRef = useRef();

  useFrame((state) => {
    if (ringRef.current) {
      ringRef.current.rotation.z = state.clock.elapsedTime * 0.1;
      ringRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.1;
    }
  });

  return (
    <group ref={ringRef}>
      {/* Outer orbital ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[5, 0.02, 8, 64]} />
        <meshBasicMaterial
          color="#f59e0b"
          transparent
          opacity={0.15}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Inner orbital ring */}
      <mesh rotation={[Math.PI / 2.5, 0, 0]}>
        <torusGeometry args={[4, 0.015, 8, 64]} />
        <meshBasicMaterial
          color="#fb923c"
          transparent
          opacity={0.1}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// SCENE - Complete 3D composition
// ═══════════════════════════════════════════════════════════════════════════

function Scene() {
  const groupRef = useRef();

  // Gentle overall rotation
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.15) * 0.15;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Lighting setup */}
      <ambientLight intensity={0.4} />
      <pointLight position={[5, 5, 5]} intensity={1} color="#f59e0b" />
      <pointLight position={[-5, -5, 5]} intensity={0.5} color="#fb923c" />
      <pointLight position={[0, 0, 8]} intensity={0.3} color="#fef3c7" />

      {/* Core elements */}
      <CortexText />
      <NeuralParticles count={200} radius={4.5} />
      <AmbientEffects />
    </group>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT - Exported reusable component
// ═══════════════════════════════════════════════════════════════════════════

export default function CortexLogo3D({
  width = "100%",
  height = "400px",
  className = "",
}) {
  return (
    <div
      className={className}
      style={{
        width: typeof width === "number" ? `${width}px` : width,
        height: typeof height === "number" ? `${height}px` : height,
        background: "transparent",
      }}
    >
      <Canvas
        camera={{ position: [0, 0, 8], fov: 50 }}
        gl={{
          alpha: true,
          antialias: true,
          powerPreference: "high-performance",
        }}
        style={{ background: "transparent" }}
      >
        <Scene />
      </Canvas>
    </div>
  );
}
