import React from 'react'
import { NavLink, Link } from 'react-router-dom'
import {
  FiHome,
  FiGrid,
  FiFileText,
  FiMessageSquare,
  FiZap,
  FiGitMerge,
  FiBarChart2,
  FiCheckCircle
} from 'react-icons/fi'

function Sidebar() {
  const biServices = [
    { to: '/dashboard', icon: FiGrid, label: 'Dashboard' },
    { to: '/documents', icon: FiFileText, label: 'Documents' },
    { to: '/reports', icon: FiBarChart2, label: 'Reports' }
  ]

  const aiServices = [
    { to: '/chat', icon: FiMessageSquare, label: 'RAG Chat' },
    { to: '/summarize', icon: FiZap, label: 'Summarization' },
    { to: '/compare', icon: FiGitMerge, label: 'Comparison' },
    { to: '/quality', icon: FiCheckCircle, label: 'Data Quality' }
  ]

  const NavItem = ({ item }) => (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all border`
      }
      style={({ isActive }) => ({
        background: isActive ? 'var(--accent-muted)' : 'transparent',
        color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
        borderColor: isActive ? 'var(--border-color)' : 'transparent'
      })}
    >
      <item.icon className="w-4 h-4" />
      <span className="font-medium text-sm">{item.label}</span>
    </NavLink>
  )

  return (
    <aside className="w-64 md:w-72 flex flex-col h-full rounded-3xl shadow-2xl backdrop-blur-sm" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
      {/* Logo */}
      <div className="p-5" style={{ borderBottom: '1px solid var(--border-color)' }}>
        <Link to="/" className="block">
          <h1 className="font-bold text-2xl tracking-tight" style={{ color: 'var(--color-text)' }}>Cortex</h1>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <Link
          to="/"
          className="flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all"
          style={{ color: 'var(--text-muted)' }}
        >
          <FiHome className="w-4 h-4" />
          <span className="font-medium text-sm">Home</span>
        </Link>

        {/* BI Platform */}
        <div className="pt-4 pb-2 px-4">
          <span className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            BI Platform
          </span>
        </div>
        {biServices.map((item) => (
          <NavItem key={item.to} item={item} />
        ))}

        {/* AI Platform */}
        <div className="pt-4 pb-2 px-4">
          <span className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            AI Platform
          </span>
        </div>
        {aiServices.map((item) => (
          <NavItem key={item.to} item={item} />
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4" style={{ borderTop: '1px solid var(--border-color)' }}>
        <div className="flex items-center justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
          <span>All Services</span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--accent)' }} />
            Active
          </span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
