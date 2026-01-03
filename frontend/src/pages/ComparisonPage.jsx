import React, { useState } from 'react'
import { FiGitMerge, FiPercent, FiPlus, FiMinus, FiEdit3 } from 'react-icons/fi'

function ComparisonPage() {
  const [text1, setText1] = useState('')
  const [text2, setText2] = useState('')
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleCompare = async () => {
    if (!text1.trim() || !text2.trim()) return

    setLoading(true)
    setComparison(null)

    try {
      const response = await fetch('http://localhost:8000/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text1,
          text2,
          generate_summary: true
        })
      })

      if (response.ok) {
        const data = await response.json()
        setComparison(data)
      } else {
        const error = await response.json()
        alert(error.detail || 'Comparison failed')
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to connect to the server')
    } finally {
      setLoading(false)
    }
  }

  const getSimilarityColor = (score) => {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.5) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getSimilarityBg = (score) => {
    if (score >= 0.8) return 'from-green-500/20 to-green-500/5'
    if (score >= 0.5) return 'from-yellow-500/20 to-yellow-500/5'
    return 'from-red-500/20 to-red-500/5'
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Document Comparison</h1>
        <p className="text-emerald-50/50">Compare documents for similarities and differences</p>
      </div>

      {/* Input Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Document 1</h2>
          <textarea
            value={text1}
            onChange={(e) => setText1(e.target.value)}
            placeholder="Paste first document text..."
            className="w-full h-48 p-4 rounded-xl bg-white/[0.03] border border-white/5 text-white placeholder-emerald-50/30 focus:outline-none focus:border-emerald-500/50 resize-none"
          />
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Document 2</h2>
          <textarea
            value={text2}
            onChange={(e) => setText2(e.target.value)}
            placeholder="Paste second document text..."
            className="w-full h-48 p-4 rounded-xl bg-white/[0.03] border border-white/5 text-white placeholder-emerald-50/30 focus:outline-none focus:border-emerald-500/50 resize-none"
          />
        </div>
      </div>

      <button
        onClick={handleCompare}
        disabled={loading || !text1.trim() || !text2.trim()}
        className="w-full mb-6 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-medium hover:from-emerald-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
      >
        <FiGitMerge className="w-4 h-4" />
        {loading ? 'Comparing...' : 'Compare Documents'}
      </button>

      {/* Results Section */}
      {comparison && (
        <div className="space-y-6">
          {/* Similarity Score */}
          <div className={`rounded-2xl border border-white/5 bg-gradient-to-br ${getSimilarityBg(comparison.similarity_score)} p-6`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-white/10">
                  <FiPercent className={`w-6 h-6 ${getSimilarityColor(comparison.similarity_score)}`} />
                </div>
                <div>
                  <h3 className="text-sm text-emerald-50/50">Similarity Score</h3>
                  <p className={`text-3xl font-bold ${getSimilarityColor(comparison.similarity_score)}`}>
                    {(comparison.similarity_score * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-emerald-50/50">Match Level</p>
                <p className={`text-lg font-medium ${getSimilarityColor(comparison.similarity_score)}`}>
                  {comparison.similarity_score >= 0.8 ? 'High' :
                   comparison.similarity_score >= 0.5 ? 'Medium' : 'Low'}
                </p>
              </div>
            </div>
          </div>

          {/* Change Summary */}
          {comparison.change_summary && (
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Change Summary</h2>
              <p className="text-emerald-50/70 leading-relaxed">{comparison.change_summary}</p>
            </div>
          )}

          {/* Differences */}
          {comparison.differences && comparison.differences.length > 0 && (
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Differences Found</h2>
              <div className="space-y-3">
                {comparison.differences.map((diff, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-xl ${
                      diff.type === 'added' ? 'bg-green-500/10 border border-green-500/20' :
                      diff.type === 'removed' ? 'bg-red-500/10 border border-red-500/20' :
                      'bg-yellow-500/10 border border-yellow-500/20'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {diff.type === 'added' && <FiPlus className="w-4 h-4 text-green-400" />}
                      {diff.type === 'removed' && <FiMinus className="w-4 h-4 text-red-400" />}
                      {diff.type === 'modified' && <FiEdit3 className="w-4 h-4 text-yellow-400" />}
                      <span className={`text-sm font-medium ${
                        diff.type === 'added' ? 'text-green-400' :
                        diff.type === 'removed' ? 'text-red-400' :
                        'text-yellow-400'
                      }`}>
                        {diff.type.charAt(0).toUpperCase() + diff.type.slice(1)}
                      </span>
                    </div>
                    <p className="text-emerald-50/70 text-sm">{diff.content || diff.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Common Elements */}
          {comparison.common_elements && comparison.common_elements.length > 0 && (
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Common Elements</h2>
              <div className="flex flex-wrap gap-2">
                {comparison.common_elements.map((element, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-300 text-sm"
                  >
                    {element}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!comparison && !loading && (
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-12 text-center">
          <FiGitMerge className="w-12 h-12 mx-auto mb-4 text-emerald-50/20" />
          <p className="text-emerald-50/50">
            Enter text in both documents and click "Compare Documents" to see the analysis
          </p>
        </div>
      )}
    </div>
  )
}

export default ComparisonPage
