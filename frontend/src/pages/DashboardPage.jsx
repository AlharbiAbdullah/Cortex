import React, { useState, useEffect } from 'react'
import { FiTrendingUp, FiFileText, FiCpu, FiActivity, FiPieChart, FiBarChart2 } from 'react-icons/fi'

function DashboardPage() {
  const [stats, setStats] = useState({
    totalDocuments: 0,
    processedToday: 0,
    avgConfidence: 0,
    activeJobs: 0
  })
  const [recentActivity, setRecentActivity] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [docsRes, jobsRes] = await Promise.all([
        fetch('http://localhost:8000/api/documents').catch(() => ({ ok: false })),
        fetch('http://localhost:8000/api/upload/jobs').catch(() => ({ ok: false }))
      ])

      if (docsRes.ok) {
        const docs = await docsRes.json()
        setStats(prev => ({
          ...prev,
          totalDocuments: docs.length || 0
        }))
        setRecentActivity(docs.slice(0, 5))
      }

      if (jobsRes.ok) {
        const jobs = await jobsRes.json()
        const activeJobs = jobs.filter(j => j.status === 'processing').length
        const todayJobs = jobs.filter(j => {
          const jobDate = new Date(j.created_at)
          const today = new Date()
          return jobDate.toDateString() === today.toDateString()
        }).length
        setStats(prev => ({
          ...prev,
          activeJobs,
          processedToday: todayJobs
        }))
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const statCards = [
    {
      label: 'Total Documents',
      value: stats.totalDocuments,
      icon: FiFileText,
      iconColor: '#8ec07c',
      bgColor: 'rgba(142, 192, 124, 0.15)'
    },
    {
      label: 'Processed Today',
      value: stats.processedToday,
      icon: FiTrendingUp,
      iconColor: '#83a598',
      bgColor: 'rgba(131, 165, 152, 0.15)'
    },
    {
      label: 'Active Jobs',
      value: stats.activeJobs,
      icon: FiCpu,
      iconColor: '#fabd2f',
      bgColor: 'rgba(250, 189, 47, 0.15)'
    },
    {
      label: 'System Status',
      value: 'Healthy',
      icon: FiActivity,
      iconColor: '#b8bb26',
      bgColor: 'rgba(184, 187, 38, 0.15)'
    }
  ]

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Dashboard</h1>
        <p style={{ color: 'var(--text-muted)' }}>Overview of your Cortex platform</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat, index) => (
          <div
            key={index}
            className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 hover:bg-white/[0.04] transition-colors"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 rounded-xl" style={{ background: stat.bgColor }}>
                <stat.icon className="w-5 h-5" style={{ color: stat.iconColor }} />
              </div>
            </div>
            <div className="text-2xl font-bold text-white mb-1">
              {loading ? '...' : stat.value}
            </div>
            <div className="text-sm" style={{ color: 'var(--text-muted)' }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents */}
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg" style={{ background: 'var(--accent-muted)' }}>
              <FiFileText className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            </div>
            <h2 className="text-lg font-semibold text-white">Recent Documents</h2>
          </div>

          {loading ? (
            <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>Loading...</div>
          ) : recentActivity.length > 0 ? (
            <div className="space-y-3">
              {recentActivity.map((doc, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--accent-muted)' }}>
                      <FiFileText className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                    </div>
                    <div>
                      <div className="text-sm font-medium truncate max-w-[200px]" style={{ color: 'var(--text-primary)' }}>
                        {doc.original_filename || doc.filename || 'Document'}
                      </div>
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        {doc.category || 'Processing...'}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {doc.confidence ? `${(doc.confidence * 100).toFixed(0)}%` : '-'}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
              No documents uploaded yet
            </div>
          )}
        </div>

        {/* Platform Services */}
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <FiPieChart className="w-5 h-5 text-blue-400" />
            </div>
            <h2 className="text-lg font-semibold text-white">Platform Services</h2>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { name: 'RAG Chat', status: 'Active' },
              { name: 'Smart Router', status: 'Active' },
              { name: 'Summarization', status: 'Active' },
              { name: 'Comparison', status: 'Active' },
              { name: 'Reports', status: 'Active' },
              { name: 'Data Quality', status: 'Active' }
            ].map((service, index) => (
              <div
                key={index}
                className="p-3 rounded-xl transition-colors"
                style={{ background: 'var(--card-bg)' }}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{service.name}</span>
                  <span className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--accent)' }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--accent)' }} />
                    {service.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
