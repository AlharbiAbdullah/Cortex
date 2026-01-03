import React, { useRef, useMemo, useEffect } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import { EffectComposer, Bloom } from "@react-three/postprocessing"
import * as THREE from "three"

// Brain outline path (inspired by the AI brain icon - curved brain shape)
const BRAIN_OUTLINE = [
  // Top curve
  [0.50, 0.95],
  [0.40, 0.94],
  [0.30, 0.90],
  [0.22, 0.82],
  [0.18, 0.72],
  // Left side
  [0.15, 0.60],
  [0.14, 0.50],
  [0.16, 0.40],
  [0.20, 0.32],
  [0.26, 0.25],
  [0.34, 0.18],
  [0.44, 0.14],
  // Bottom curve
  [0.50, 0.12],
  [0.56, 0.14],
  [0.66, 0.18],
  [0.74, 0.25],
  [0.80, 0.32],
  // Right side
  [0.84, 0.40],
  [0.86, 0.50],
  [0.85, 0.60],
  [0.82, 0.72],
  [0.78, 0.82],
  [0.70, 0.90],
  [0.60, 0.94],
  [0.50, 0.95],
]

// Central brain fold (creates the characteristic brain division)
const BRAIN_FOLD = [
  [0.50, 0.88],
  [0.48, 0.75],
  [0.50, 0.62],
  [0.52, 0.50],
  [0.50, 0.38],
  [0.48, 0.25],
]

// Check if point is inside brain outline
function isInsideBrain(x, y) {
  let inside = false
  const profile = BRAIN_OUTLINE

  for (let i = 0, j = profile.length - 1; i < profile.length; j = i++) {
    const xi = profile[i][0], yi = profile[i][1]
    const xj = profile[j][0], yj = profile[j][1]

    if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
      inside = !inside
    }
  }

  return inside
}

// Generate circuit nodes inside brain shape
function generateCircuitNodes(count = 55) {
  const nodes = []
  let attempts = 0
  const maxAttempts = count * 30

  // Define key node positions (larger, more prominent)
  const keyPositions = [
    { x: 0.30, y: 0.70, size: 0.08, isKey: true },  // Top left
    { x: 0.70, y: 0.70, size: 0.08, isKey: true },  // Top right
    { x: 0.50, y: 0.50, size: 0.10, isKey: true },  // Center (main processor)
    { x: 0.35, y: 0.35, size: 0.07, isKey: true },  // Bottom left
    { x: 0.65, y: 0.35, size: 0.07, isKey: true },  // Bottom right
    { x: 0.25, y: 0.55, size: 0.06, isKey: true },  // Left mid
    { x: 0.75, y: 0.55, size: 0.06, isKey: true },  // Right mid
  ]

  // Add key nodes first
  keyPositions.forEach((pos) => {
    if (isInsideBrain(pos.x, pos.y)) {
      nodes.push({
        x: (pos.x - 0.5) * 3.2,
        y: (pos.y - 0.5) * 3.2,
        size: pos.size,
        isKey: true,
        phase: Math.random() * Math.PI * 2,
        pulseSpeed: 0.8 + Math.random() * 0.5,
      })
    }
  })

  // Fill with smaller nodes
  while (nodes.length < count && attempts < maxAttempts) {
    attempts++
    const x = 0.12 + Math.random() * 0.76
    const y = 0.10 + Math.random() * 0.88

    if (isInsideBrain(x, y)) {
      // Check minimum distance from existing nodes
      const nodeX = (x - 0.5) * 3.2
      const nodeY = (y - 0.5) * 3.2
      const tooClose = nodes.some(
        (n) => Math.hypot(n.x - nodeX, n.y - nodeY) < 0.25
      )

      if (!tooClose) {
        nodes.push({
          x: nodeX,
          y: nodeY,
          size: 0.025 + Math.random() * 0.015,
          isKey: false,
          phase: Math.random() * Math.PI * 2,
          pulseSpeed: 1 + Math.random() * 1.5,
        })
      }
    }
  }

  return nodes
}

// Generate circuit traces (neural connections)
function generateCircuitTraces(nodes) {
  const traces = []
  const keyNodes = nodes.filter((n) => n.isKey)
  const smallNodes = nodes.filter((n) => !n.isKey)

  // Connect key nodes to each other
  for (let i = 0; i < keyNodes.length; i++) {
    for (let j = i + 1; j < keyNodes.length; j++) {
      const dist = Math.hypot(keyNodes[i].x - keyNodes[j].x, keyNodes[i].y - keyNodes[j].y)
      if (dist < 1.8 && Math.random() > 0.3) {
        traces.push({
          from: nodes.indexOf(keyNodes[i]),
          to: nodes.indexOf(keyNodes[j]),
          isMain: true,
          pulseOffset: Math.random(),
          pulseSpeed: 0.4 + Math.random() * 0.3,
        })
      }
    }
  }

  // Connect small nodes to nearest key node and nearby small nodes
  smallNodes.forEach((node) => {
    const nodeIdx = nodes.indexOf(node)

    // Find nearest key node
    let nearestKey = null
    let nearestKeyDist = Infinity
    keyNodes.forEach((kn) => {
      const dist = Math.hypot(kn.x - node.x, kn.y - node.y)
      if (dist < nearestKeyDist) {
        nearestKeyDist = dist
        nearestKey = kn
      }
    })

    if (nearestKey && nearestKeyDist < 1.2) {
      traces.push({
        from: nodeIdx,
        to: nodes.indexOf(nearestKey),
        isMain: false,
        pulseOffset: Math.random(),
        pulseSpeed: 0.5 + Math.random() * 0.5,
      })
    }

    // Connect to 1-2 nearby small nodes
    const nearby = smallNodes
      .filter((n) => n !== node)
      .map((n) => ({ node: n, dist: Math.hypot(n.x - node.x, n.y - node.y) }))
      .filter((d) => d.dist < 0.6)
      .sort((a, b) => a.dist - b.dist)
      .slice(0, 1)

    nearby.forEach(({ node: targetNode }) => {
      const targetIdx = nodes.indexOf(targetNode)
      const exists = traces.some(
        (t) =>
          (t.from === nodeIdx && t.to === targetIdx) ||
          (t.from === targetIdx && t.to === nodeIdx)
      )
      if (!exists && Math.random() > 0.4) {
        traces.push({
          from: nodeIdx,
          to: targetIdx,
          isMain: false,
          pulseOffset: Math.random(),
          pulseSpeed: 0.6 + Math.random() * 0.6,
        })
      }
    })
  })

  return traces
}

// Circuit node component (dot with glow)
function CircuitNode({ x, y, size, isKey, phase, pulseSpeed }) {
  const meshRef = useRef()
  const glowRef = useRef()
  const ringRef = useRef()

  useFrame((state) => {
    const t = state.clock.elapsedTime
    const pulse = 0.7 + Math.sin(t * pulseSpeed + phase) * 0.3

    if (meshRef.current) {
      meshRef.current.material.emissiveIntensity = pulse * (isKey ? 4 : 2)
    }
    if (glowRef.current) {
      glowRef.current.material.opacity = 0.2 + pulse * 0.3
      glowRef.current.scale.setScalar(1 + pulse * 0.3)
    }
    if (ringRef.current && isKey) {
      ringRef.current.rotation.z = t * 0.5
      ringRef.current.material.opacity = 0.3 + Math.sin(t * 2 + phase) * 0.2
    }
  })

  return (
    <group position={[x, y, 0]}>
      {/* Main dot */}
      <mesh ref={meshRef}>
        <circleGeometry args={[size, isKey ? 32 : 16]} />
        <meshStandardMaterial
          color={isKey ? "#ffffff" : "#10b981"}
          emissive={isKey ? "#34d399" : "#10b981"}
          emissiveIntensity={isKey ? 3 : 1.5}
        />
      </mesh>

      {/* Outer glow */}
      <mesh ref={glowRef}>
        <circleGeometry args={[size * 2.5, 32]} />
        <meshBasicMaterial color="#34d399" transparent opacity={0.25} />
      </mesh>

      {/* Ring for key nodes */}
      {isKey && (
        <mesh ref={ringRef}>
          <ringGeometry args={[size * 1.4, size * 1.6, 32]} />
          <meshBasicMaterial color="#6ee7b7" transparent opacity={0.4} />
        </mesh>
      )}
    </group>
  )
}

// Circuit trace component (line with traveling pulse)
function CircuitTrace({ startNode, endNode, isMain, pulseOffset, pulseSpeed }) {
  const lineRef = useRef()
  const pulseRef = useRef()

  const { points, pathLength } = useMemo(() => {
    const start = new THREE.Vector3(startNode.x, startNode.y, 0)
    const end = new THREE.Vector3(endNode.x, endNode.y, 0)
    const pts = [start, end]
    const len = start.distanceTo(end)
    return { points: pts, pathLength: len }
  }, [startNode, endNode])

  const geometry = useMemo(() => {
    return new THREE.BufferGeometry().setFromPoints(points)
  }, [points])

  useFrame((state) => {
    const t = state.clock.elapsedTime

    if (lineRef.current) {
      const basePulse = 0.15 + Math.sin(t * 1.5 + pulseOffset * 10) * 0.1
      lineRef.current.material.opacity = isMain ? basePulse + 0.15 : basePulse
    }

    if (pulseRef.current) {
      const progress = (t * pulseSpeed + pulseOffset) % 1
      const pos = new THREE.Vector3().lerpVectors(points[0], points[1], progress)
      pulseRef.current.position.copy(pos)
      pulseRef.current.material.opacity = 0.5 + Math.sin(progress * Math.PI) * 0.5
    }
  })

  return (
    <group>
      <line ref={lineRef} geometry={geometry}>
        <lineBasicMaterial
          color={isMain ? "#6ee7b7" : "#34d399"}
          transparent
          opacity={isMain ? 0.35 : 0.2}
        />
      </line>
      {/* Traveling pulse dot */}
      <mesh ref={pulseRef}>
        <circleGeometry args={[isMain ? 0.025 : 0.015, 8]} />
        <meshStandardMaterial
          color="#ffffff"
          emissive="#6ee7b7"
          emissiveIntensity={5}
          transparent
          opacity={0.8}
        />
      </mesh>
    </group>
  )
}

// Brain outline
function BrainOutline() {
  const outlineRef = useRef()
  const foldRef = useRef()

  const outlineGeometry = useMemo(() => {
    const points = BRAIN_OUTLINE.map(
      ([x, y]) => new THREE.Vector3((x - 0.5) * 3.2, (y - 0.5) * 3.2, 0)
    )
    return new THREE.BufferGeometry().setFromPoints(points)
  }, [])

  const foldGeometry = useMemo(() => {
    const points = BRAIN_FOLD.map(
      ([x, y]) => new THREE.Vector3((x - 0.5) * 3.2, (y - 0.5) * 3.2, 0)
    )
    return new THREE.BufferGeometry().setFromPoints(points)
  }, [])

  useFrame((state) => {
    const t = state.clock.elapsedTime
    const pulse = 0.5 + Math.sin(t * 0.5) * 0.15

    if (outlineRef.current) {
      outlineRef.current.material.opacity = pulse
    }
    if (foldRef.current) {
      foldRef.current.material.opacity = pulse * 0.6
    }
  })

  return (
    <group>
      {/* Main outline */}
      <line ref={outlineRef} geometry={outlineGeometry}>
        <lineBasicMaterial color="#34d399" transparent opacity={0.5} />
      </line>
      {/* Central fold */}
      <line ref={foldRef} geometry={foldGeometry}>
        <lineBasicMaterial color="#34d399" transparent opacity={0.3} />
      </line>
    </group>
  )
}

// Main circuit brain scene
function CircuitBrainScene() {
  const groupRef = useRef()
  const mouse = useRef({ x: 0, y: 0 })

  const nodes = useMemo(() => generateCircuitNodes(50), [])
  const traces = useMemo(() => generateCircuitTraces(nodes), [nodes])

  useEffect(() => {
    const handleMouseMove = (e) => {
      mouse.current.x = (e.clientX / window.innerWidth) * 2 - 1
      mouse.current.y = -(e.clientY / window.innerHeight) * 2 + 1
    }
    window.addEventListener("mousemove", handleMouseMove)
    return () => window.removeEventListener("mousemove", handleMouseMove)
  }, [])

  useFrame(() => {
    if (groupRef.current) {
      const targetY = mouse.current.x * 0.12
      const targetX = mouse.current.y * 0.08

      groupRef.current.rotation.y += (targetY - groupRef.current.rotation.y) * 0.03
      groupRef.current.rotation.x += (targetX - groupRef.current.rotation.x) * 0.03
    }
  })

  return (
    <group ref={groupRef}>
      <BrainOutline />

      {traces.map((trace, i) => (
        <CircuitTrace
          key={`trace-${i}`}
          startNode={nodes[trace.from]}
          endNode={nodes[trace.to]}
          isMain={trace.isMain}
          pulseOffset={trace.pulseOffset}
          pulseSpeed={trace.pulseSpeed}
        />
      ))}

      {nodes.map((node, i) => (
        <CircuitNode
          key={`node-${i}`}
          x={node.x}
          y={node.y}
          size={node.size}
          isKey={node.isKey}
          phase={node.phase}
          pulseSpeed={node.pulseSpeed}
        />
      ))}

      <ambientLight intensity={0.3} />
      <pointLight position={[0, 0, 3]} color="#34d399" intensity={0.8} />
    </group>
  )
}

// Main exported component
export default function CortexLogo({ size = 128 }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: "absolute",
          inset: "-40%",
          background:
            "radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, transparent 55%)",
          filter: "blur(20px)",
          pointerEvents: "none",
        }}
      />

      <Canvas
        camera={{ position: [0, 0, 4], fov: 45 }}
        style={{ background: "transparent" }}
        gl={{ alpha: true, antialias: true }}
      >
        <CircuitBrainScene />

        <EffectComposer>
          <Bloom
            intensity={1.8}
            luminanceThreshold={0.15}
            luminanceSmoothing={0.9}
            mipmapBlur
          />
        </EffectComposer>
      </Canvas>
    </div>
  )
}
