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
import { HiOutlineSparkles } from 'react-icons/hi2'

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
        `flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all ${
          isActive
            ? 'bg-emerald-500/10 text-white border border-emerald-500/20'
            : 'text-emerald-50/50 hover:text-white hover:bg-white/5 border border-transparent'
        }`
      }
    >
      <item.icon className="w-4 h-4" />
      <span className="font-medium text-sm">{item.label}</span>
    </NavLink>
  )

  return (
    <aside className="w-64 md:w-72 flex flex-col h-full rounded-3xl border border-white/5 shadow-2xl bg-[#0f1c16]/60 backdrop-blur-sm">
      {/* Logo */}
      <div className="p-5 border-b border-white/5">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-500/30 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <HiOutlineSparkles className="w-5 h-5 text-white" />
            </div>
          </div>
          <div>
            <h1 className="font-bold text-white text-lg tracking-tight">Cortex</h1>
            <p className="text-xs text-emerald-50/40">Enterprise Intelligence</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <Link
          to="/"
          className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-emerald-50/50 hover:text-white hover:bg-white/5 transition-all"
        >
          <FiHome className="w-4 h-4" />
          <span className="font-medium text-sm">Home</span>
        </Link>

        {/* BI Platform */}
        <div className="pt-4 pb-2 px-4">
          <span className="text-xs font-medium text-emerald-50/30 uppercase tracking-wider">
            BI Platform
          </span>
        </div>
        {biServices.map((item) => (
          <NavItem key={item.to} item={item} />
        ))}

        {/* AI Platform */}
        <div className="pt-4 pb-2 px-4">
          <span className="text-xs font-medium text-emerald-50/30 uppercase tracking-wider">
            AI Platform
          </span>
        </div>
        {aiServices.map((item) => (
          <NavItem key={item.to} item={item} />
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/5">
        <div className="flex items-center justify-between text-xs text-emerald-50/30">
          <span>All Services</span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Active
          </span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
