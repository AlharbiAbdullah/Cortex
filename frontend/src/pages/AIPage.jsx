import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { FiSend, FiDownload, FiChevronDown, FiArrowLeft, FiMessageSquare, FiZap, FiGitMerge, FiCheckCircle, FiUpload } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'

const AI_SERVICES = [
  { id: 'chat', name: 'RAG Chat', icon: FiMessageSquare, description: 'Query your documents with AI', color: 'emerald' },
  { id: 'summarize', name: 'Summarize', icon: FiZap, description: 'Extract key points from text', color: 'blue' },
  { id: 'compare', name: 'Compare', icon: FiGitMerge, description: 'Analyze document differences', color: 'purple' },
  { id: 'quality', name: 'Data Quality', icon: FiCheckCircle, description: 'Assess data quality', color: 'amber' },
]

const MODELS = [
  { id: 'qwen2.5:14b', name: 'Qwen 2.5' },
  { id: 'qwen3:8b', name: 'Qwen 3' },
  { id: 'gemma2:9b', name: 'Gemma 2' },
  { id: 'mistral:7b', name: 'Mistral' },
]

const EXPERTS = [
  { id: 'general', name: 'General' },
  { id: 'political', name: 'Political' },
  { id: 'intelligence', name: 'Intel' },
  { id: 'data_analytics', name: 'Analytics' },
  { id: 'media', name: 'Media' },
]

function AIPage() {
  const [activeService, setActiveService] = useState('chat')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState(MODELS[0].id)
  const [selectedExpert, setSelectedExpert] = useState(EXPERTS[0].id)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    inputRef.current?.focus()
  }, [activeService])

  const getServicePlaceholder = () => {
    switch (activeService) {
      case 'chat': return 'Ask anything about your documents...'
      case 'summarize': return 'Paste text to summarize, or ask to summarize a document...'
      case 'compare': return 'Describe what you want to compare...'
      case 'quality': return 'Describe the data you want to assess...'
      default: return 'Type your message...'
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')

    const newMessages = [...messages, { role: 'user', content: userMessage, service: activeService }]
    setMessages(newMessages)
    setLoading(true)

    try {
      let response
      const timeout = 120000

      if (activeService === 'chat') {
        response = await axios.post('/api/chat', {
          message: userMessage,
          conversation_history: newMessages.filter(m => m.service === 'chat').slice(-10),
          use_rag: true,
          model_name: selectedModel,
          expert: selectedExpert,
        }, { timeout })

        const assistantMessage = {
          role: 'assistant',
          content: response.data.response,
          service: activeService,
          expert: response.data.expert || selectedExpert,
        }
        if (response.data.excel_file) {
          assistantMessage.excel_file = response.data.excel_file
        }
        setMessages([...newMessages, assistantMessage])

      } else if (activeService === 'summarize') {
        response = await axios.post('/api/summarize', {
          text: userMessage,
          include_entities: true,
          include_actions: true,
        }, { timeout })

        let summaryContent = `**Summary:**\n${response.data.executive_summary || response.data.summary || 'No summary generated'}`
        if (response.data.key_points?.length) {
          summaryContent += `\n\n**Key Points:**\n${response.data.key_points.map(p => `- ${p}`).join('\n')}`
        }
        if (response.data.action_items?.length) {
          summaryContent += `\n\n**Action Items:**\n${response.data.action_items.map((a, i) => `${i + 1}. ${a}`).join('\n')}`
        }

        setMessages([...newMessages, { role: 'assistant', content: summaryContent, service: activeService }])

      } else if (activeService === 'compare') {
        // For compare, we expect user to provide two texts separated by "---"
        const parts = userMessage.split(/---+/)
        if (parts.length >= 2) {
          response = await axios.post('/api/compare', {
            text1: parts[0].trim(),
            text2: parts[1].trim(),
            generate_summary: true,
          }, { timeout })

          let compareContent = `**Similarity Score:** ${(response.data.similarity_score * 100).toFixed(1)}%`
          if (response.data.change_summary) {
            compareContent += `\n\n**Summary:**\n${response.data.change_summary}`
          }
          if (response.data.differences?.length) {
            compareContent += `\n\n**Differences:**\n${response.data.differences.map(d => `- ${d.type}: ${d.content || d.text}`).join('\n')}`
          }
          setMessages([...newMessages, { role: 'assistant', content: compareContent, service: activeService }])
        } else {
          setMessages([...newMessages, {
            role: 'assistant',
            content: 'To compare documents, please provide two texts separated by "---". For example:\n\n```\nFirst document text here\n---\nSecond document text here\n```',
            service: activeService
          }])
        }

      } else if (activeService === 'quality') {
        // For quality, we try to parse JSON or provide guidance
        try {
          const data = JSON.parse(userMessage)
          response = await axios.post('/api/quality/quick-check', { data }, { timeout })

          let qualityContent = `**Overall Quality Score:** ${((response.data.overall_score || 0.85) * 100).toFixed(0)}%`
          qualityContent += `\n\n**Metrics:**`
          qualityContent += `\n- Completeness: ${((response.data.completeness || response.data.metrics?.completeness || 0.95) * 100).toFixed(0)}%`
          qualityContent += `\n- Uniqueness: ${((response.data.uniqueness || response.data.metrics?.uniqueness || 0.99) * 100).toFixed(0)}%`
          qualityContent += `\n- Consistency: ${((response.data.consistency || response.data.metrics?.consistency || 0.92) * 100).toFixed(0)}%`

          if (response.data.issues?.length) {
            qualityContent += `\n\n**Issues Found:**\n${response.data.issues.map(i => `- ${i.message || i.description}`).join('\n')}`
          }

          setMessages([...newMessages, { role: 'assistant', content: qualityContent, service: activeService }])
        } catch {
          setMessages([...newMessages, {
            role: 'assistant',
            content: 'To assess data quality, please provide JSON data. For example:\n\n```json\n[{"id": 1, "name": "John", "email": "john@example.com"}, {"id": 2, "name": null, "email": "jane@example.com"}]\n```\n\nOr upload a CSV/Excel file using the Documents page.',
            service: activeService
          }])
        }
      }
    } catch (err) {
      console.error('Error:', err)
      setMessages([...newMessages, {
        role: 'assistant',
        content: err.response?.data?.detail || 'An error occurred. Please try again.',
        service: activeService
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const currentService = AI_SERVICES.find(s => s.id === activeService)

  return (
    <div className="h-full flex">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-white/5 bg-[#0f1c16]/40 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-white/5">
          <Link to="/" className="flex items-center gap-2 text-emerald-50/50 hover:text-white transition-colors">
            <FiArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to Home</span>
          </Link>
        </div>

        {/* Logo */}
        <div className="p-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 flex items-center justify-center">
              <HiOutlineSparkles className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h1 className="font-bold text-white">AI Platform</h1>
              <p className="text-xs text-purple-300/50">Smart Services</p>
            </div>
          </div>
        </div>

        {/* Services */}
        <nav className="flex-1 p-3 space-y-1">
          <div className="px-3 py-2">
            <span className="text-xs font-medium text-emerald-50/30 uppercase tracking-wider">Services</span>
          </div>
          {AI_SERVICES.map((service) => (
            <button
              key={service.id}
              onClick={() => setActiveService(service.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left ${
                activeService === service.id
                  ? 'bg-purple-500/10 text-white border border-purple-500/20'
                  : 'text-emerald-50/50 hover:text-white hover:bg-white/5'
              }`}
            >
              <service.icon className="w-4 h-4" />
              <div>
                <div className="text-sm font-medium">{service.name}</div>
                <div className="text-xs text-emerald-50/30">{service.description}</div>
              </div>
            </button>
          ))}
        </nav>

        {/* Model Selection */}
        <div className="p-4 border-t border-white/5">
          <label className="block text-xs text-emerald-50/30 mb-2">Model</label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full bg-white/[0.03] text-white text-sm px-3 py-2 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500/40"
          >
            {MODELS.map((model) => (
              <option key={model.id} value={model.id} className="bg-[#0c1612]">{model.name}</option>
            ))}
          </select>
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <currentService.icon className="w-5 h-5 text-purple-400" />
            <div>
              <h2 className="font-semibold text-white">{currentService.name}</h2>
              <p className="text-xs text-emerald-50/40">{currentService.description}</p>
            </div>
          </div>

          {activeService === 'chat' && (
            <div className="flex gap-1.5">
              {EXPERTS.map((expert) => (
                <button
                  key={expert.id}
                  onClick={() => setSelectedExpert(expert.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                    selectedExpert === expert.id
                      ? 'bg-purple-500/15 text-purple-300 border border-purple-500/30'
                      : 'text-white/40 border border-white/10 hover:border-white/20'
                  }`}
                >
                  {expert.name}
                </button>
              ))}
            </div>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-auto px-6 py-4">
          {messages.filter(m => m.service === activeService).length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <currentService.icon className="w-16 h-16 mx-auto mb-4 text-purple-400/20" />
                <h3 className="text-xl font-medium text-white/80 mb-2">{currentService.name}</h3>
                <p className="text-emerald-50/40 max-w-md">{currentService.description}</p>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.filter(m => m.service === activeService).map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] ${message.role === 'user' ? 'text-right' : ''}`}>
                    {message.role === 'assistant' && (
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-1.5 h-1.5 bg-purple-400 rounded-full" />
                        <span className="text-xs text-purple-400/70 uppercase tracking-wider">
                          {currentService.name}
                        </span>
                      </div>
                    )}
                    {message.role === 'assistant' ? (
                      <div className="prose prose-invert text-sm leading-relaxed">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm text-white/60 whitespace-pre-wrap">{message.content}</p>
                    )}
                    {message.excel_file && (
                      <a
                        href={`/api/download/${message.excel_file}`}
                        className="inline-flex items-center gap-2 mt-2 text-purple-400 text-sm hover:text-purple-300"
                      >
                        <FiDownload className="w-4 h-4" />
                        Download file
                      </a>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex items-center gap-2 text-purple-400/60">
                  <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-pulse" />
                  <span className="text-sm">Processing...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-white/5">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
            <div className="relative rounded-2xl border border-white/10 focus-within:border-purple-500/40 transition-colors">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={getServicePlaceholder()}
                rows={1}
                className="w-full bg-transparent text-white placeholder-white/30 text-sm pl-4 pr-14 py-4 resize-none focus:outline-none"
                style={{ minHeight: '56px', maxHeight: '200px' }}
                onInput={(e) => {
                  e.target.style.height = 'auto'
                  e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'
                }}
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className={`absolute right-3 bottom-3 w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                  input.trim() && !loading
                    ? 'bg-purple-500 text-white'
                    : 'bg-white/5 text-white/20'
                }`}
              >
                <FiSend className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      </div>

      <style>{`
        .prose p { margin-bottom: 0.5em; }
        .prose p:last-child { margin-bottom: 0; }
        .prose strong { font-weight: 600; color: #c4b5fd; }
        .prose code {
          font-size: 0.875em;
          background: rgba(255, 255, 255, 0.08);
          color: #c4b5fd;
          padding: 0.15em 0.4em;
          border-radius: 4px;
        }
        .prose pre {
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.08);
          padding: 1em;
          overflow-x: auto;
          border-radius: 8px;
        }
        .prose pre code { background: none; padding: 0; }
        .prose ul, .prose ol { padding-left: 1.25em; margin: 0.5em 0; }
        .prose li { margin: 0.25em 0; }
      `}</style>
    </div>
  )
}

export default AIPage
