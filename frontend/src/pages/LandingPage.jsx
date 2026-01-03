import React, { useState, useRef, Suspense } from 'react'
import { Link } from 'react-router-dom'
import { FiArrowRight, FiArrowLeft, FiUpload, FiCheck, FiX, FiLoader } from 'react-icons/fi'
import axios from 'axios'
import { useTypewriter } from '../hooks/useTypewriter'
import CortexLogo from '../components/CortexLogo'

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
        <div className="absolute inset-0 z-50 bg-emerald-500/10 backdrop-blur-sm border-4 border-dashed border-emerald-500 flex items-center justify-center">
          <div className="text-center">
            <FiUpload className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
            <p className="text-2xl font-semibold text-white">Drop file to upload</p>
            <p className="text-emerald-200/60 mt-2">PDF, DOCX, Excel, TXT, Markdown</p>
          </div>
        </div>
      )}

      {/* Logo and Title */}
      <div className="text-center mb-8">
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-500/20 blur-3xl rounded-full scale-150" />
            <Suspense
              fallback={
                <div className="relative w-32 h-32 rounded-full bg-gradient-to-br from-emerald-400/30 to-emerald-600/30 flex items-center justify-center">
                  <div className="w-8 h-8 border-2 border-emerald-400/50 border-t-emerald-400 rounded-full animate-spin" />
                </div>
              }
            >
              <CortexLogo size={160} />
            </Suspense>
          </div>
        </div>

        <h1 className="text-5xl md:text-7xl font-semibold tracking-tight">
          <span className="bg-gradient-to-r from-emerald-200/90 via-emerald-100/70 to-white/60 bg-clip-text text-transparent">
            Cortex
          </span>
        </h1>
        <p className="mt-3 text-xl text-emerald-50/50">Enterprise Intelligence Platform</p>

        {/* Typewriter */}
        <div className="mt-4">
          <h2 className="text-2xl md:text-3xl font-semibold tracking-tight">
            <span className="bg-gradient-to-r from-gray-400/90 via-gray-300/70 to-white/60 bg-clip-text text-transparent">Built for</span>
            <span className="text-gray-400/70 mx-2">&gt;</span>
            <span className="relative inline-block min-w-[180px] text-left">
              <span className="bg-gradient-to-r from-emerald-200/90 via-emerald-100/70 to-white/60 bg-clip-text text-transparent">
                {text}
              </span>
              <span className="animate-blink text-emerald-300/80">|</span>
            </span>
          </h2>
        </div>
      </div>

      {/* Platform Buttons - AI and BI */}
      <div className="flex items-center justify-center gap-6 mb-6">
        <Link
          to="/ai"
          className="group inline-flex items-center gap-3 px-8 py-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-white font-semibold transition-all duration-300 hover:border-emerald-500/50 hover:bg-emerald-500/20"
        >
          <FiArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
          <span>AI Platform</span>
        </Link>

        <Link
          to="/bi"
          className="group inline-flex items-center gap-3 px-8 py-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-white font-semibold transition-all duration-300 hover:border-emerald-500/50 hover:bg-emerald-500/20"
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
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-emerald-200/80 font-medium transition-all duration-300 hover:text-emerald-100 hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? (
            <>
              <FiLoader className="w-4 h-4 animate-spin" />
              <span>Uploading {uploadPercent}%...</span>
            </>
          ) : uploadSuccess ? (
            <>
              <FiCheck className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">Uploaded!</span>
            </>
          ) : uploadError ? (
            <>
              <FiX className="w-4 h-4 text-red-400" />
              <span className="text-red-400">Failed</span>
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
          <p className="mt-2 text-xs text-emerald-50/30 group-hover:text-emerald-50/60 opacity-0 group-hover:opacity-100 transition-all duration-300">
            PDF, DOCX, Excel, TXT, Markdown
          </p>
        )}
      </div>

      {/* Upload Status */}
      {(uploadFileName || uploadError) && (
        <div className="mt-4">
          <div className={`px-4 py-2 rounded-lg text-sm ${
            uploadError
              ? 'bg-red-500/10 border border-red-500/20 text-red-300'
              : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
          }`}>
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
