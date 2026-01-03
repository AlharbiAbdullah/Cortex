import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import NeuralNetworkBackground from './components/NeuralNetworkBackground'

// Pages
import LandingPage from './pages/LandingPage'
import AIPage from './pages/AIPage'
import BIPage from './pages/BIPage'
import BIDashboardPage from './pages/BIDashboardPage'
import BISelfServicePage from './pages/BISelfServicePage'
import ChatPage from './pages/ChatPage'
import SummarizationPage from './pages/SummarizationPage'
import DataQualityPage from './pages/DataQualityPage'
import ExtractPage from './pages/ExtractPage'
import AnalyticsPage from './pages/AnalyticsPage'

function AppLayout() {
  const location = useLocation()
  const isLandingPage = location.pathname === '/'

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0c1612] text-[#e7f0e7]">
      <div className="aurora-bg" />
      <div className="floating-orb orb-1" />
      <div className="floating-orb orb-2" />
      <div className="floating-orb orb-3" />
      <div className="grid-overlay" />
      {isLandingPage && <NeuralNetworkBackground className="opacity-60" />}

      <div className="relative z-10 h-screen">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/ai" element={<AIPage />} />
          <Route path="/ai/chat" element={<ChatPage />} />
          <Route path="/ai/analytics" element={<AnalyticsPage />} />
          <Route path="/ai/summarize" element={<SummarizationPage />} />
          <Route path="/ai/quality" element={<DataQualityPage />} />
          <Route path="/ai/extract" element={<ExtractPage />} />
          <Route path="/bi" element={<BIPage />} />
          <Route path="/bi/dashboard" element={<BIDashboardPage />} />
          <Route path="/bi/selfservice" element={<BISelfServicePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
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
