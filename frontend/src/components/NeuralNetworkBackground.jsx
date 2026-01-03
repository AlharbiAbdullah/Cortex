import React, { useEffect, useRef } from 'react'

function NeuralNetworkBackground({ className = '' }) {
  const canvasRef = useRef(null)
  const animationRef = useRef()
  const nodesRef = useRef([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    let width = 0
    let height = 0

    const createNodes = () => {
      const area = Math.max(width * height, 1)
      const desired = Math.max(224, Math.min(560, Math.floor(area / 3250)))
      nodesRef.current = Array.from({ length: desired }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.15,
        vy: (Math.random() - 0.5) * 0.15,
        r: 1.6 + Math.random() * 1.6
      }))
    }

    const resize = () => {
      width = canvas.offsetWidth
      height = canvas.offsetHeight
      canvas.width = width * dpr
      canvas.height = height * dpr
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      createNodes()
    }

    const draw = () => {
      const nodes = nodesRef.current
      ctx.clearRect(0, 0, width, height)

      // subtle fade for motion trails
      ctx.fillStyle = 'rgba(12, 22, 18, 0.22)'
      ctx.fillRect(0, 0, width, height)

      const maxDist = 170
      const drift = 0.003

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i]

        n.vx += (Math.random() - 0.5) * drift
        n.vy += (Math.random() - 0.5) * drift

        n.x += n.vx
        n.y += n.vy

        if (n.x < 0 || n.x > width) n.vx *= -1
        if (n.y < 0 || n.y > height) n.vy *= -1

        // dotted nodes (no shadowBlur for performance)
        ctx.beginPath()
        ctx.fillStyle = 'rgba(74, 222, 128, 0.85)'
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
        ctx.fill()
      }

      // connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i]
          const b = nodes[j]
          const dx = a.x - b.x
          const dy = a.y - b.y
          const dist = Math.hypot(dx, dy)

          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.35
            ctx.strokeStyle = `rgba(52, 211, 153, ${alpha})`
            ctx.lineWidth = 0.8
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.stroke()
          }
        }
      }

      animationRef.current = requestAnimationFrame(draw)
    }

    resize()
    window.addEventListener('resize', resize)
    animationRef.current = requestAnimationFrame(draw)

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className={`pointer-events-none absolute inset-0 block w-full h-full ${className}`}
      style={{ willChange: 'contents', transform: 'translateZ(0)', isolation: 'isolate' }}
    />
  )
}

export default NeuralNetworkBackground
