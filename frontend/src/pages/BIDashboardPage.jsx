import React from 'react'
import { Link } from 'react-router-dom'
import { FiArrowLeft, FiGrid, FiExternalLink } from 'react-icons/fi'

function BIDashboardPage() {
  const supersetUrl = 'http://localhost:8088'

  return (
    <div className="relative h-full overflow-hidden flex flex-col bg-[#0c1612]">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-emerald-500/10">
        <div className="flex items-center gap-4">
          <Link
            to="/bi"
            className="group inline-flex items-center gap-2 text-sm text-emerald-300/70 hover:text-emerald-200 transition-colors py-2 px-3 rounded-lg hover:bg-white/5"
          >
            <FiArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
            Back
          </Link>
          <div className="h-6 w-px bg-emerald-500/20" />
          <div className="flex items-center gap-2">
            <FiGrid className="w-5 h-5 text-emerald-400" />
            <h1 className="text-lg font-semibold text-white">Dashboards</h1>
          </div>
        </div>
        <a
          href={supersetUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm text-emerald-300/70 hover:text-emerald-200 transition-colors py-2 px-3 rounded-lg hover:bg-white/5"
        >
          Open in new tab
          <FiExternalLink className="w-4 h-4" />
        </a>
      </div>

      {/* Embedded Superset */}
      <div className="flex-1 relative">
        <iframe
          src={supersetUrl}
          title="Apache Superset Dashboards"
          className="absolute inset-0 w-full h-full border-0"
          allow="fullscreen"
        />
      </div>
    </div>
  )
}

export default BIDashboardPage
