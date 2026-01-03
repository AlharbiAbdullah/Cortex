import React from 'react'
import { Link } from 'react-router-dom'
import { FiArrowLeft } from 'react-icons/fi'
import ChatInterface from '../components/ChatInterface'

function ChatPage() {
  return (
    <div className="h-full flex flex-col relative">
      {/* Header */}
      <header className="px-6 py-4 flex-shrink-0 z-20 relative">
        <div className="flex items-center justify-between">
          <Link
            to="/ai"
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

          <div className="w-20" />
        </div>
      </header>

      {/* Main Chat Area */}
      <div className="flex-1 overflow-hidden relative z-10">
        <ChatInterface />
      </div>
    </div>
  )
}

export default ChatPage
