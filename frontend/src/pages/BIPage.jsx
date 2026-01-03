import React, { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FiArrowLeft, FiGrid, FiDatabase, FiArrowRight, FiChevronLeft, FiChevronRight } from 'react-icons/fi'
import NeuralNetworkBackground from '../components/NeuralNetworkBackground'

const BI_SERVICES = [
  {
    id: 'dashboard',
    name: 'Dashboards',
    description: 'Interactive KPI dashboards powered by Apache Superset',
    icon: FiGrid,
    path: '/bi/dashboard'
  },
  {
    id: 'self-service',
    name: 'Self-Service Analytics',
    description: 'Ad-hoc queries and data exploration with Dremio',
    icon: FiDatabase,
    path: '/bi/selfservice'
  },
]

function BIPage() {
  const navigate = useNavigate()
  const servicesRef = useRef(null)

  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

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
          className="group inline-flex items-center gap-2 text-sm text-emerald-300/70 hover:text-emerald-200 transition-colors py-2 px-4 rounded-xl hover:bg-white/5"
        >
          <FiArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
          Back
        </Link>
      </div>

      {/* Logo and Title */}
      <div className="text-center mb-8 relative z-10">
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-500/20 blur-3xl rounded-full scale-150" />
            <div className="relative w-32 h-32 rounded-full bg-gradient-to-br from-emerald-400/30 to-emerald-600/30 flex items-center justify-center">
              <span className="text-6xl font-bold text-emerald-400/90 drop-shadow-2xl">C</span>
            </div>
          </div>
        </div>

        <h1 className="text-5xl md:text-7xl font-semibold tracking-tight">
          <span className="bg-gradient-to-r from-emerald-200/90 via-teal-100/70 to-white/60 bg-clip-text text-transparent">
            CortexBI
          </span>
        </h1>
        <p className="mt-3 text-xl text-emerald-50/50">Business Intelligence Services</p>
      </div>

      {/* Services Section */}
      <div className="w-full max-w-4xl relative z-10">
        <div className="flex items-center justify-center gap-4">
          {/* Left Arrow */}
          <button
            onClick={() => scrollServices('left')}
            className={`flex-shrink-0 w-12 h-12 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 flex items-center justify-center transition-all duration-300 hover:border-emerald-500/40 hover:bg-emerald-500/10 ${
              canScrollLeft ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
          >
            <FiChevronLeft className="w-6 h-6" />
          </button>

          {/* Services Container */}
          <div
            ref={servicesRef}
            className="flex gap-4 overflow-x-hidden justify-center"
            onScroll={updateScrollButtons}
          >
            {BI_SERVICES.map((service) => (
              <button
                key={service.id}
                onClick={() => handleServiceClick(service)}
                className="flex-shrink-0 group flex flex-col items-start gap-2 p-5 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 text-left transition-all duration-300 hover:border-emerald-500/40 hover:bg-emerald-500/10"
                style={{ width: '220px' }}
              >
                <div className="flex items-center gap-3 w-full">
                  <service.icon className="w-6 h-6 text-emerald-400" />
                  <span className="text-white font-semibold">{service.name}</span>
                  <FiArrowRight className="w-4 h-4 ml-auto text-emerald-400 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
                </div>
                <p className="text-sm text-emerald-50/50 leading-relaxed">{service.description}</p>
              </button>
            ))}
          </div>

          {/* Right Arrow */}
          <button
            onClick={() => scrollServices('right')}
            className={`flex-shrink-0 w-12 h-12 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 flex items-center justify-center transition-all duration-300 hover:border-emerald-500/40 hover:bg-emerald-500/10 ${
              canScrollRight ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
          >
            <FiChevronRight className="w-6 h-6" />
          </button>
        </div>
      </div>

    </div>
  )
}

export default BIPage
