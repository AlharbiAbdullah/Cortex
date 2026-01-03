import React from 'react'
import { Link } from 'react-router-dom'
import { FiArrowLeft, FiDatabase, FiExternalLink } from 'react-icons/fi'

function BISelfServicePage() {
  const dremioUrl = 'http://localhost:9047'

  return (
    <div className="relative h-full overflow-hidden flex flex-col" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: '1px solid var(--border-color)' }}>
        <div className="flex items-center gap-4">
          <Link
            to="/bi"
            className="group inline-flex items-center gap-2 text-sm transition-colors py-2 px-3 rounded-lg"
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
          <div className="h-6 w-px" style={{ background: 'var(--border-color)' }} />
          <div className="flex items-center gap-2">
            <FiDatabase className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            <h1 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Self-Service Analytics</h1>
          </div>
        </div>
        <a
          href={dremioUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm transition-colors py-2 px-3 rounded-lg"
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
          Open in new tab
          <FiExternalLink className="w-4 h-4" />
        </a>
      </div>

      {/* Embedded Dremio */}
      <div className="flex-1 relative">
        <iframe
          src={dremioUrl}
          title="Dremio Self-Service Analytics"
          className="absolute inset-0 w-full h-full border-0"
          allow="fullscreen"
        />
      </div>
    </div>
  )
}

export default BISelfServicePage
