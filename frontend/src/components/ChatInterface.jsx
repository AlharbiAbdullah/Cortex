import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { FiSend, FiDownload, FiChevronDown } from 'react-icons/fi'
import { useTypewriter } from '../hooks/useTypewriter'

// Rotating phrases for empty state
const PHRASES = [
  "How can I help you?",
  "Want me to search your documents?",
  "What's on your mind?",
  "Ask me anything...",
  "Ready to explore your data?",
  "What would you like to know?",
  "Let's find some answers.",
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

function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState(MODELS[0].id)
  const [selectedExpert, setSelectedExpert] = useState(EXPERTS[0].id)
  const [inputFocused, setInputFocused] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Typewriter effect for empty state
  const typewriterText = useTypewriter(PHRASES, 70, 40, 2000)

  const getExpert = (expertId) => {
    return EXPERTS.find((e) => e.id === expertId) || EXPERTS[0]
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')

    const newMessages = [...messages, { role: 'user', content: userMessage }]
    setMessages(newMessages)
    setLoading(true)

    try {
      const timeout = selectedExpert === 'media' ? 300000 : 120000
      const response = await axios.post('/api/chat', {
        message: userMessage,
        conversation_history: newMessages.slice(-10),
        use_rag: true,
        model_name: selectedModel,
        expert: selectedExpert,
      }, { timeout })

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        expert: response.data.expert || selectedExpert,
      }

      if (response.data.excel_file) {
        assistantMessage.excel_file = response.data.excel_file
      }

      setMessages([...newMessages, assistantMessage])
    } catch (err) {
      console.error('Chat error:', err)
      let errorMessage = 'Unable to get response.'
      if (err.response) {
        errorMessage = err.response?.data?.detail || 'Server error'
      } else if (err.request) {
        errorMessage = 'No response from server'
      }
      setMessages([...newMessages, { role: 'assistant', content: errorMessage }])
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

  return (
    <div className="flex flex-col h-full relative overflow-hidden bg-transparent">
      {/* Messages Area */}
      <div className="flex-1 overflow-auto relative px-4 sm:px-6 hide-scrollbar">
        {messages.length === 0 ? (
          /* Empty State - Elegant with Typewriter */
          <div className="h-full flex flex-col items-center justify-center">
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="relative">
                  <div className="absolute inset-0 bg-emerald-500/20 blur-3xl rounded-full scale-150" />
                  <div className="relative w-40 h-40 rounded-full bg-gradient-to-br from-emerald-400/20 to-emerald-600/20 flex items-center justify-center">
                    <span className="text-6xl font-bold text-emerald-400/80">C</span>
                  </div>
                </div>
              </div>
              <h1 className="text-2xl font-light tracking-wide text-white/80 font-display h-9 flex items-center justify-center">
                <span>{typewriterText}</span>
                <span className="ml-0.5 w-0.5 h-6 bg-emerald-400/70 animate-blink" />
              </h1>
            </div>
          </div>
        ) : (
          /* Messages - Elegant Minimal */
          <div className="max-w-2xl mx-auto py-8 space-y-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                style={{
                  animation: 'fadeIn 0.4s ease-out forwards',
                  animationDelay: `${index * 30}ms`,
                }}
              >
                <div className={`max-w-[80%] ${message.role === 'user' ? 'text-right' : ''}`}>
                  {message.role === 'assistant' && (
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
                      <span className="text-[11px] font-medium text-emerald-400/70 uppercase tracking-wider font-display">
                        {getExpert(message.expert).name}
                      </span>
                    </div>
                  )}

                  {message.role === 'assistant' ? (
                    <div className="prose text-[15px] leading-[1.8] text-white/85">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-[15px] leading-[1.8] text-white/60 font-display">
                      {message.content}
                    </p>
                  )}

                  {message.excel_file && (
                    <a
                      href={`/api/download/${message.excel_file}`}
                      download
                      className="inline-flex items-center gap-2 mt-3 text-emerald-400/70 text-sm font-display hover:text-emerald-400 transition-colors"
                    >
                      <FiDownload className="w-3.5 h-3.5" />
                      <span>Download file</span>
                    </a>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-emerald-400/60 rounded-full animate-pulse" />
                  <span className="text-sm text-white/40 font-display">Thinking...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="relative p-4 sm:p-6">
        <div className="max-w-2xl mx-auto">
          {/* Two Options: Persona & Model */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-4 mb-5">
            {/* Persona Selection */}
            <div className="flex-1">
              <label className="block text-[10px] uppercase tracking-wider text-white/30 font-display mb-2 ml-1">
                Persona
              </label>
              <div className="flex flex-wrap gap-1.5">
                {EXPERTS.map((expert) => (
                  <button
                    key={expert.id}
                    onClick={() => setSelectedExpert(expert.id)}
                    disabled={loading}
                    className={`px-3.5 py-1.5 rounded-full text-xs font-medium font-display transition-all duration-200 ${
                      selectedExpert === expert.id
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                        : 'text-white/40 border border-white/10 hover:border-white/20 hover:text-white/60'
                    }`}
                  >
                    {expert.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Divider */}
            <div className="hidden sm:block w-px h-12 bg-white/10" />

            {/* Model Selection */}
            <div className="sm:w-40">
              <label className="block text-[10px] uppercase tracking-wider text-white/30 font-display mb-2 ml-1">
                Model
              </label>
              <div className="relative">
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  disabled={loading}
                  className="w-full appearance-none bg-white/[0.03] text-white/80 text-sm font-display px-3 py-2 pr-8 border border-white/10 rounded-lg cursor-pointer focus:outline-none focus:border-emerald-500/40 hover:border-white/20 transition-colors"
                >
                  {MODELS.map((model) => (
                    <option key={model.id} value={model.id} className="bg-[#0c1612]">
                      {model.name}
                    </option>
                  ))}
                </select>
                <FiChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit}>
            <div
              className={`rounded-2xl border transition-all duration-300 ${
                inputFocused ? 'border-emerald-500/40' : 'border-white/10'
              }`}
            >
              <div className="relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onFocus={() => setInputFocused(true)}
                  onBlur={() => setInputFocused(false)}
                  placeholder="Ask anything..."
                  rows={1}
                  className="w-full bg-transparent text-white/90 placeholder-white/30 text-[15px] font-display pl-5 pr-14 py-4 resize-none focus:outline-none"
                  style={{ minHeight: '56px', maxHeight: '140px' }}
                  onInput={(e) => {
                    e.target.style.height = 'auto'
                    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
                  }}
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || loading}
                  className={`absolute right-3 bottom-3 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
                    input.trim() && !loading
                      ? 'bg-emerald-500 text-white'
                      : 'bg-white/5 text-white/20'
                  }`}
                >
                  <FiSend className="w-4 h-4" />
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      <style>{`
        .font-display {
          font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, sans-serif;
          letter-spacing: -0.01em;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }

        .animate-blink {
          animation: blink 1s step-end infinite;
        }

        .prose p { margin-bottom: 0.75em; }
        .prose p:last-child { margin-bottom: 0; }
        .prose strong { font-weight: 600; color: #a7f3d0; }
        .prose a { color: #6ee7b7; text-decoration: underline; }
        .prose code {
          font-size: 0.875em;
          background: rgba(255, 255, 255, 0.08);
          color: #a7f3d0;
          padding: 0.15em 0.4em;
          border-radius: 4px;
        }
        .prose pre {
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.08);
          padding: 1em;
          overflow-x: auto;
          margin: 0.75em 0;
          border-radius: 8px;
        }
        .prose pre code { background: none; padding: 0; }
        .prose ul, .prose ol { padding-left: 1.25em; margin: 0.5em 0; }
        .prose li { margin: 0.25em 0; }
        .prose li::marker { color: #10b981; }
        .prose blockquote {
          border-left: 2px solid rgba(16, 185, 129, 0.4);
          padding-left: 1em;
          margin: 0.75em 0;
          color: rgba(255, 255, 255, 0.6);
        }

        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        .hide-scrollbar::-webkit-scrollbar { display: none; }
      `}</style>
    </div>
  )
}

export default ChatInterface
