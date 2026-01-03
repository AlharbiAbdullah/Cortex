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

    // Get theme colors from CSS variables
    const getThemeColors = () => {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
      if (isDark) {
        return {
          trail: 'rgba(40, 40, 40, 0.22)',
          node: 'rgba(191, 168, 122, 0.85)',
          connection: [191, 168, 122]
        }
      } else {
        return {
          trail: 'rgba(191, 168, 122, 0.22)',
          node: 'rgba(40, 40, 40, 0.85)',
          connection: [40, 40, 40]
        }
      }
    }

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
      const colors = getThemeColors()
      ctx.clearRect(0, 0, width, height)

      // subtle fade for motion trails
      ctx.fillStyle = colors.trail
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

        // dotted nodes
        ctx.beginPath()
        ctx.fillStyle = colors.node
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
        ctx.fill()
      }

      // connections
      const [r, g, b] = colors.connection
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i]
          const bNode = nodes[j]
          const dx = a.x - bNode.x
          const dy = a.y - bNode.y
          const dist = Math.hypot(dx, dy)

          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.35
            ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`
            ctx.lineWidth = 0.8
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(bNode.x, bNode.y)
            ctx.stroke()
          }
        }
      }

      animationRef.current = requestAnimationFrame(draw)
    }

    resize()
    window.addEventListener('resize', resize)
    animationRef.current = requestAnimationFrame(draw)

    // Listen for theme changes
    const observer = new MutationObserver(() => {
      // Theme changed, colors will update on next frame
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
      window.removeEventListener('resize', resize)
      observer.disconnect()
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
