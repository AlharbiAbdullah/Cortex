import React from 'react'
import { Link } from 'react-router-dom'
import { FiCpu, FiBarChart2, FiArrowRight } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'

function LandingPage() {
  return (
    <div className="relative h-full overflow-hidden flex flex-col items-center justify-center px-6">
      {/* Logo and Title */}
      <div className="text-center mb-12">
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-500/20 blur-3xl rounded-full scale-150" />
            <div className="relative w-32 h-32 rounded-full bg-gradient-to-br from-emerald-400/30 to-emerald-600/30 flex items-center justify-center">
              <span className="text-6xl font-bold text-emerald-400/90 drop-shadow-2xl">C</span>
            </div>
          </div>
        </div>

        <h1 className="text-5xl md:text-7xl font-semibold tracking-tight">
          <span className="bg-gradient-to-r from-emerald-200/90 via-emerald-100/70 to-white/60 bg-clip-text text-transparent">
            Cortex
          </span>
        </h1>
        <p className="mt-3 text-xl text-emerald-50/50">Enterprise Intelligence Platform</p>
      </div>

      {/* Platform Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl w-full">
        {/* AI Platform */}
        <Link
          to="/ai"
          className="group relative overflow-hidden rounded-3xl border border-purple-500/20 bg-gradient-to-br from-purple-500/10 to-purple-600/5 p-8 transition-all duration-300 hover:border-purple-500/40 hover:from-purple-500/20 hover:to-purple-600/10 hover:scale-[1.02]"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-purple-500/20 transition-colors" />

          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-purple-500/20 flex items-center justify-center mb-6">
              <HiOutlineSparkles className="w-8 h-8 text-purple-400" />
            </div>

            <h2 className="text-3xl font-bold text-white mb-3">AI Platform</h2>
            <p className="text-purple-200/60 mb-6">
              Smart services powered by AI: RAG Chat, Document Summarization,
              Comparison, Data Quality Assessment
            </p>

            <div className="flex items-center gap-2 text-purple-400 font-medium">
              <span>Enter AI Platform</span>
              <FiArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-2" />
            </div>
          </div>
        </Link>

        {/* BI Platform */}
        <Link
          to="/bi"
          className="group relative overflow-hidden rounded-3xl border border-blue-500/20 bg-gradient-to-br from-blue-500/10 to-blue-600/5 p-8 transition-all duration-300 hover:border-blue-500/40 hover:from-blue-500/20 hover:to-blue-600/10 hover:scale-[1.02]"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-blue-500/20 transition-colors" />

          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-blue-500/20 flex items-center justify-center mb-6">
              <FiBarChart2 className="w-8 h-8 text-blue-400" />
            </div>

            <h2 className="text-3xl font-bold text-white mb-3">BI Platform</h2>
            <p className="text-blue-200/60 mb-6">
              Business Intelligence tools: Interactive Dashboards,
              Self-Service Analytics, Report Generation
            </p>

            <div className="flex items-center gap-2 text-blue-400 font-medium">
              <span>Enter BI Platform</span>
              <FiArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-2" />
            </div>
          </div>
        </Link>
      </div>

      {/* Footer */}
      <div className="mt-12 text-center">
        <p className="text-emerald-50/30 text-sm">
          Unified BI dashboards, self-service analytics, and AI-powered smart services
        </p>
      </div>
    </div>
  )
}

export default LandingPage
