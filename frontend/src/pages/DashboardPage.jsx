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
      color: 'from-emerald-500 to-emerald-600',
      bgColor: 'bg-emerald-500/10'
    },
    {
      label: 'Processed Today',
      value: stats.processedToday,
      icon: FiTrendingUp,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-500/10'
    },
    {
      label: 'Active Jobs',
      value: stats.activeJobs,
      icon: FiCpu,
      color: 'from-amber-500 to-amber-600',
      bgColor: 'bg-amber-500/10'
    },
    {
      label: 'System Status',
      value: 'Healthy',
      icon: FiActivity,
      color: 'from-green-500 to-green-600',
      bgColor: 'bg-green-500/10'
    }
  ]

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-emerald-50/50">Overview of your Cortex platform</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat, index) => (
          <div
            key={index}
            className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 hover:bg-white/[0.04] transition-colors"
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                <stat.icon className={`w-5 h-5 bg-gradient-to-br ${stat.color} bg-clip-text text-transparent`}
                  style={{ color: stat.color.includes('emerald') ? '#10b981' :
                          stat.color.includes('blue') ? '#3b82f6' :
                          stat.color.includes('amber') ? '#f59e0b' : '#22c55e' }}
                />
              </div>
            </div>
            <div className="text-2xl font-bold text-white mb-1">
              {loading ? '...' : stat.value}
            </div>
            <div className="text-sm text-emerald-50/50">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents */}
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-emerald-500/10">
              <FiFileText className="w-5 h-5 text-emerald-400" />
            </div>
            <h2 className="text-lg font-semibold text-white">Recent Documents</h2>
          </div>

          {loading ? (
            <div className="text-emerald-50/50 text-center py-8">Loading...</div>
          ) : recentActivity.length > 0 ? (
            <div className="space-y-3">
              {recentActivity.map((doc, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                      <FiFileText className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white truncate max-w-[200px]">
                        {doc.original_filename || doc.filename || 'Document'}
                      </div>
                      <div className="text-xs text-emerald-50/40">
                        {doc.category || 'Processing...'}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-emerald-50/30">
                    {doc.confidence ? `${(doc.confidence * 100).toFixed(0)}%` : '-'}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-emerald-50/50 text-center py-8">
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
              { name: 'RAG Chat', status: 'Active', color: 'emerald' },
              { name: 'Smart Router', status: 'Active', color: 'emerald' },
              { name: 'Summarization', status: 'Active', color: 'emerald' },
              { name: 'Comparison', status: 'Active', color: 'emerald' },
              { name: 'Reports', status: 'Active', color: 'emerald' },
              { name: 'Data Quality', status: 'Active', color: 'emerald' }
            ].map((service, index) => (
              <div
                key={index}
                className="p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white">{service.name}</span>
                  <span className={`flex items-center gap-1.5 text-xs text-${service.color}-400`}>
                    <span className={`w-1.5 h-1.5 rounded-full bg-${service.color}-400`} />
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
