import React, { useState } from 'react'
import { FiFileText, FiZap, FiList, FiUsers, FiCheckSquare } from 'react-icons/fi'

function SummarizationPage() {
  const [inputText, setInputText] = useState('')
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [options, setOptions] = useState({
    include_entities: true,
    include_actions: true
  })

  const handleSummarize = async () => {
    if (!inputText.trim()) return

    setLoading(true)
    setSummary(null)

    try {
      const response = await fetch('http://localhost:8000/api/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: inputText,
          ...options
        })
      })

      if (response.ok) {
        const data = await response.json()
        setSummary(data)
      } else {
        const error = await response.json()
        alert(error.detail || 'Summarization failed')
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to connect to the server')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickSummarize = async () => {
    if (!inputText.trim()) return

    setLoading(true)
    setSummary(null)

    try {
      const response = await fetch('http://localhost:8000/api/summarize/quick', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      })

      if (response.ok) {
        const data = await response.json()
        setSummary(data)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Document Summarization</h1>
        <p className="text-emerald-50/50">Generate concise summaries with key points, entities, and action items</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <FiFileText className="text-emerald-400" />
              Input Text
            </h2>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste your document text here..."
              className="w-full h-64 p-4 rounded-xl bg-white/[0.03] border border-white/5 text-white placeholder-emerald-50/30 focus:outline-none focus:border-emerald-500/50 resize-none"
            />

            {/* Options */}
            <div className="mt-4 flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.include_entities}
                  onChange={(e) => setOptions(prev => ({ ...prev, include_entities: e.target.checked }))}
                  className="w-4 h-4 rounded bg-white/10 border-white/20 text-emerald-500 focus:ring-emerald-500/50"
                />
                <span className="text-sm text-emerald-50/70">Extract Entities</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.include_actions}
                  onChange={(e) => setOptions(prev => ({ ...prev, include_actions: e.target.checked }))}
                  className="w-4 h-4 rounded bg-white/10 border-white/20 text-emerald-500 focus:ring-emerald-500/50"
                />
                <span className="text-sm text-emerald-50/70">Extract Action Items</span>
              </label>
            </div>

            {/* Buttons */}
            <div className="mt-4 flex gap-3">
              <button
                onClick={handleSummarize}
                disabled={loading || !inputText.trim()}
                className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-medium hover:from-emerald-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
              >
                <FiZap className="w-4 h-4" />
                {loading ? 'Summarizing...' : 'Full Summary'}
              </button>
              <button
                onClick={handleQuickSummarize}
                disabled={loading || !inputText.trim()}
                className="py-3 px-4 rounded-xl bg-white/[0.05] border border-white/10 text-white font-medium hover:bg-white/[0.1] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                Quick
              </button>
            </div>
          </div>
        </div>

        {/* Output Section */}
        <div className="space-y-4">
          {summary ? (
            <>
              {/* Executive Summary */}
              <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <FiZap className="text-emerald-400" />
                  Executive Summary
                </h2>
                <p className="text-emerald-50/80 leading-relaxed">
                  {summary.executive_summary || summary.summary || 'No summary generated'}
                </p>
              </div>

              {/* Key Points */}
              {summary.key_points && summary.key_points.length > 0 && (
                <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                  <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <FiList className="text-blue-400" />
                    Key Points
                  </h2>
                  <ul className="space-y-2">
                    {summary.key_points.map((point, index) => (
                      <li key={index} className="flex items-start gap-3 text-emerald-50/70">
                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Entities */}
              {summary.entities && Object.keys(summary.entities).length > 0 && (
                <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                  <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <FiUsers className="text-purple-400" />
                    Entities
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(summary.entities).map(([type, entities]) => (
                      Array.isArray(entities) && entities.map((entity, index) => (
                        <span
                          key={`${type}-${index}`}
                          className="px-3 py-1 rounded-full bg-purple-500/10 text-purple-300 text-sm"
                        >
                          {entity}
                        </span>
                      ))
                    ))}
                  </div>
                </div>
              )}

              {/* Action Items */}
              {summary.action_items && summary.action_items.length > 0 && (
                <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                  <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <FiCheckSquare className="text-amber-400" />
                    Action Items
                  </h2>
                  <ul className="space-y-2">
                    {summary.action_items.map((action, index) => (
                      <li key={index} className="flex items-start gap-3 text-emerald-50/70">
                        <span className="mt-0.5 w-5 h-5 rounded bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                          <span className="text-xs text-amber-400">{index + 1}</span>
                        </span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-12 text-center">
              <FiFileText className="w-12 h-12 mx-auto mb-4 text-emerald-50/20" />
              <p className="text-emerald-50/50">
                Enter text and click "Full Summary" to generate a comprehensive summary
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SummarizationPage
