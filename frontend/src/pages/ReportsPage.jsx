import React, { useState, useEffect } from 'react'
import { FiFileText, FiDownload, FiPlus, FiLayout, FiBarChart2 } from 'react-icons/fi'

function ReportsPage() {
  const [templates, setTemplates] = useState([])
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [reportData, setReportData] = useState({})
  const [outputFormat, setOutputFormat] = useState('pdf')
  const [loading, setLoading] = useState(false)
  const [generatedReport, setGeneratedReport] = useState(null)

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/reports/templates')
      if (response.ok) {
        const data = await response.json()
        setTemplates(data.templates || data || [])
      }
    } catch (error) {
      console.error('Error fetching templates:', error)
      // Set default templates for demo
      setTemplates([
        { id: 'executive_summary', name: 'Executive Summary', description: 'High-level business overview' },
        { id: 'data_analysis', name: 'Data Analysis', description: 'Detailed data analysis report' },
        { id: 'comparison', name: 'Comparison Report', description: 'Document comparison report' }
      ])
    }
  }

  const handleGenerateReport = async () => {
    if (!selectedTemplate) return

    setLoading(true)
    setGeneratedReport(null)

    try {
      const response = await fetch('http://localhost:8000/api/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: selectedTemplate,
          data: reportData,
          output_format: outputFormat
        })
      })

      if (response.ok) {
        const data = await response.json()
        setGeneratedReport(data)
      } else {
        const error = await response.json()
        alert(error.detail || 'Report generation failed')
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  const sampleData = {
    executive_summary: {
      title: 'Q4 2024 Performance Review',
      summary: 'Strong quarterly performance with significant growth across all metrics.',
      key_findings: [
        'Revenue exceeded targets by 12%',
        'Customer acquisition cost reduced by 20%',
        'Market share increased to 23%'
      ],
      recommendations: [
        'Expand into European markets',
        'Increase R&D investment by 10%',
        'Launch customer loyalty program'
      ]
    },
    data_analysis: {
      title: 'Sales Data Analysis',
      analysis_summary: 'Comprehensive analysis of Q4 sales performance.',
      data_table: [
        { month: 'October', revenue: 45000, units: 120 },
        { month: 'November', revenue: 52000, units: 145 },
        { month: 'December', revenue: 61000, units: 180 }
      ],
      insights: [
        'December showed 35% increase over October',
        'Average order value increased by 8%'
      ]
    }
  }

  const loadSampleData = () => {
    if (selectedTemplate && sampleData[selectedTemplate]) {
      setReportData(sampleData[selectedTemplate])
    }
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Report Generation</h1>
        <p style={{ color: 'var(--text-muted)' }}>Generate formatted reports from templates</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template Selection */}
        <div className="lg:col-span-1 space-y-4">
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <FiLayout style={{ color: 'var(--accent)' }} />
              Templates
            </h2>
            <div className="space-y-2">
              {templates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => {
                    setSelectedTemplate(template.id)
                    setReportData({})
                  }}
                  className="w-full p-4 rounded-xl text-left transition-colors"
                  style={{
                    background: selectedTemplate === template.id ? 'var(--accent-muted)' : 'var(--card-bg)',
                    border: selectedTemplate === template.id ? '1px solid var(--accent)' : '1px solid var(--border-color)'
                  }}
                >
                  <div className="font-medium" style={{ color: 'var(--text-primary)' }}>{template.name}</div>
                  <div className="text-sm" style={{ color: 'var(--text-muted)' }}>{template.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Output Format */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Output Format</h2>
            <div className="flex gap-2">
              {['pdf', 'docx', 'html'].map((format) => (
                <button
                  key={format}
                  onClick={() => setOutputFormat(format)}
                  className="flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors"
                  style={{
                    background: outputFormat === format ? 'var(--accent)' : 'var(--card-bg)',
                    color: outputFormat === format ? 'var(--bg-primary)' : 'var(--text-secondary)'
                  }}
                >
                  {format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Report Data */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <FiBarChart2 className="text-blue-400" />
                Report Data
              </h2>
              {selectedTemplate && sampleData[selectedTemplate] && (
                <button
                  onClick={loadSampleData}
                  className="text-sm transition-colors"
                  style={{ color: 'var(--accent)' }}
                >
                  Load Sample Data
                </button>
              )}
            </div>

            {selectedTemplate ? (
              <div className="space-y-4">
                <textarea
                  value={JSON.stringify(reportData, null, 2)}
                  onChange={(e) => {
                    try {
                      setReportData(JSON.parse(e.target.value))
                    } catch {
                      // Invalid JSON, ignore
                    }
                  }}
                  placeholder="Enter report data as JSON..."
                  className="w-full h-64 p-4 rounded-xl font-mono text-sm resize-none focus:outline-none"
                  style={{
                    background: 'var(--card-bg)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)'
                  }}
                />

                <button
                  onClick={handleGenerateReport}
                  disabled={loading || Object.keys(reportData).length === 0}
                  className="w-full py-3 px-4 rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                  style={{ background: 'var(--accent)', color: 'var(--bg-primary)' }}
                >
                  <FiFileText className="w-4 h-4" />
                  {loading ? 'Generating...' : 'Generate Report'}
                </button>
              </div>
            ) : (
              <div className="text-center py-12" style={{ color: 'var(--text-muted)' }}>
                <FiLayout className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p>Select a template to get started</p>
              </div>
            )}
          </div>

          {/* Generated Report */}
          {generatedReport && (
            <div className="rounded-2xl p-6" style={{ border: '1px solid var(--accent)', background: 'var(--accent-muted)' }}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Report Generated</h2>
                {generatedReport.download_url && (
                  <a
                    href={`http://localhost:8000${generatedReport.download_url}`}
                    download
                    className="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors"
                    style={{ background: 'var(--accent)', color: 'var(--bg-primary)' }}
                  >
                    <FiDownload className="w-4 h-4" />
                    Download
                  </a>
                )}
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                <p>Filename: {generatedReport.filename || 'report.' + outputFormat}</p>
                <p>Format: {outputFormat.toUpperCase()}</p>
                {generatedReport.size && <p>Size: {(generatedReport.size / 1024).toFixed(1)} KB</p>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ReportsPage
