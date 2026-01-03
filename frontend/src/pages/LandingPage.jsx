import React, { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { FiArrowRight, FiUpload, FiCheck, FiX, FiLoader } from 'react-icons/fi'
import axios from 'axios'
import { useTypewriter } from '../hooks/useTypewriter'

// Configuration
const ROTATING_WORDS = [
  "Analyzing...",
  "Chatting...",
  "Extracting...",
  "Exploring...",
  "Researching...",
  "Reporting...",
  "Predicting...",
  "Connecting...",
]

function LandingPage() {
  const text = useTypewriter(ROTATING_WORDS, 120, 60, 2500)
  const fileInputRef = useRef(null)

  // Upload state
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
      className="relative h-full overflow-hidden"
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

      {/* Vertical Accent Bar - Grid-breaking element */}
      <div className="absolute left-1/3 top-0 bottom-0 w-px pointer-events-none hidden md:block">
        <div className="sticky top-1/2 -translate-y-1/2">
          <div className="w-1 h-32 bg-gradient-to-b from-transparent via-gray-400/30 to-transparent rounded-full blur-sm" />
          <div className="w-px h-48 bg-gradient-to-b from-transparent via-emerald-400/50 to-transparent -mt-24" />
        </div>
      </div>

      <div className="relative h-full overflow-auto flex flex-col">
        {/* Hero Section */}
        <div className="flex-1 flex flex-col items-center justify-center text-center px-6 py-2 min-h-[70vh]">
          <div className="max-w-4xl">

            {/* Logo */}
            <div className="flex justify-center -mt-16">
              <div className="relative">
                <div className="absolute inset-0 bg-emerald-500/20 blur-3xl rounded-full scale-150" />
                <div className="relative w-48 h-48 rounded-full bg-gradient-to-br from-emerald-400/30 to-emerald-600/30 flex items-center justify-center">
                  <span className="text-8xl font-bold text-emerald-400/90 drop-shadow-2xl">C</span>
                </div>
              </div>
            </div>

            {/* Cortex Title */}
            <div className="-mt-8">
              <h1 className="text-5xl md:text-7xl font-semibold tracking-tight font-brand hero-haze">
                <span className="relative inline-block bg-gradient-to-r from-emerald-200/90 via-emerald-100/70 to-white/60 bg-clip-text text-transparent drop-shadow-[0_18px_45px_rgba(0,0,0,0.45)] before:absolute before:inset-0 before:-z-10 before:rounded-full before:bg-emerald-400/10 before:blur-2xl before:content-[''] after:absolute after:inset-x-0 after:-bottom-2 after:h-px after:bg-gradient-to-r after:from-emerald-400/0 after:via-emerald-300/60 after:to-emerald-400/0 after:content-['']">Cortex</span>
              </h1>
              <p className="mt-2 text-lg text-emerald-50/50 font-display">Document Intelligence Platform</p>
            </div>

            {/* Typewriter Text */}
            <div className="mt-6">
              <h1 className="text-3xl md:text-5xl font-semibold tracking-tight font-brand hero-haze">
                <span className="bg-gradient-to-r from-gray-400/90 via-gray-300/70 to-white/60 bg-clip-text text-transparent">Built for</span>
                <span className="text-gray-400/70 mx-2">&gt;</span>
                <span className="relative inline-block min-w-[200px] text-left">
                  <span className="bg-gradient-to-r from-emerald-200/90 via-emerald-100/70 to-white/60 bg-clip-text text-transparent">
                    {text}
                  </span>
                  <span className="animate-blink text-emerald-300/80">|</span>
                </span>
              </h1>
            </div>

            {/* Action Button */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mt-8">
              <Link
                to="/chat"
                className="group inline-flex items-center px-10 py-5 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-white font-semibold font-display transition-all duration-300 hover:border-emerald-500/50 hover:bg-emerald-500/20"
              >
                <span className="flex items-center gap-3">
                  <span>Start Chatting</span>
                  <FiArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                </span>
              </Link>
            </div>

            {/* Tertiary Action - Upload Files (Ghost/Subtle) */}
            <div className="group flex flex-col items-center mt-8">
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
                className="inline-flex items-center px-6 py-3 rounded-xl text-emerald-200/80 font-medium font-display transition-all duration-300 hover:text-emerald-100 hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="flex items-center gap-2">
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
                </span>
              </button>

              {/* File types hint - shown on hover */}
              {!uploading && !uploadSuccess && !uploadError && (
                <p className="mt-2 text-xs text-emerald-50/30 group-hover:text-emerald-50/60 opacity-0 group-hover:opacity-100 transition-all duration-300">
                  PDF, DOCX, Excel, TXT, Markdown
                </p>
              )}
            </div>

            {/* Upload Status Message */}
            {(uploadFileName || uploadError) && (
              <div className="flex justify-center mt-4">
                <div className={`px-4 py-2 rounded-lg text-sm ${
                  uploadError
                    ? 'bg-red-500/10 border border-red-500/20 text-red-300'
                    : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                }`}>
                  {uploadError || uploadFileName}
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  )
}

export default LandingPage
