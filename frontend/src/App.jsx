import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import NeuralNetworkBackground from './components/NeuralNetworkBackground'

// Pages
import LandingPage from './pages/LandingPage'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'
import DocumentsPage from './pages/DocumentsPage'
import SummarizationPage from './pages/SummarizationPage'
import ComparisonPage from './pages/ComparisonPage'
import ReportsPage from './pages/ReportsPage'
import DataQualityPage from './pages/DataQualityPage'

function AppLayout() {
  const location = useLocation()
  const isLandingPage = location.pathname === '/'
  const isChatPage = location.pathname === '/chat'

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0c1612] text-[#e7f0e7]">
      <div className="aurora-bg" />
      <div className="floating-orb orb-1" />
      <div className="floating-orb orb-2" />
      <div className="floating-orb orb-3" />
      <div className="grid-overlay" />
      {isLandingPage && <NeuralNetworkBackground className="opacity-60" />}

      <div
        className={`relative z-10 h-screen px-4 py-5 md:px-6 md:py-7 ${
          isLandingPage ? 'flex justify-center' : 'flex gap-4 md:gap-6'
        }`}
      >
        {!isLandingPage && <Sidebar />}

        <main className={`flex-1 overflow-hidden ${isLandingPage ? 'max-w-6xl' : ''}`}>
          <div
            className={`h-full rounded-3xl ${
              isLandingPage
                ? 'overflow-auto'
                : isChatPage
                ? 'overflow-hidden'
                : 'glass-panel border border-white/5 shadow-2xl overflow-hidden'
            }`}
          >
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/summarize" element={<SummarizationPage />} />
              <Route path="/compare" element={<ComparisonPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/quality" element={<DataQualityPage />} />
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
