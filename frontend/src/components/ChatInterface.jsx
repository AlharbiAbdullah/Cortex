import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { FiSend, FiDownload, FiChevronDown } from 'react-icons/fi'
import { useTypewriter } from '../hooks/useTypewriter'
import ChartRenderer, { containsChartData, extractSummary } from './ChartRenderer'

// Default rotating phrases for empty state
const DEFAULT_PHRASES = [
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
  { id: 'data_analytics', name: 'Analyst' },
]

function ChatInterface({ showOptions = true, phrases = DEFAULT_PHRASES }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState(MODELS[0].id)
  const [selectedExpert, setSelectedExpert] = useState(EXPERTS[0].id)
  const [inputFocused, setInputFocused] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Typewriter effect for empty state
  const typewriterText = useTypewriter(phrases, 70, 40, 2000)

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
      const response = await axios.post('/api/chat', {
        message: userMessage,
        conversation_history: newMessages.slice(-10),
        use_rag: true,
        model_name: selectedModel,
        expert: selectedExpert,
      }, { timeout: 120000 })

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
              <h1 className="text-2xl font-light tracking-wide font-display h-9 flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>
                <span>{typewriterText}</span>
                <span className="ml-0.5 w-0.5 h-6 animate-blink" style={{ background: 'var(--accent)' }} />
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
                      <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--accent)' }} />
                      <span className="text-[11px] font-medium uppercase tracking-wider font-display" style={{ color: 'var(--accent)' }}>
                        {getExpert(message.expert).name}
                      </span>
                    </div>
                  )}

                  {message.role === 'assistant' ? (
                    <div className="prose text-[15px] leading-[1.8]" style={{ color: 'var(--text-primary)' }}>
                      {containsChartData(message.content) ? (
                        <>
                          <ChartRenderer content={message.content} />
                          {extractSummary(message.content) && (
                            <p className="mt-4 text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                              {extractSummary(message.content)}
                            </p>
                          )}
                        </>
                      ) : (
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      )}
                    </div>
                  ) : (
                    <p className="text-[15px] leading-[1.8] font-display" style={{ color: 'var(--text-muted)' }}>
                      {message.content}
                    </p>
                  )}

                  {message.excel_file && (
                    <a
                      href={`/api/download/${message.excel_file}`}
                      download
                      className="inline-flex items-center gap-2 mt-3 text-sm font-display transition-colors"
                      style={{ color: 'var(--accent)' }}
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
                  <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--accent)' }} />
                  <span className="text-sm font-display" style={{ color: 'var(--text-muted)' }}>Thinking...</span>
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
          {/* Two Options: Persona & Model - Only shown when showOptions is true */}
          {showOptions && (
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-4 mb-5">
              {/* Persona Selection */}
              <div className="flex-1">
                <label className="block text-[10px] uppercase tracking-wider font-display mb-2 ml-1" style={{ color: 'var(--text-muted)' }}>
                  Persona
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {EXPERTS.map((expert) => (
                    <button
                      key={expert.id}
                      onClick={() => setSelectedExpert(expert.id)}
                      disabled={loading}
                      className="px-3.5 py-1.5 rounded-full text-xs font-medium font-display transition-all duration-200"
                      style={{
                        background: selectedExpert === expert.id ? 'var(--accent-muted)' : 'transparent',
                        color: selectedExpert === expert.id ? 'var(--accent)' : 'var(--text-muted)',
                        border: selectedExpert === expert.id ? '1px solid var(--accent)' : '1px solid var(--border-color)'
                      }}
                    >
                      {expert.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Divider */}
              <div className="hidden sm:block w-px h-12" style={{ background: 'var(--border-color)' }} />

              {/* Model Selection */}
              <div className="sm:w-40">
                <label className="block text-[10px] uppercase tracking-wider font-display mb-2 ml-1" style={{ color: 'var(--text-muted)' }}>
                  Model
                </label>
                <div className="relative">
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    disabled={loading}
                    className="w-full appearance-none text-sm font-display px-3 py-2 pr-8 rounded-lg cursor-pointer focus:outline-none transition-colors"
                    style={{
                      background: 'var(--card-bg)',
                      color: 'var(--text-secondary)',
                      border: '1px solid var(--border-color)'
                    }}
                  >
                    {MODELS.map((model) => (
                      <option key={model.id} value={model.id} style={{ background: 'var(--bg-secondary)' }}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                  <FiChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: 'var(--text-muted)' }} />
                </div>
              </div>
            </div>
          )}

          {/* Input */}
          <form onSubmit={handleSubmit}>
            <div
              className="rounded-2xl transition-all duration-300"
              style={{
                border: inputFocused ? '1px solid var(--accent)' : '1px solid var(--border-color)'
              }}
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
                  className="w-full bg-transparent text-[15px] font-display pl-5 pr-14 py-4 resize-none focus:outline-none"
                  style={{
                    minHeight: '56px',
                    maxHeight: '140px',
                    color: 'var(--text-primary)',
                    '::placeholder': { color: 'var(--text-muted)' }
                  }}
                  onInput={(e) => {
                    e.target.style.height = 'auto'
                    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
                  }}
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || loading}
                  className="absolute right-3 bottom-3 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200"
                  style={{
                    background: input.trim() && !loading ? 'var(--accent)' : 'var(--card-bg)',
                    color: input.trim() && !loading ? 'var(--bg-primary)' : 'var(--text-muted)'
                  }}
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
        .prose strong { font-weight: 600; color: var(--accent); }
        .prose a { color: var(--accent); text-decoration: underline; }
        .prose code {
          font-size: 0.875em;
          background: var(--bg-tertiary);
          color: var(--accent);
          padding: 0.15em 0.4em;
          border-radius: 4px;
        }
        .prose pre {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          padding: 1em;
          overflow-x: auto;
          margin: 0.75em 0;
          border-radius: 8px;
        }
        .prose pre code { background: none; padding: 0; color: var(--text-primary); }
        .prose ul, .prose ol { padding-left: 1.25em; margin: 0.5em 0; }
        .prose li { margin: 0.25em 0; }
        .prose li::marker { color: var(--accent); }
        .prose blockquote {
          border-left: 2px solid var(--accent-muted);
          padding-left: 1em;
          margin: 0.75em 0;
          color: var(--text-muted);
        }

        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        .hide-scrollbar::-webkit-scrollbar { display: none; }
      `}</style>
    </div>
  )
}

export default ChatInterface
