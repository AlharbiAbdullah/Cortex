import React, { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { FiArrowRight, FiArrowLeft, FiUpload, FiCheck, FiX, FiLoader } from 'react-icons/fi'
import axios from 'axios'
import { useTypewriter } from '../hooks/useTypewriter'

const ROTATING_WORDS = [
  "Engineers...",
  "Data Engineers...",
  "Data Scientists...",
  "Analysts...",
  "Curious Minds...",
  "Researchers...",
]

function LandingPage() {
  const text = useTypewriter(ROTATING_WORDS, 120, 60, 2500)
  const fileInputRef = useRef(null)

  const [uploading, setUploading] = useState(false)
  const [uploadFileName, setUploadFileName] = useState(null)
  const [uploadPercent, setUploadPercent] = useState(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [dragActive, setDragActive] = useState(false)

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleUpload(e.target.files[0])
    }
  }

  const handleUpload = async (file) => {
    setUploadError('')
    setUploadSuccess(false)
    setUploading(true)
    setUploadFileName(file.name)
    setUploadPercent(0)

    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
        onUploadProgress: (progressEvent) => {
          const total = progressEvent?.total
          const loaded = progressEvent?.loaded
          if (typeof total === 'number' && total > 0 && typeof loaded === 'number') {
            setUploadPercent(Math.min(100, Math.max(0, Math.round((loaded / total) * 100))))
          } else {
            setUploadPercent(null)
          }
        }
      })
      setUploadSuccess(true)
      setTimeout(() => {
        setUploadSuccess(false)
        setUploadFileName(null)
      }, 3000)
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Failed to upload')
      setTimeout(() => {
        setUploadError('')
      }, 4000)
    } finally {
      setUploading(false)
      setUploadPercent(null)
    }
  }

  return (
    <div
      className="relative h-full overflow-hidden flex flex-col items-center justify-center px-6"
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      {/* Drag Overlay */}
      {dragActive && (
        <div
          className="absolute inset-0 z-50 backdrop-blur-sm border-4 border-dashed flex items-center justify-center"
          style={{
            background: 'var(--accent-muted)',
            borderColor: 'var(--accent)'
          }}
        >
          <div className="text-center">
            <FiUpload className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--accent)' }} />
            <p className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>Drop file to upload</p>
            <p className="mt-2" style={{ color: 'var(--text-muted)' }}>PDF, DOCX, Excel, TXT, Markdown</p>
          </div>
        </div>
      )}

      {/* Static Cortex Logo */}
      <div className="w-full max-w-3xl -mt-8 mb-4 text-center">
        <h1
          className="text-7xl md:text-8xl font-bold tracking-widest"
          style={{ color: 'var(--color-text)' }}
        >
          CORTEX
        </h1>
      </div>

      {/* Subtitle & Typewriter */}
      <div className="text-center -mt-4 mb-8">
        <p className="text-xl" style={{ color: 'var(--text-muted)' }}>Enterprise Intelligence Platform</p>

        {/* Typewriter */}
        <div className="mt-4">
          <h2 className="text-2xl md:text-3xl font-semibold tracking-tight">
            <span style={{ color: 'var(--text-secondary)' }}>Built for</span>
            <span className="mx-2" style={{ color: '#79740e' }}>&gt;</span>
            <span className="relative inline-block min-w-[180px] text-left">
              <span style={{ color: '#9d0006' }}>
                {text}
              </span>
              <span className="animate-blink" style={{ color: 'var(--accent-light)' }}>|</span>
            </span>
          </h2>
        </div>
      </div>

      {/* Platform Buttons - AI and BI */}
      <div className="flex items-center justify-center gap-6 mb-6">
        <Link
          to="/ai"
          className="group inline-flex items-center gap-3 px-8 py-4 rounded-2xl font-semibold transition-all duration-300"
          style={{
            border: '1px solid var(--border-color)',
            background: 'var(--card-bg)',
            color: 'var(--text-primary)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent)'
            e.currentTarget.style.background = 'var(--card-hover)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border-color)'
            e.currentTarget.style.background = 'var(--card-bg)'
          }}
        >
          <FiArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
          <span>AI Platform</span>
        </Link>

        <Link
          to="/bi"
          className="group inline-flex items-center gap-3 px-8 py-4 rounded-2xl font-semibold transition-all duration-300"
          style={{
            border: '1px solid var(--border-color)',
            background: 'var(--card-bg)',
            color: 'var(--text-primary)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent)'
            e.currentTarget.style.background = 'var(--card-hover)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border-color)'
            e.currentTarget.style.background = 'var(--card-bg)'
          }}
        >
          <span>BI Platform</span>
          <FiArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>

      {/* Upload Button */}
      <div className="group flex flex-col items-center">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md,.markdown,.xlsx,.xls,.csv"
          onChange={handleFileSelect}
          className="hidden"
        />
        <button
          onClick={handleUploadClick}
          disabled={uploading}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ color: 'var(--text-secondary)' }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--text-primary)'
            e.currentTarget.style.background = 'var(--card-bg)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-secondary)'
            e.currentTarget.style.background = 'transparent'
          }}
        >
          {uploading ? (
            <>
              <FiLoader className="w-4 h-4 animate-spin" />
              <span>Uploading {uploadPercent}%...</span>
            </>
          ) : uploadSuccess ? (
            <>
              <FiCheck className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              <span style={{ color: 'var(--accent)' }}>Uploaded!</span>
            </>
          ) : uploadError ? (
            <>
              <FiX className="w-4 h-4" style={{ color: 'var(--red)' }} />
              <span style={{ color: 'var(--red)' }}>Failed</span>
            </>
          ) : (
            <>
              <FiUpload className="w-4 h-4" />
              <span>Upload Files</span>
              <FiArrowRight className="w-4 h-4 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
            </>
          )}
        </button>

        {!uploading && !uploadSuccess && !uploadError && (
          <p className="mt-2 text-xs opacity-0 group-hover:opacity-100 transition-all duration-300" style={{ color: 'var(--text-muted)' }}>
            PDF, DOCX, Excel, TXT, Markdown
          </p>
        )}
      </div>

      {/* Upload Status */}
      {(uploadFileName || uploadError) && (
        <div className="mt-4">
          <div
            className="px-4 py-2 rounded-lg text-sm"
            style={{
              background: uploadError ? 'rgba(251, 73, 52, 0.1)' : 'var(--accent-muted)',
              border: uploadError ? '1px solid rgba(251, 73, 52, 0.2)' : '1px solid var(--border-color)',
              color: uploadError ? 'var(--red)' : 'var(--accent)'
            }}
          >
            {uploadError || uploadFileName}
          </div>
        </div>
      )}

      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        .animate-blink {
          animation: blink 1s step-end infinite;
        }
      `}</style>
    </div>
  )
}

export default LandingPage
