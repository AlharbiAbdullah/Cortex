import React from 'react'
import { Link } from 'react-router-dom'
import { FiArrowLeft } from 'react-icons/fi'
import ChatInterface from '../components/ChatInterface'

const EXTRACT_PHRASES = [
  "What format do you need?",
  "Drop a file to convert...",
  "Need data in JSON format?",
  "Which table should I extract?",
  "Want CSV, Excel, or JSON?",
  "Ready to transform your data...",
  "What data should I extract?",
]

function ExtractPage() {
  return (
    <div className="h-full flex flex-col relative">
      {/* Header */}
      <header className="px-6 py-4 flex-shrink-0 z-20 relative">
        <div className="flex items-center justify-between">
          <Link
            to="/ai"
            className="group inline-flex items-center gap-2 text-sm text-emerald-300/70 hover:text-emerald-200 transition-colors py-2 px-4 rounded-xl hover:bg-white/5"
          >
            <FiArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
            Back
          </Link>

          <div className="w-20" />
        </div>
      </header>

      {/* Main Chat Area */}
      <div className="flex-1 overflow-hidden relative z-10">
        <ChatInterface showOptions={false} phrases={EXTRACT_PHRASES} />
      </div>
    </div>
  )
}

export default ExtractPage
