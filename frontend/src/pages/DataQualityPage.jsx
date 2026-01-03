import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FiCheckCircle, FiAlertTriangle, FiXCircle, FiUploadCloud, FiDatabase, FiPieChart } from 'react-icons/fi'

function DataQualityPage() {
  const [assessment, setAssessment] = useState(null)
  const [loading, setLoading] = useState(false)
  const [jsonData, setJsonData] = useState('')

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return

    setLoading(true)
    setAssessment(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('dataset_name', file.name)

    try {
      const response = await fetch('http://localhost:8000/api/quality/assess', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setAssessment(data)
      } else {
        const error = await response.json()
        alert(error.detail || 'Assessment failed')
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to assess file')
    } finally {
      setLoading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/json': ['.json']
    },
    maxFiles: 1
  })

  const handleQuickCheck = async () => {
    if (!jsonData.trim()) return

    setLoading(true)
    setAssessment(null)

    try {
      const data = JSON.parse(jsonData)
      const response = await fetch('http://localhost:8000/api/quality/quick-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data })
      })

      if (response.ok) {
        const result = await response.json()
        setAssessment(result)
      } else {
        const error = await response.json()
        alert(error.detail || 'Quick check failed')
      }
    } catch (error) {
      if (error instanceof SyntaxError) {
        alert('Invalid JSON data')
      } else {
        console.error('Error:', error)
        alert('Failed to run quick check')
      }
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 0.95) return 'text-green-400'
    if (score >= 0.8) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getScoreIcon = (score) => {
    if (score >= 0.95) return FiCheckCircle
    if (score >= 0.8) return FiAlertTriangle
    return FiXCircle
  }

  const getScoreBg = (score) => {
    if (score >= 0.95) return 'bg-green-500/10 border-green-500/20'
    if (score >= 0.8) return 'bg-yellow-500/10 border-yellow-500/20'
    return 'bg-red-500/10 border-red-500/20'
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Data Quality Assessment</h1>
        <p className="text-emerald-50/50">Analyze data quality with profiling, anomaly detection, and scoring</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          {/* File Upload */}
          <div
            {...getRootProps()}
            className={`rounded-2xl border-2 border-dashed p-8 text-center transition-colors cursor-pointer ${
              isDragActive
                ? 'border-emerald-500 bg-emerald-500/10'
                : 'border-white/10 hover:border-emerald-500/50 bg-white/[0.02]'
            }`}
          >
            <input {...getInputProps()} />
            <FiUploadCloud className={`w-12 h-12 mx-auto mb-4 ${isDragActive ? 'text-emerald-400' : 'text-emerald-50/30'}`} />
            {loading ? (
              <p className="text-emerald-400">Analyzing...</p>
            ) : isDragActive ? (
              <p className="text-emerald-400">Drop file here...</p>
            ) : (
              <>
                <p className="text-white mb-2">Upload a data file for quality assessment</p>
                <p className="text-sm text-emerald-50/40">Supports CSV, XLSX, JSON</p>
              </>
            )}
          </div>

          {/* Quick Check */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <FiDatabase className="text-blue-400" />
              Quick Check (JSON)
            </h2>
            <textarea
              value={jsonData}
              onChange={(e) => setJsonData(e.target.value)}
              placeholder='[{"id": 1, "name": "John", "email": "john@example.com"}, ...]'
              className="w-full h-32 p-4 rounded-xl bg-white/[0.03] border border-white/5 text-white placeholder-emerald-50/30 focus:outline-none focus:border-emerald-500/50 font-mono text-sm resize-none"
            />
            <button
              onClick={handleQuickCheck}
              disabled={loading || !jsonData.trim()}
              className="w-full mt-4 py-3 px-4 rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              Run Quick Check
            </button>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          {assessment ? (
            <>
              {/* Overall Score */}
              <div className={`rounded-2xl border ${getScoreBg(assessment.overall_score || 0.85)} p-6`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-xl ${getScoreBg(assessment.overall_score || 0.85)}`}>
                      {React.createElement(getScoreIcon(assessment.overall_score || 0.85), {
                        className: `w-8 h-8 ${getScoreColor(assessment.overall_score || 0.85)}`
                      })}
                    </div>
                    <div>
                      <h3 className="text-sm text-emerald-50/50">Overall Quality Score</h3>
                      <p className={`text-4xl font-bold ${getScoreColor(assessment.overall_score || 0.85)}`}>
                        {((assessment.overall_score || 0.85) * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-emerald-50/50">Records Analyzed</p>
                    <p className="text-2xl font-bold text-white">
                      {assessment.record_count || assessment.row_count || '-'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Quality Metrics */}
              <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <FiPieChart className="text-emerald-400" />
                  Quality Metrics
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Completeness', value: assessment.completeness || assessment.metrics?.completeness || 0.95 },
                    { label: 'Uniqueness', value: assessment.uniqueness || assessment.metrics?.uniqueness || 0.99 },
                    { label: 'Consistency', value: assessment.consistency || assessment.metrics?.consistency || 0.92 },
                    { label: 'Validity', value: assessment.validity || assessment.metrics?.validity || 0.88 }
                  ].map((metric, index) => (
                    <div key={index} className="p-4 rounded-xl bg-white/[0.02]">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-emerald-50/50">{metric.label}</span>
                        <span className={`text-sm font-medium ${getScoreColor(metric.value)}`}>
                          {(metric.value * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            metric.value >= 0.95 ? 'bg-green-400' :
                            metric.value >= 0.8 ? 'bg-yellow-400' : 'bg-red-400'
                          }`}
                          style={{ width: `${metric.value * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Issues */}
              {assessment.issues && assessment.issues.length > 0 && (
                <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                  <h2 className="text-lg font-semibold text-white mb-4">Issues Found</h2>
                  <div className="space-y-2">
                    {assessment.issues.map((issue, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-xl flex items-start gap-3 ${
                          issue.severity === 'high' ? 'bg-red-500/10' :
                          issue.severity === 'medium' ? 'bg-yellow-500/10' :
                          'bg-blue-500/10'
                        }`}
                      >
                        {issue.severity === 'high' ? (
                          <FiXCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                        ) : issue.severity === 'medium' ? (
                          <FiAlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                        ) : (
                          <FiCheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                        )}
                        <div>
                          <p className="text-white text-sm">{issue.message || issue.description}</p>
                          {issue.column && (
                            <p className="text-emerald-50/40 text-xs mt-1">Column: {issue.column}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Column Profile */}
              {assessment.column_profiles && (
                <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                  <h2 className="text-lg font-semibold text-white mb-4">Column Profiles</h2>
                  <div className="space-y-2">
                    {Object.entries(assessment.column_profiles).map(([column, profile], index) => (
                      <div key={index} className="p-3 rounded-xl bg-white/[0.02]">
                        <div className="flex items-center justify-between">
                          <span className="text-white font-medium">{column}</span>
                          <span className="text-xs text-emerald-50/40">{profile.type || 'string'}</span>
                        </div>
                        <div className="flex gap-4 mt-2 text-xs text-emerald-50/50">
                          <span>Non-null: {profile.non_null_count || '-'}</span>
                          <span>Unique: {profile.unique_count || '-'}</span>
                          {profile.null_percentage !== undefined && (
                            <span>Missing: {(profile.null_percentage * 100).toFixed(1)}%</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-12 text-center">
              <FiDatabase className="w-12 h-12 mx-auto mb-4 text-emerald-50/20" />
              <p className="text-emerald-50/50">
                Upload a file or paste JSON data to assess data quality
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DataQualityPage
