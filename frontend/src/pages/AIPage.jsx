import React, { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FiArrowLeft, FiMessageSquare, FiZap, FiCheckCircle, FiFileText, FiArrowRight, FiChevronLeft, FiChevronRight, FiBarChart2 } from 'react-icons/fi'
import NeuralNetworkBackground from '../components/NeuralNetworkBackground'

const AI_SERVICES = [
  { id: 'chat', name: 'Chat', description: 'Chat with your documents using AI-powered retrieval', icon: FiMessageSquare, path: '/ai/chat' },
  { id: 'analytics', name: 'Conversational Analytics', description: 'Ask about graphs, charts, ML insights and data analytics', icon: FiBarChart2, path: '/ai/analytics' },
  { id: 'summarize', name: 'Summarize', description: 'Drop a document or ask to summarize topics from your data', icon: FiZap, path: '/ai/summarize' },
  { id: 'quality', name: 'Data Quality', description: 'Ask quality measures for datasets, tables, or categories', icon: FiCheckCircle, path: '/ai/quality' },
  { id: 'extract', name: 'Extract', description: 'Drop a file or request data in any format (JSON, CSV, etc.)', icon: FiFileText, path: '/ai/extract' },
]

function AIPage() {
  const servicesRef = useRef(null)
  const navigate = useNavigate()

  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(true)

  const updateScrollButtons = () => {
    if (servicesRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = servicesRef.current
      setCanScrollLeft(scrollLeft > 0)
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1)
    }
  }

  useEffect(() => {
    updateScrollButtons()
  }, [])

  const handleServiceClick = (service) => {
    navigate(service.path)
  }

  const scrollServices = (direction) => {
    if (servicesRef.current) {
      const scrollAmount = 236 // card width (220px) + gap (16px)
      servicesRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      })
      // Update button visibility after scroll animation
      setTimeout(updateScrollButtons, 300)
    }
  }

  return (
    <div className="relative h-full overflow-hidden flex flex-col items-center justify-center px-6">
      {/* Neural Network Background */}
      <NeuralNetworkBackground className="opacity-60" />

      {/* Back Button */}
      <div className="absolute top-6 left-6 z-20">
        <Link
          to="/"
          className="group inline-flex items-center gap-2 text-sm transition-colors py-2 px-4 rounded-xl"
          style={{ color: 'var(--text-muted)' }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--text-primary)'
            e.currentTarget.style.background = 'var(--card-bg)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-muted)'
            e.currentTarget.style.background = 'transparent'
          }}
        >
          <FiArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
          Back
        </Link>
      </div>

      {/* Title */}
      <div className="text-center mb-8 relative z-10">
        <h1 className="text-5xl md:text-7xl font-semibold tracking-tight" style={{ color: 'var(--accent)' }}>
          CortexAI
        </h1>
        <p className="mt-3 text-xl" style={{ color: 'var(--text-muted)' }}>AI-Powered Intelligence Services</p>
      </div>

      {/* Services Section */}
      <div className="w-full max-w-4xl relative z-10">
        <div className="flex items-center gap-4">
          {/* Left Arrow */}
          <button
            onClick={() => scrollServices('left')}
            className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${
              canScrollLeft ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
            style={{
              border: '1px solid var(--border-color)',
              background: 'var(--card-bg)',
              color: 'var(--accent)'
            }}
          >
            <FiChevronLeft className="w-6 h-6" />
          </button>

          {/* Services Container - shows 3 at a time */}
          <div
            ref={servicesRef}
            className="flex gap-4 overflow-x-hidden"
            style={{ width: 'calc(3 * 220px + 2 * 16px)' }}
          >
            {AI_SERVICES.map((service) => (
              <button
                key={service.id}
                onClick={() => handleServiceClick(service)}
                className="flex-shrink-0 group flex flex-col items-start gap-2 p-5 rounded-2xl text-left transition-all duration-300"
                style={{
                  width: '220px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--card-bg)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent)'
                  e.currentTarget.style.background = 'var(--card-hover)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color)'
                  e.currentTarget.style.background = 'var(--card-bg)'
                }}
              >
                <div className="flex items-center gap-3 w-full">
                  <service.icon className="w-6 h-6" style={{ color: 'var(--accent)' }} />
                  <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{service.name}</span>
                  <FiArrowRight className="w-4 h-4 ml-auto opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" style={{ color: 'var(--accent)' }} />
                </div>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{service.description}</p>
              </button>
            ))}
          </div>

          {/* Right Arrow */}
          <button
            onClick={() => scrollServices('right')}
            className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${
              canScrollRight ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
            style={{
              border: '1px solid var(--border-color)',
              background: 'var(--card-bg)',
              color: 'var(--accent)'
            }}
          >
            <FiChevronRight className="w-6 h-6" />
          </button>
        </div>
      </div>

    </div>
  )
}

export default AIPage
