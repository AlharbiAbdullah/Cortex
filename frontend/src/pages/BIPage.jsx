import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { FiArrowLeft, FiGrid, FiDatabase, FiFileText, FiExternalLink } from 'react-icons/fi'

const BI_SERVICES = [
  {
    id: 'dashboard',
    name: 'Dashboards',
    icon: FiGrid,
    description: 'Interactive KPI dashboards powered by Apache Superset',
    embedUrl: 'http://localhost:8088',
    color: 'blue'
  },
  {
    id: 'self-service',
    name: 'Self-Service Analytics',
    icon: FiDatabase,
    description: 'Ad-hoc queries and data exploration with Dremio',
    embedUrl: 'http://localhost:9047',
    color: 'cyan'
  },
]

function BIPage() {
  const [activeService, setActiveService] = useState('dashboard')

  const currentService = BI_SERVICES.find(s => s.id === activeService)

  return (
    <div className="h-full flex">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-white/5 bg-[#0f1c16]/40 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-white/5">
          <Link to="/" className="flex items-center gap-2 text-emerald-50/50 hover:text-white transition-colors">
            <FiArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to Home</span>
          </Link>
        </div>

        {/* Logo */}
        <div className="p-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-600/20 flex items-center justify-center">
              <FiGrid className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="font-bold text-white">BI Platform</h1>
              <p className="text-xs text-blue-300/50">Business Intelligence</p>
            </div>
          </div>
        </div>

        {/* Services */}
        <nav className="flex-1 p-3 space-y-1">
          <div className="px-3 py-2">
            <span className="text-xs font-medium text-emerald-50/30 uppercase tracking-wider">Services</span>
          </div>
          {BI_SERVICES.map((service) => (
            <button
              key={service.id}
              onClick={() => setActiveService(service.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left ${
                activeService === service.id
                  ? 'bg-blue-500/10 text-white border border-blue-500/20'
                  : 'text-emerald-50/50 hover:text-white hover:bg-white/5'
              }`}
            >
              <service.icon className="w-4 h-4" />
              <div>
                <div className="text-sm font-medium">{service.name}</div>
                <div className="text-xs text-emerald-50/30 line-clamp-1">{service.description}</div>
              </div>
            </button>
          ))}
        </nav>

        {/* Quick Links */}
        <div className="p-4 border-t border-white/5">
          <div className="text-xs text-emerald-50/30 mb-2">Direct Access</div>
          <div className="space-y-2">
            <a
              href="http://localhost:8088"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-blue-400/70 hover:text-blue-400 transition-colors"
            >
              <FiExternalLink className="w-3 h-3" />
              Superset
            </a>
            <a
              href="http://localhost:9047"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-cyan-400/70 hover:text-cyan-400 transition-colors"
            >
              <FiExternalLink className="w-3 h-3" />
              Dremio
            </a>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <currentService.icon className="w-5 h-5 text-blue-400" />
            <div>
              <h2 className="font-semibold text-white">{currentService.name}</h2>
              <p className="text-xs text-emerald-50/40">{currentService.description}</p>
            </div>
          </div>
          <a
            href={currentService.embedUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/10 text-blue-400 text-sm hover:bg-blue-500/20 transition-colors"
          >
            <FiExternalLink className="w-4 h-4" />
            Open in new tab
          </a>
        </header>

        {/* Embedded Content */}
        <div className="flex-1 relative">
          <iframe
            src={currentService.embedUrl}
            title={currentService.name}
            className="absolute inset-0 w-full h-full border-0"
            sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals"
          />

          {/* Fallback Message */}
          <div className="absolute inset-0 flex items-center justify-center bg-[#0c1612] pointer-events-none opacity-0 transition-opacity iframe-fallback">
            <div className="text-center">
              <currentService.icon className="w-16 h-16 mx-auto mb-4 text-blue-400/20" />
              <h3 className="text-xl font-medium text-white/80 mb-2">Loading {currentService.name}...</h3>
              <p className="text-emerald-50/40 mb-4">
                If the content doesn't load, the service may not be running.
              </p>
              <a
                href={currentService.embedUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors pointer-events-auto"
              >
                <FiExternalLink className="w-4 h-4" />
                Open directly
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BIPage
