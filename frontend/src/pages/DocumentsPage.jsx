import React, { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FiUploadCloud, FiFileText, FiTrash2, FiSearch, FiFilter, FiRefreshCw } from 'react-icons/fi'

function DocumentsPage() {
  const [documents, setDocuments] = useState([])
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')

  const categories = [
    'all', 'invoice', 'contract', 'report', 'meeting_minutes',
    'resume_cv', 'technical_documentation', 'other'
  ]

  useEffect(() => {
    fetchDocuments()
    fetchJobs()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/documents')
      if (response.ok) {
        const data = await response.json()
        setDocuments(data)
      }
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchJobs = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/upload/jobs')
      if (response.ok) {
        const data = await response.json()
        setJobs(data)
      }
    } catch (error) {
      console.error('Error fetching jobs:', error)
    }
  }

  const onDrop = useCallback(async (acceptedFiles) => {
    setUploading(true)
    for (const file of acceptedFiles) {
      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await fetch('http://localhost:8000/api/upload', {
          method: 'POST',
          body: formData
        })
        if (response.ok) {
          fetchDocuments()
          fetchJobs()
        }
      } catch (error) {
        console.error('Error uploading file:', error)
      }
    }
    setUploading(false)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md']
    }
  })

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.original_filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.category?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const processingJobs = jobs.filter(j => j.status === 'processing' || j.status === 'queued')

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Documents</h1>
        <p style={{ color: 'var(--text-muted)' }}>Upload and manage your documents</p>
      </div>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className="mb-6 border-2 border-dashed rounded-2xl p-8 text-center transition-colors cursor-pointer"
        style={{
          borderColor: isDragActive ? 'var(--accent)' : 'var(--border-color)',
          background: isDragActive ? 'var(--accent-muted)' : 'transparent'
        }}
      >
        <input {...getInputProps()} />
        <FiUploadCloud className="w-12 h-12 mx-auto mb-4" style={{ color: isDragActive ? 'var(--accent)' : 'var(--text-muted)' }} />
        {uploading ? (
          <p style={{ color: 'var(--accent)' }}>Uploading...</p>
        ) : isDragActive ? (
          <p style={{ color: 'var(--accent)' }}>Drop files here...</p>
        ) : (
          <>
            <p className="mb-2" style={{ color: 'var(--text-primary)' }}>Drag & drop files here, or click to select</p>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Supports PDF, DOCX, XLSX, TXT, MD</p>
          </>
        )}
      </div>

      {/* Processing Jobs */}
      {processingJobs.length > 0 && (
        <div className="mb-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4">
          <div className="flex items-center gap-2 mb-3">
            <FiRefreshCw className="w-4 h-4 text-amber-400 animate-spin" />
            <span className="text-sm font-medium text-amber-400">Processing {processingJobs.length} document(s)</span>
          </div>
          <div className="space-y-2">
            {processingJobs.slice(0, 3).map((job, index) => (
              <div key={index} className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {job.filename} - {job.status}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl focus:outline-none"
            style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
          />
        </div>
        <div className="relative">
          <FiFilter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="pl-10 pr-8 py-2.5 rounded-xl focus:outline-none appearance-none cursor-pointer"
            style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
          >
            {categories.map(cat => (
              <option key={cat} value={cat} style={{ background: 'var(--bg-secondary)' }}>
                {cat === 'all' ? 'All Categories' : cat.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={() => { fetchDocuments(); fetchJobs(); }}
          className="px-4 py-2.5 rounded-xl transition-colors"
          style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}
        >
          <FiRefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Documents List */}
      <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-emerald-50/50">Loading documents...</div>
        ) : filteredDocuments.length > 0 ? (
          <div className="divide-y divide-white/5">
            {filteredDocuments.map((doc, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                    <FiFileText className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">
                      {doc.original_filename || doc.filename}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-emerald-50/40">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400">
                        {doc.category || 'Uncategorized'}
                      </span>
                      {doc.confidence && (
                        <span>Confidence: {(doc.confidence * 100).toFixed(0)}%</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-emerald-50/30">
                    {new Date(doc.created_at || Date.now()).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-emerald-50/50">
            {searchTerm || selectedCategory !== 'all'
              ? 'No documents match your search'
              : 'No documents uploaded yet'}
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentsPage
