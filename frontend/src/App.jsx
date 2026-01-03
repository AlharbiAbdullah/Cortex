import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import LandingPage from './pages/LandingPage'
import ChatPage from './pages/ChatPage'
import NeuralNetworkBackground from './components/NeuralNetworkBackground'

function AppLayout() {
  const location = useLocation()
  const isLandingStyle = ['/', '/chat'].includes(location.pathname)
  const isChatStyle = ['/chat'].includes(location.pathname)

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0c1612] text-[#e7f0e7]">
      <div className="aurora-bg" />
      <div className="floating-orb orb-1" />
      <div className="floating-orb orb-2" />
      <div className="floating-orb orb-3" />
      <div className="grid-overlay" />
      {isLandingStyle && !isChatStyle && <NeuralNetworkBackground className="opacity-60" />}

      <div
        className={`relative z-10 h-screen px-4 py-5 md:px-6 md:py-7 ${
          isLandingStyle ? 'flex justify-center' : 'flex gap-4 md:gap-6'
        }`}
      >
        {!isLandingStyle && <Sidebar />}

        <main className={`flex-1 overflow-hidden ${isLandingStyle ? 'max-w-6xl' : ''}`}>
          <div
            className={`h-full rounded-3xl ${
              isLandingStyle
                ? (isChatStyle ? 'overflow-hidden' : 'overflow-auto')
                : 'glass-panel border border-white/5 shadow-2xl overflow-hidden'
            }`}
          >
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  )
}

function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  )
}

export default App
