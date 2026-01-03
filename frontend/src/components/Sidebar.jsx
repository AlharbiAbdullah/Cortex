import React from 'react'
import { NavLink, Link } from 'react-router-dom'
import { FiMessageSquare, FiUpload, FiHome } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'

function Sidebar() {
  const navItems = [
    {
      to: '/chat',
      icon: FiMessageSquare,
      label: 'Chat'
    },
    {
      to: '/upload',
      icon: FiUpload,
      label: 'Upload'
    }
  ]

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
            <h1 className="font-bold text-white text-lg tracking-tight">
              Cortex
            </h1>
            <p className="text-xs text-emerald-50/40">Document Intelligence</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        <Link
          to="/"
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-emerald-50/50 hover:text-white hover:bg-white/5 transition-all"
        >
          <FiHome className="w-5 h-5" />
          <span className="font-medium text-sm">Home</span>
        </Link>

        <div className="pt-2 pb-1 px-4">
          <span className="text-xs font-medium text-emerald-50/30 uppercase tracking-wider">
            Workspace
          </span>
        </div>

        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? 'bg-emerald-500/10 text-white border border-emerald-500/20'
                  : 'text-emerald-50/50 hover:text-white hover:bg-white/5 border border-transparent'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium text-sm">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/5">
        <div className="flex items-center justify-between text-xs text-emerald-50/30">
          <span>RAG Enabled</span>
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
